import os
from dotenv import load_dotenv
from minio import Minio
import time

load_dotenv()

class Settings:
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"
    MINIO_BUCKETS = ["note", "document"]
    API_BASE_URL = os.getenv("API_BASE_URL")
    

settings = Settings()

# MinIO client with timeout
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
    http_client=None
)

# Create buckets if not exist (with timeout)
try:
    for bucket in settings.MINIO_BUCKETS:
        try:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                print(f"Bucket '{bucket}' created.")
            else:
                print(f"Bucket '{bucket}' already exists.")
        except Exception as e:
            print(f"Warning: Could not create bucket '{bucket}': {str(e)}")
except Exception as e:
    print(f"Warning: MinIO initialization failed: {str(e)}")