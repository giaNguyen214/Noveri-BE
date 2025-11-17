from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from services.minio_service import MinioService
import mimetypes
router = APIRouter(prefix="/files", tags=["Files"])

@router.post("/upload/{bucket}")
def upload(bucket: str, file: UploadFile = File(...)):
    return MinioService.upload_file(bucket, file)

@router.get("/download/{bucket}/{file_name}")
def download(bucket: str, file_name: str):
    data = MinioService.download_file(bucket, file_name)
    return StreamingResponse(
        data,
        media_type=mimetypes.guess_type(file_name)[0] or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )

@router.get("/metadata/{bucket}")
def metadata(bucket: str):
    return MinioService.list_metadata(bucket)
