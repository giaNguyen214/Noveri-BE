from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from services.minio_service import MinioService
import mimetypes
from urllib.parse import quote
router = APIRouter(prefix="/files", tags=["Files"])

@router.post("/upload/{bucket}")
def upload(bucket: str, file: UploadFile = File(...), user_id: str = None):
    return MinioService.upload_file(bucket, file, user_id)

# @router.get("/download/{bucket}/{file_name}")
# def download(bucket: str, file_name: str, user_id: str = None):
#     data = MinioService.download_file(bucket, file_name, user_id)
#     return StreamingResponse(
#         data,
#         media_type=mimetypes.guess_type(file_name)[0] or "application/octet-stream",
#         headers={"Content-Disposition": f"attachment; filename={file_name}"}  # để thằng này khi mà tên file chứa tiếng việt là bị lỗi cors á
#     )

@router.get("/download/{bucket}/{file_name}")
def download(bucket: str, file_name: str, user_id: str = None):
    data = MinioService.download_file(bucket, file_name, user_id)

    response = StreamingResponse(
        data,
        media_type=mimetypes.guess_type(file_name)[0]
        or "application/octet-stream",
    )

    encoded = quote(file_name)
    response.headers["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''{encoded}"
    )

    return response

@router.get("/metadata/{bucket}/{etag}")
def detail_metadata(bucket: str, etag: str, user_id: str = None):
    return MinioService.list_detail_metadata(bucket, etag, user_id)    

@router.get("/metadata/{bucket}")
def metadata(bucket: str, user_id: str = None):
    return MinioService.list_metadata(bucket, user_id)
