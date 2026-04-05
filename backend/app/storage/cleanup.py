"""
Cleanup task for old files.
"""
from app.tasks.celery_app import celery_app
from app.storage.file_manager import FileManager
import logging

logger = logging.getLogger(__name__)


@celery_app.task
def cleanup_old_files():
    """
    Periodic task to clean up old uploaded and result files.
    Should be scheduled to run daily.
    """
    try:
        file_manager = FileManager()
        removed_count = file_manager.cleanup_old_files()
        logger.info(f"Cleanup task completed. Removed {removed_count} old file directories.")
        return {"status": "success", "removed": removed_count}
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        return {"status": "error", "error": str(e)}
