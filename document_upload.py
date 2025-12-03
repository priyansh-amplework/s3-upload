import os
from pathlib import Path
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError
from langdetect import detect, LangDetectException, DetectorFactory
import PyPDF2
import docx2txt
#import warnings

# Suppress warnings
#warnings.filterwarnings("ignore", category=UserWarning)

# ---------------- Load environment variables ----------------
load_dotenv()

# Constants
BUCKET_NAME = os.getenv('BUCKET_NAME')
REGION = os.getenv('REGION')

# Define folder mappings for non-tiered folders
FOLDER_MAPPINGS = {
    "personality": "personality",      # → Pinecone: ona-system (tone examples)
    "instructions": "instructions",    # → Pinecone: ona-system (guidelines)
}

# Tier folders that need language detection
TIER_FOLDERS = ["Tier 1", "Tier 2"]

# ---------------- Initialize S3 client ----------------
try:
    s3 = boto3.client(
        "s3",
        region_name=REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    print("✅ S3 client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize S3 client: {e}")
    raise

def sample_text_from_docs(filepath:str)->str:
    text=docx2txt.process(filepath)
    return text[:500] if len(text)>500 else text

def sample_text_from_pdf(filepath:str)->str:
    with open(filepath,'rb') as file:
        text=""
        fhand=PyPDF2.PdfReader(file)
        pages=fhand.pages[:4] if len(fhand.pages)>4 else fhand.pages
        for page in pages:
            text += page.extract_text() or ""
    return text #if len(text)>500 else text

# ---------------- Language Detection with Langdetect ----------------
def detect_language_from_file(filepath: str) -> str:
    """
    Detect if a file content is in Spanish or English using langdetect.
    Returns: 'spanish' or 'english'
    """
    DetectorFactory.seed = 0
    # Get file extension and clean the filename
    file_ext = filepath.suffix

    # Use langdetect to predict language
    try:
        absolute_path=filepath.parent/filepath.name
        if file_ext==".pdf":
            pdf_text=sample_text_from_pdf(absolute_path)
            lang_code = detect(pdf_text)
        else:
            docx_text=sample_text_from_docs(absolute_path)
            lang_code = detect(docx_text)
        # Map language codes to our categories
        if lang_code == 'es':  # Spanish
            return "spanish"
        elif lang_code == 'en':  # English
            return "english"
        else:
            # If detected language is neither English nor Spanish, 
            # default to English
            print(f"   ⚠️  Detected '{lang_code}' for '{filepath}', defaulting to English")
            return "english"
    except LangDetectException as e:
        print(f"   ⚠️  Error detecting language for '{filepath}': {e}, defaulting to English")
        return "english"

# ---------------- Ensure bucket exists ----------------
def ensure_bucket_exists():
    try:
        buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
        if BUCKET_NAME not in buckets:
            print(f"ℹ️  Bucket '{BUCKET_NAME}' not found. Creating it...")
            if REGION == "eu-west-1":
                s3.create_bucket(Bucket=BUCKET_NAME)
            else:
                s3.create_bucket(
                    Bucket=BUCKET_NAME,
                    CreateBucketConfiguration={"LocationConstraint": REGION},
                )
            print(f"✅ Bucket '{BUCKET_NAME}' created successfully.")
        else:
            print(f"✅ Bucket '{BUCKET_NAME}' already exists.")
    except NoCredentialsError:
        print("❌ AWS credentials not found. Check your .env file.")
        raise
    except ClientError as e:
        print(f"❌ Error checking/creating bucket: {e}")
        raise

# ---------------- Upload all files in folder ----------------
def upload_folder_to_s3(local_folder_name: str, s3_prefix: str):
    local_folder = Path(__file__).parent/local_folder_name
    
    if not local_folder.exists():
        print(f"⚠️  Folder not found: {local_folder} - Skipping...")
        return 0
    
    files = list(local_folder.glob("*.*"))
    if not files:
        print(f"⚠️  No files found in folder: {local_folder} - Skipping...")
        return 0
    
    uploaded_count = 0
    print(f"\n📁 Processing folder: {local_folder_name}/")
    print(f"   → S3 prefix: {s3_prefix}/")
    
    for file_path in files:
        if file_path.is_file():
            # Create S3 key with the specified prefix
            s3_key = f"{s3_prefix}/{file_path.name}"
            
            try:
                s3.upload_file(str(file_path), BUCKET_NAME, s3_key)
                print(f"   ✅ Uploaded: {file_path.name} → s3://{BUCKET_NAME}/{s3_key}")
                uploaded_count += 1
            except (ClientError, NoCredentialsError) as e:
                print(f"   ❌ Failed to upload {file_path.name}: {e}")
    
    print(f"   📦 Uploaded {uploaded_count}/{len(files)} file(s) from '{local_folder_name}/'")
    return uploaded_count

# ---------------- Upload Tier folder with language detection ----------------
def upload_tier_folder_with_language_detection(tier_folder_name: str):
    """
    Upload files from a tier folder, automatically detecting language
    and uploading to appropriate S3 prefix (e.g., Tier1-spanish, Tier1-english)
    """
    local_folder  = Path(__file__).parent/tier_folder_name
    
    if not local_folder.exists():
        print(f"⚠️  Folder not found: {local_folder} - Skipping...")
        return 0, 0
    
    files = list(local_folder.glob("*.*"))
    if not files:
        print(f"⚠️  No files found in folder: {local_folder} - Skipping...")
        return 0, 0
    
    spanish_count = 0
    english_count = 0
    
    print(f"\n📁 Processing tier folder: {tier_folder_name}/")

    s3_files=list()
    for lang in ["spanish", "english"]:
        prefix = f"{tier_folder_name}-{lang}"
        s3_files+=list_s3_files_by_prefix(prefix)
        
    cleaned_s3_files={file.split('/',1)[1] for file in s3_files}
    unique_files=[file for file in files if file.name not in cleaned_s3_files]

    for file_path in unique_files:
        if file_path.is_file():
            
            # Detect language from filename using langdetect
            language = detect_language_from_file(file_path)
            
            # Determine S3 prefix based on tier and language
            s3_prefix = f"{tier_folder_name}-{language}"
            s3_key = f"{s3_prefix}/{file_path.name}"
            
            try:
                s3.upload_file(str(file_path), BUCKET_NAME, s3_key)
                print(f"   ✅ [{language.upper()}] {file_path.name} → s3://{BUCKET_NAME}/{s3_key}")
                
                if language == "spanish":
                    spanish_count += 1
                else:
                    english_count += 1
                    
            except (ClientError, NoCredentialsError) as e:
                print(f"   ❌ Failed to upload {file_path.name}: {e}")
    
    total = spanish_count + english_count
    print(f"   📦 Uploaded {total} file(s): {spanish_count} Spanish, {english_count} English")
    return spanish_count, english_count

# ---------------- List uploaded files (verification) ----------------
def list_s3_files_by_prefix(prefix: str):
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        
        if 'Contents' not in response:
            print(f"   No files found with prefix '{prefix}/'")
            return []
        
        files = [obj['Key'] for obj in response['Contents']]
        return files
    except ClientError as e:
        print(f"   ❌ Error listing files: {e}")
        return []

# ---------------- Remove files from S3 ----------------
def remove_files_from_S3(prefix:str=None,key:str=None):
    """
    Remove files from S3 Bucket
    Args:
       prefix: If provided, remove all files with this prefix.
       key: If provided, remove the file corresponding to this key
    Note:Provide either prefix or key ,not both
    """
    if prefix is None and key is None:
        print("Error:No file provided")
        return None
    
    deleted_count=0
    try:
        if prefix:
            print(f"\n🗑️  Removing all files with prefix: {prefix}")
            response=s3.list_objects_v2(Bucket=BUCKET_NAME,Prefix=prefix)
            if "Contents" not in response:
                print(f"No files found with Prefix:{prefix}")
                return None
            files_to_delete=[{'key':obj['key']} for obj in response['Contents']]

            print(f"Found {len(files_to_delete)} file(s) to delete:")
            for file in files_to_delete:
                print(f"{file['key']}")
            confirm=input(f"Delete {len(files_to_delete)} files? yes/no:").strip().lower()
            if confirm!='yes':
                print("Deletion Cancelled?")
                return None
            
            for i in range(0,len(files_to_delete)):
                batch= files_to_delete[i]
                s3.delete_objects(
                    Bucket=BUCKET_NAME,
                    Delete={'Objects':batch}
                )
                print(f"Deleted {files_to_delete[i]} file")
            
            print(f" 🗑️ Total Deleted:{deleted_count} files")
        
        elif key:
            # Delete a specific file
            print(f"\n🗑️  Removing file: {key}")
            
            # Check if file exists
            try:
                s3.head_object(Bucket=BUCKET_NAME, Key=key)
            except ClientError:
                print(f"   ⚠️  File not found: {key}")
                return 0
            
            confirm = input(f"   ⚠️  Delete this file? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("   ❌ Deletion cancelled")
                return 0
            
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)
            deleted_count = 1
            print(f"   ✅ File deleted: {key}")
        
        return deleted_count
        
    except ClientError as e:
        print(f"   ❌ Error removing files: {e}")
        return 0

# ---------------- MAIN EXECUTION ----------------
if __name__ == "__main__":
    print("=" * 70)
    print(f"🚀 Multi-Folder S3 Upload Script with Langdetect Language Detection")
    print(f"   Bucket: {BUCKET_NAME} ({REGION})")
    print("=" * 70)
    
    # Ensure bucket exists
    ensure_bucket_exists()
    
    # Upload non-tiered folders
    total_uploaded = 0
    for local_folder, s3_prefix in FOLDER_MAPPINGS.items():
        count = upload_folder_to_s3(local_folder, s3_prefix)
        total_uploaded += count
    
    # Upload tier folders with language detection
    total_spanish = 0
    total_english = 0
    
    for tier_folder in TIER_FOLDERS:
        spanish, english = upload_tier_folder_with_language_detection(tier_folder)
        total_spanish += spanish
        total_english += english
        total_uploaded += spanish + english
    
    # Summary
    print("\n" + "=" * 70)
    print(f"📊 UPLOAD SUMMARY")
    print("=" * 70)
    print(f"   Total files uploaded: {total_uploaded}")
    print(f"   Spanish files: {total_spanish}")
    print(f"   English files: {total_english}")
    
    # Verify uploads by listing files in each prefix
    print(f"\n🔍 Verifying uploads in S3:")
    
    # List non-tiered folders
    for s3_prefix in FOLDER_MAPPINGS.values():
        files = list_s3_files_by_prefix(s3_prefix)
        print(f"\n   📂 {s3_prefix}/ ({len(files)} files)")
        for f in files[:5]:
            print(f"      • {f}")
        if len(files) > 5:
            print(f"      ... and {len(files) - 5} more")
    
    # List tier folders (all language variants)
    for tier in TIER_FOLDERS:
        for lang in ["spanish", "english"]:
            prefix = f"{tier}-{lang}"
            files = list_s3_files_by_prefix(prefix)
            print(f"\n   📂 {prefix}/ ({len(files)} files)")
            for f in files[:5]:
                print(f"      • {f}")
            if len(files) > 5:
                print(f"      ... and {len(files) - 5} more")
    
    print("\n" + "=" * 70)
    print("✅ Upload complete!")
    print("=" * 70)