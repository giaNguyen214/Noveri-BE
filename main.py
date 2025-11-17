from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from minio import Minio
from minio.error import S3Error
from fastapi.responses import StreamingResponse
import os
from dotenv import load_dotenv


# GN
from fastapi.responses import JSONResponse

from gemini_client import model
from decompose import decompose_input
from checkworthy import identify_checkworthy
from NAVER import call_naver

from pydantic import BaseModel
import json





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
    
    
    
# GN
@app.post("/decompose/md")
async def decompose_markdown(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    return await decompose_input(model, content)


@app.post("/decompose/text")
async def decompose_text_api(payload: dict):
    text = payload.get("text", "")
    if not text:
        return JSONResponse({"error": "Thiếu trường text"}, status_code=400)

    return await decompose_input(model, text)

@app.post("/checkworthy")
async def api_checkworthy(payload: dict):
    texts = payload.get("texts", [])

    claims, mapping = await identify_checkworthy(model, texts)

    return {
        "checkworthy": claims,
        "full_output": mapping
    }
    
@app.post("/naver")
async def naver_api(
    checkworthy: list[str] = Form(...),
    note: str | None = Form(None),
    internet: str | None = Form(None),
    file: UploadFile | None = File(None)
):
    """
    /naver API — nhận form-data:
    - checkworthy: list[str]
    - note: optional str
    - internet: optional str
    - file: optional File
    """
    result = await call_naver(
        checkworthy_list=checkworthy,
        note=note,
        internet=internet,
        file=file
    )
    return result


class RawInput(BaseModel):
    raw_json: str
    
@app.post("/parse-json")
def parse_json_pretty(data: RawInput):
    raw = data.raw_json

    try:
        # Parse JSON (không sửa nội dung)
        parsed = json.loads(raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    try:
        # Format lại JSON cho dễ đọc — KHÔNG thay đổi nội dung
        pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Formatting error: {e}")

    return {
        "pretty_json": pretty,
        "parsed_object": parsed  # giữ luôn object nếu cần xài tiếp
    }