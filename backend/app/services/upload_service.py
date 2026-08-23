import logging
from io import BytesIO
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestException

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _validate_image(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestException(
            detail=f"Invalid image type '{file.content_type}'. "
            f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )


async def _validate_file_size(file: UploadFile) -> None:
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise BadRequestException(
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB."
        )
    await file.seek(0)


class UploadService:
    def __init__(self) -> None:
        self.cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET
        self._configured = bool(self.cloud_name and self.api_key and self.api_secret)

    def _configure_cloudinary(self) -> None:
        if not self._configured:
            return
        import cloudinary

        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    async def upload_profile_image(
        self,
        *,
        file: UploadFile,
        folder: str,
        user_id: str,
    ) -> str:
        _validate_image(file)
        await _validate_file_size(file)

        if not self._configured:
            raise BadRequestException(
                detail="File upload service is not configured"
            )

        self._configure_cloudinary()
        import cloudinary.uploader

        contents = await file.read()
        file_bytes = BytesIO(contents)
        public_id = f"{folder}/{user_id}"

        try:
            result = cloudinary.uploader.upload(
                file_bytes,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
                transformation=[
                    {"width": 400, "height": 400, "crop": "fill", "gravity": "face"}
                ],
            )
            url: str = result.get("secure_url", "")
            if not url:
                raise BadRequestException(detail="Upload failed: no URL returned")
            return url
        except BadRequestException:
            raise
        except Exception as exc:
            logger.error("Cloudinary upload failed: %s", str(exc))
            raise BadRequestException(
                detail="File upload failed. Please try again later."
            )


upload_service = UploadService()
