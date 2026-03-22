"""
Archive download API endpoint.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import zipfile
import io
from pathlib import Path
import logging

from app.tasks.celery_app import celery_app

router = APIRouter(tags=["archive"])
logger = logging.getLogger(__name__)


@router.get("/result/{task_id}/archive")
async def download_archive(task_id: str):
    """
    Download all results as ZIP archive.

    Args:
        task_id: Celery task ID

    Returns:
        ZIP file with all result formats
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
        results = result.get('results', {})

        if not results:
            raise HTTPException(status_code=404, detail="No results found")

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for format_name, file_path in results.items():
                path = Path(file_path)
                if path.exists():
                    # Add file to ZIP with format-specific name
                    zip_file.write(file_path, f"result.{format_name}")
                    logger.info(f"Added {format_name} to archive")

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=results_{file_id}.zip"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating archive: {e}")
        raise HTTPException(status_code=500, detail="Error creating archive")
