import logging
import uuid as uuid_lib
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestException

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_RESUME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
RESUME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
# Magic bytes so we don't trust the client-supplied content type alone.
_PDF_MAGIC = b"%PDF"
_ZIP_MAGIC = b"PK\x03\x04"  # DOCX is a ZIP container


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


def _validate_resume(file: UploadFile, contents: bytes) -> str:
    """Validate resume content type/extension and magic bytes.

    Returns the canonical file extension for the detected type.
    """
    content_type = (file.content_type or "").lower()
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if content_type not in ALLOWED_RESUME_TYPES and extension not in (
        ".pdf",
        ".doc",
        ".docx",
    ):
        raise BadRequestException(
            detail="Only PDF and DOCX files are allowed"
        )

    is_pdf = contents.startswith(_PDF_MAGIC)
    is_docx_zip = contents.startswith(_ZIP_MAGIC)
    if not (is_pdf or is_docx_zip):
        raise BadRequestException(
            detail="File content does not look like a valid PDF or DOCX document"
        )

    if is_pdf:
        return ".pdf"
    return ".docx" if extension == ".docx" else ".doc"


async def _read_and_validate_resume(file: UploadFile) -> tuple[bytes, str]:
    await file.seek(0)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise BadRequestException(
            detail=f"Resume too large. Maximum size is {MAX_FILE_SIZE_MB}MB."
        )
    if not contents:
        raise BadRequestException(detail="Resume file is empty")
    extension = _validate_resume(file, contents)
    return contents, extension


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

    async def upload_resume(
        self,
        *,
        file: UploadFile,
        user_id: str,
    ) -> str:
        """Upload a resume (PDF/DOCX, max 5MB).

        Uses Cloudinary raw storage when configured; otherwise falls back
        to local disk under ``settings.UPLOAD_DIR/resumes``. Returns the
        URL/path that should be persisted on the application record.
        """
        contents, extension = await _read_and_validate_resume(file)

        if self._configured:
            self._configure_cloudinary()
            import cloudinary.uploader

            public_id = f"resumes/{user_id}/{uuid_lib.uuid4()}"
            try:
                result = cloudinary.uploader.upload(
                    BytesIO(contents),
                    public_id=public_id + extension,
                    resource_type="raw",
                    folder="resumes",
                    overwrite=False,
                )
                url: str = result.get("secure_url", "")
                if not url:
                    raise BadRequestException(
                        detail="Resume upload failed: no URL returned"
                    )
                return url
            except BadRequestException:
                raise
            except Exception as exc:
                logger.error("Cloudinary resume upload failed: %s", str(exc))
                raise BadRequestException(
                    detail="Resume upload failed. Please try again later."
                )

        return self._save_resume_locally(contents, user_id=user_id, extension=extension)

    def _save_resume_locally(
        self, contents: bytes, *, user_id: str, extension: str
    ) -> str:
        base_dir = Path(settings.UPLOAD_DIR) / "resumes" / user_id
        base_dir.mkdir(parents=True, exist_ok=True)
        file_path = base_dir / f"{uuid_lib.uuid4()}{extension}"
        file_path.write_bytes(contents)
        logger.info("Resume saved locally: %s", file_path)
        return f"/{file_path.as_posix()}"


upload_service = UploadService()
