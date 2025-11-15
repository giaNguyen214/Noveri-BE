from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from minio import Minio
from minio.error import S3Error
from fastapi.responses import StreamingResponse
import os
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()  # Load environment variables from .env file

# MinIO client configuration
client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_SECURE", "False").lower() == "true"  # convert string -> bool
)

# Ensure the bucket exists
BUCKETS = ['note', 'document']

for bucket in BUCKETS:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"Bucket '{bucket}' created.")
    else:
        print(f"Bucket '{bucket}' already exists.")
        
        
# API 1: Upload file to MinIO
@app.post("/upload/{bucket_name}")
def upload_file(bucket_name: str, file: UploadFile = File(...)):
    if bucket_name not in BUCKETS:
        raise HTTPException(status_code=400, detail="Invalid bucket name.")
    
    try:
        client.put_object(
            bucket_name,
            file.filename,
            file.file,
            length=-1,                  # Cho phép upload khi không biết size
            part_size=10*1024*1024      # 10MB mỗi part
        )
        return {
            "message": f"Uploaded successfully",
            "bucket": bucket_name,
            "filename": file.filename
        }
    except S3Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# API 2: Download file from MinIO
@app.get("/download/{bucket_name}/{file_name}")
def download_file(bucket_name: str, file_name: str):

    try:
        data = client.get_object(bucket_name, file_name)
    except S3Error:
        raise HTTPException(status_code=404, detail="File not found.")

    return StreamingResponse(
        data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}"
        }
    )
            
# API 3: List metadata of files in a bucket
@app.get("/metadata/{bucket_name}")
def list_metadata(bucket_name: str):
    if bucket_name not in BUCKETS:
        raise HTTPException(status_code=400, detail="Invalid bucket name.")
    
    try:
        objects = client.list_objects(bucket_name)
        metadata_list = []
        
        for obj in objects:
            metadata = client.stat_object(bucket_name, obj.object_name)
            metadata_list.append({
                "file_name": obj.object_name,
                "size": metadata.size,
                "last_modified": metadata.last_modified,
                "etag": metadata.etag
            })
        
        return {"bucket": bucket_name, "files": metadata_list}
    except S3Error as e:
        raise HTTPException(status_code=500, detail=str(e))