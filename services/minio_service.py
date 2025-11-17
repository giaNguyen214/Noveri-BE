from core.config import minio_client, settings
from fastapi import HTTPException
from minio.error import S3Error
import mimetypes
from urllib.parse import quote



class MinioService:

    @staticmethod
    def upload_file(bucket: str, file):
        if bucket not in settings.MINIO_BUCKETS:
            raise HTTPException(status_code=400, detail="Invalid bucket name.")

        try:
            minio_client.put_object(
                bucket,
                file.filename,
                file.file,
                length=-1,
                part_size=10 * 1024 * 1024
            )
            return {"message": "Uploaded successfully", "bucket": bucket, "filename": file.filename}
        except S3Error as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def download_file(bucket: str, file_name: str):
        try:
            return minio_client.get_object(bucket, file_name)
        except S3Error:
            raise HTTPException(status_code=404, detail="File not found.")

    @staticmethod
    def list_metadata(bucket: str):
        if bucket not in settings.MINIO_BUCKETS:
            raise HTTPException(status_code=400, detail="Invalid bucket name.")

        try:
            objects = minio_client.list_objects(bucket)
            metadata_list = []

            for obj in objects:
                metadata = minio_client.stat_object(bucket, obj.object_name)

                # Detect file MIME type
                file_type, _ = mimetypes.guess_type(obj.object_name)
                file_type = file_type or "application/octet-stream"

                # ---- PREVIEW URL: Dùng API download, không dùng presigned URL ----
                obj_name_url_encoded = quote(obj.object_name, safe="")
                preview_url = (
                    f"{settings.API_BASE_URL}/files/download/{bucket}/{obj_name_url_encoded}"
                )

                metadata_list.append({
                    "file_name": obj.object_name,
                    "size": metadata.size,
                    "last_modified": metadata.last_modified,
                    "etag": metadata.etag,
                    "type": file_type,
                    "preview_url": preview_url,    # dùng API download => không expire
                })

            return {"bucket": bucket, "files": metadata_list}

        except S3Error as e:
            raise HTTPException(status_code=500, detail=str(e))

