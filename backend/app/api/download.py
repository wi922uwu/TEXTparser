"""
Result download API endpoints.
"""
from fastapi import APIRouter, HTTPException, Response
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
        File download response with proper UTF-8 headers
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

        # Read file content
        with open(result_path, 'rb') as f:
            content = f.read()

        # Determine media type with charset for text files
        if format == "txt":
            media_type = "text/plain; charset=utf-8"
        elif format == "csv":
            media_type = "text/csv; charset=utf-8"
        elif format == "docx":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif format == "xlsx":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            media_type = "application/octet-stream"

        filename = f"result.{format}"

        # RFC 5987 encoding for UTF-8 filenames in Content-Disposition
        # This ensures proper handling of UTF-8 encoded content
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
            "Content-Type": media_type,
            "Content-Length": str(len(content)),
            "Access-Control-Expose-Headers": "Content-Disposition"
        }

        return Response(content=content, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading result: {e}")
        raise HTTPException(status_code=500, detail="Error downloading result")
