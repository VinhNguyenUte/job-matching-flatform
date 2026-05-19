import base64
from typing import Optional

import cloudinary
import cloudinary.uploader

from app.core.config import settings


class CloudinaryService:
    def __init__(self):
        self.cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET
        self.folder = settings.CLOUDINARY_FOLDER

        if not self.cloud_name or not self.api_key or not self.api_secret:
            raise RuntimeError(
                "Cloudinary is not configured. Set CLOUDINARY_CLOUD_NAME, "
                "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET."
            )

        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    async def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str,
        folder: Optional[str] = None,
        resource_type: str = "image",
        strip_extension: bool = True,
    ) -> str:
        data_uri = f"data:{content_type};base64,{base64.b64encode(file_data).decode('ascii')}"
        public_id = object_name.replace("\\", "/")
        if strip_extension:
            public_id = public_id.rsplit(".", 1)[0]

        result = cloudinary.uploader.upload(
            data_uri,
            folder=folder or self.folder,
            public_id=public_id,
            overwrite=False,
            resource_type=resource_type,
        )
        return result["secure_url"]

    async def upload_cv(self, file_data: bytes, object_name: str, content_type: str) -> str:
        return await self.upload_file(
            file_data=file_data,
            object_name=object_name,
            content_type=content_type,
            resource_type="raw",
            strip_extension=False,
        )


cloudinary_service = CloudinaryService()
