import io
from minio import Minio
from app.core.config import settings

class MinioService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(settings.MINIO_BUCKET_CV):
            self.client.make_bucket(settings.MINIO_BUCKET_CV)

    def upload_cv(self, file_data: bytes, file_name: str, content_type: str) -> str:
        data_stream = io.BytesIO(file_data)
        self.client.put_object(
            bucket_name=settings.MINIO_BUCKET_CV,
            object_name=file_name,
            data=data_stream,
            length=len(file_data),
            content_type=content_type
        )
        # Trả về định danh object_name hoặc URI để lưu vào DB
        return file_name

minio_service = MinioService()