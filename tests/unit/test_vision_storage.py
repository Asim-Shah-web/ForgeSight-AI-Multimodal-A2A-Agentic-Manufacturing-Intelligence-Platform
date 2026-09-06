"""Unit tests for image upload validation and storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from forgesight.config.settings import settings
from forgesight.vision.storage import InvalidUploadError, save_uploaded_image


@pytest.mark.asyncio
async def test_oversized_file_raises_invalid_upload_error() -> None:
    oversized_bytes = b"0" * ((settings.cv_upload_max_size_mb + 1) * 1024 * 1024)
    with pytest.raises(InvalidUploadError, match="exceeding"):
        await save_uploaded_image("BRD-TEST-001", oversized_bytes, "image/jpeg")


@pytest.mark.asyncio
async def test_disallowed_content_type_raises_invalid_upload_error() -> None:
    with pytest.raises(InvalidUploadError, match="not allowed"):
        await save_uploaded_image("BRD-TEST-001", b"some bytes", "application/pdf")


@pytest.mark.asyncio
async def test_empty_file_raises_invalid_upload_error() -> None:
    with pytest.raises(InvalidUploadError, match="empty"):
        await save_uploaded_image("BRD-TEST-001", b"", "image/jpeg")


@pytest.mark.asyncio
async def test_valid_upload_is_written_under_board_directory() -> None:
    board_id = "BRD-TEST-STORAGE-001"
    file_path = await save_uploaded_image(board_id, b"fake-jpeg-bytes", "image/jpeg")

    path = Path(file_path)
    assert path.exists()
    assert path.parent.name == board_id
    assert path.suffix == ".jpg"

    path.unlink()