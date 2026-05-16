from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import uuid
import time
from fastapi import UploadFile
import os

class MinioClient:
    def __init__(self):
        self._client = None
        self.bucket_name = settings.MINIO_BUCKET_NAME

    @property
    def client(self):
        """Lazy initialization"""
        if self._client is None:
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ROOT_USER,
                secret_key=settings.MINIO_ROOT_PASSWORD,
                secure=False
            )
            self._ensure_bucket()
        return self._client

    def _ensure_bucket(self, retries=10):
        for i in range(retries):
            try:
                if not self.client.bucket_exists(self.bucket_name):
                    self.client.make_bucket(self.bucket_name)
                    print(f"✅ MinIO bucket '{self.bucket_name}' đã được tạo!")
                else:
                    print(f"✅ MinIO bucket '{self.bucket_name}' đã tồn tại.")
                return
            except Exception as e:
                print(f"⚠️ MinIO retry {i+1}/{retries}: {e}")
                time.sleep(3)
        print("❌ Không thể kết nối MinIO sau nhiều lần thử.")

    def upload_cv(self, file: UploadFile, user_id: int) -> str:
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{user_id}/{uuid.uuid4()}{file_ext}"
        
        file.file.seek(0)
        
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=unique_filename,
            data=file.file,
            length=file.size,
            content_type=file.content_type or "application/pdf"
        )
        return unique_filename

    def get_object(self, object_name: str):
        return self.client.get_object(self.bucket_name, object_name)


# Singleton
minio_client = MinioClient()