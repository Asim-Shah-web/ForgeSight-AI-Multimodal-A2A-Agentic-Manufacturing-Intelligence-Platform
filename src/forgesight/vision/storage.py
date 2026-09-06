"""Image upload validation and storage for AOI inspection evidence."""

from __future__ import annotations

import uuid
from pathlib import Path

from forgesight.config.logging import get_logger
from forgesight.config.settings import settings

logger = get_logger(__name__)

_EXTENSION_BY_MIME_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
}


class InvalidUploadError(Exception):
    """Raised when an uploaded file fails size or content-type validation."""


def _validate_upload(file_bytes: bytes, content_type: str) -> None:
    if content_type not in settings.cv_upload_allowed_mime_types:
        raise InvalidUploadError(
            f"Content type '{content_type}' is not allowed. "
            f"Allowed types: {settings.cv_upload_allowed_mime_types}"
        )

    max_bytes = settings.cv_upload_max_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise InvalidUploadError(
            f"Uploaded file is {len(file_bytes) / (1024 * 1024):.2f} MB, "
            f"exceeding the {settings.cv_upload_max_size_mb} MB limit."
        )

    if len(file_bytes) == 0:
        raise InvalidUploadError("Uploaded file is empty.")


async def save_uploaded_image(board_id: str, file_bytes: bytes, content_type: str) -> str:
    """
    Validate and persist an uploaded inspection image to disk.

    Returns the stored file path, used as InspectionImage.image_reference
    and CvFinding.raw_image_reference.
    """
    _validate_upload(file_bytes, content_type)

    extension = _EXTENSION_BY_MIME_TYPE[content_type]
    board_dir = Path(settings.cv_upload_storage_dir) / board_id
    board_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{uuid.uuid4()}.{extension}"
    file_path = board_dir / file_name
    file_path.write_bytes(file_bytes)

    logger.info(
        "inspection_image_saved",
        extra={"board_id": board_id, "file_path": str(file_path), "size_bytes": len(file_bytes)},
    )
    return str(file_path)