from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import uuid
from fastapi import UploadFile
import os

class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False  # HTTP (Docker)
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Tạo bucket nếu chưa tồn tại"""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            print(f"✅ Created MinIO bucket: {self.bucket_name}")

    def upload_cv(self, file: UploadFile, user_id: int) -> str:
        """Upload CV và trả về đường dẫn file"""
        try:
            # Tạo tên file unique
            file_ext = os.path.splitext(file.filename)[1].lower()
            unique_filename = f"{user_id}/{uuid.uuid4()}{file_ext}"
            
            # Reset file pointer
            file.file.seek(0)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=unique_filename,
                data=file.file,
                length=file.size,
                content_type=file.content_type or "application/pdf"
            )
            
            return unique_filename
            
        except S3Error as e:
            print(f"MinIO Error: {e}")
            raise

    def get_file_url(self, object_name: str, expires: int = 3600):
        """Lấy presigned URL (tùy chọn)"""
        try:
            return self.client.presigned_get_object(self.bucket_name, object_name, expires)
        except S3Error:
            return None
        
    def get_object(self, object_name: str):
        """Lấy object để download"""
        return self.client.get_object(self.bucket_name, object_name)

# Singleton
minio_client = MinioClient()