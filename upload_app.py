from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import boto3
from pathlib import Path
import tempfile
import os

# import your existing functions
from document_upload import detect_language_from_file

app = FastAPI()

# Add CORS - allows frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get AWS credentials from environment variables (Railway will provide these)
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)
BUCKET = os.getenv("S3_BUCKET_NAME", "ona-wealth-v1")

@app.get("/")
async def root():
    return {"status": "healthy", "service": "Ona Upload API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/get-upload-url")
async def get_upload_url(file: UploadFile, type: str = Form(...)):
    temp_path = Path(tempfile.gettempdir()) / file.filename
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    if type == "personality":
        prefix = "personality"
    elif type == "instructions":
        prefix = "instructions"
    elif type == "Tier1":
        lang = detect_language_from_file(temp_path)
        prefix = f"Tier 1-{lang}"
    elif type == "Tier2":
        lang = detect_language_from_file(temp_path)
        prefix = f"Tier 2-{lang}"
    else:
        prefix = "others"

    key = f"{prefix}/{file.filename}"

    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=3600
    )
    
    temp_path.unlink(missing_ok=True)

    return {"uploadUrl": url, "key": key}
