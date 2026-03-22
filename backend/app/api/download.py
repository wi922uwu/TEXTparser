"""
Result download API endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import logging
from pathlib import Path

from app.storage.file_manager import FileManager
from app.tasks.celery_app import celery_app

router = APIRouter(tags=["download"])
logger = logging.getLogger(__name__)
file_manager = FileManager()


@router.get("/result/{task_id}")
async def download_result(task_id: str, format: str = "txt"):
    """
    Download processing result.

    Args:
        task_id: Celery task ID
        format: Export format (txt, docx, xlsx, csv)

    Returns:
        File download response
    """
    try:
        # Check task status
        task = celery_app.AsyncResult(task_id)

        if task.state != 'SUCCESS':
            raise HTTPException(
                status_code=400,
                detail=f"Task not completed. Status: {task.state}"
            )

        # Get result info
        result = task.result
        file_id = result.get('file_id')

        if not file_id:
            raise HTTPException(status_code=404, detail="Result not found")

        # Get result file
        result_path = file_manager.get_result_path(file_id, format)

        if not result_path or not result_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Result file not found for format: {format}"
            )

        # Determine media type
        media_types = {
            "txt": "text/plain",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv"
        }

        media_type = media_types.get(format, "application/octet-stream")
        filename = f"result.{format}"

        return FileResponse(
            path=str(result_path),
            filename=filename,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading result: {e}")
        raise HTTPException(status_code=500, detail="Error downloading result")
