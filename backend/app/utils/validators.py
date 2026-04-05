"""
File validation utilities.
"""
from pathlib import Path
from typing import Optional
import magic
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def validate_file_extension(filename: str) -> bool:
    """
    Validate file extension.

    Args:
        filename: File name to validate

    Returns:
        True if extension is allowed
    """
    ext = Path(filename).suffix.lower()
    return ext in settings.allowed_extensions


def validate_file_size(size: int) -> bool:
    """
    Validate file size.

    Args:
        size: File size in bytes

    Returns:
        True if size is within limits
    """
    return size <= settings.max_file_size


def get_file_type(file_path: str) -> Optional[str]:
    """
    Detect actual file type using magic numbers.

    Args:
        file_path: Path to file

    Returns:
        MIME type or None
    """
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    except Exception as e:
        logger.warning(f"Could not detect file type: {e}")
        return None


def is_valid_pdf(file_path: str) -> bool:
    """Check if file is a valid PDF."""
    mime_type = get_file_type(file_path)
    return mime_type == "application/pdf"


def is_valid_image(file_path: str) -> bool:
    """Check if file is a valid image."""
    mime_type = get_file_type(file_path)
    return mime_type and mime_type.startswith("image/")
