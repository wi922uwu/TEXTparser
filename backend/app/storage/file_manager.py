"""
File storage management.
"""
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file uploads and results storage."""

    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.result_dir = settings.result_dir

    def save_upload(self, file_content: bytes, filename: str) -> tuple[str, str]:
        """
        Save uploaded file.

        Args:
            file_content: File content as bytes
            filename: Original filename

        Returns:
            Tuple of (file_id, file_path)
        """
        file_id = str(uuid.uuid4())
        file_ext = Path(filename).suffix

        # Create subdirectory for this upload
        upload_path = self.upload_dir / file_id
        upload_path.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = upload_path / f"original{file_ext}"
        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"Saved upload: {file_id} ({filename})")
        return file_id, str(file_path)

    def get_upload_path(self, file_id: str) -> Optional[Path]:
        """Get path to uploaded file."""
        upload_path = self.upload_dir / file_id
        if upload_path.exists():
            # Find the original file
            files = list(upload_path.glob("original.*"))
            if files:
                return files[0]
        return None

    def save_result(self, file_id: str, format: str, content: bytes) -> str:
        """
        Save processing result.

        Args:
            file_id: Original file ID
            format: Output format (txt, docx, xlsx, csv)
            content: Result content

        Returns:
            Path to saved result
        """
        result_path = self.result_dir / file_id
        result_path.mkdir(parents=True, exist_ok=True)

        result_file = result_path / f"result.{format}"
        with open(result_file, 'wb') as f:
            f.write(content)

        logger.info(f"Saved result: {file_id}.{format}")
        return str(result_file)

    def get_result_path(self, file_id: str, format: str) -> Optional[Path]:
        """Get path to result file."""
        result_file = self.result_dir / file_id / f"result.{format}"
        if result_file.exists():
            return result_file
        return None

    def cleanup_old_files(self, hours: int = None):
        """
        Remove files older than specified hours.

        Args:
            hours: Age threshold in hours (default from settings)
        """
        if hours is None:
            hours = settings.file_retention_hours

        cutoff_time = datetime.now() - timedelta(hours=hours)
        removed_count = 0

        # Clean uploads
        for item in self.upload_dir.iterdir():
            if item.is_dir():
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff_time:
                    shutil.rmtree(item)
                    removed_count += 1

        # Clean results
        for item in self.result_dir.iterdir():
            if item.is_dir():
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff_time:
                    shutil.rmtree(item)
                    removed_count += 1

        logger.info(f"Cleaned up {removed_count} old file directories")
        return removed_count

    def delete_file(self, file_id: str):
        """Delete all files associated with file_id."""
        upload_path = self.upload_dir / file_id
        result_path = self.result_dir / file_id

        if upload_path.exists():
            shutil.rmtree(upload_path)

        if result_path.exists():
            shutil.rmtree(result_path)

        logger.info(f"Deleted files for: {file_id}")
