from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import boto3
from pathlib import Path
import tempfile
import os

app = FastAPI()

# Add CORS middleware to allow Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
)
BUCKET = "ona-wealth-v1"

@app.get("/")
def root():
    return {"status": "FastAPI backend is running", "service": "Document Upload API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/get-upload-url")
async def get_upload_url(file: UploadFile, type: str = Form(...)):
    
    # Save the uploaded file temporarily
    temp_path = Path(tempfile.gettempdir()) / file.filename
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Logic based on dropdown
    if type == "personality":
        prefix = "personality"
    elif type == "instructions":
        prefix = "instructions"
    elif type == "Tier1":
        from document_upload import detect_language_from_file
        lang = detect_language_from_file(temp_path)
        prefix = f"Tier 1-{lang}"
    elif type == "Tier2":
        from document_upload import detect_language_from_file
        lang = detect_language_from_file(temp_path)
        prefix = f"Tier 2-{lang}"
    else:
        prefix = "others"

    key = f"{prefix}/{file.filename}"

    # Pre-signed S3 upload URL
    url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET, 
            "Key": key,
            "ContentType": file.content_type or "application/octet-stream"
        },
        ExpiresIn=3600
    )
    
    # Clean up temp file
    try:
        os.unlink(temp_path)
    except:
        pass

    return {"uploadUrl": url, "key": key}