"""
OCR processing API endpoints.
"""
from fastapi import APIRouter, HTTPException
import logging

from app.models import ProcessRequest, ProcessResponse, TaskStatus
from app.tasks.ocr_tasks import process_document
from app.tasks.celery_app import celery_app

router = APIRouter(tags=["process"])
logger = logging.getLogger(__name__)


@router.post("/process", response_model=ProcessResponse)
async def start_processing(request: ProcessRequest):
    """
    Start OCR processing for uploaded file.

    Args:
        request: Processing request with file_id and export formats

    Returns:
        Task ID for tracking progress
    """
    try:
        # Validate formats
        valid_formats = {"txt", "docx", "xlsx", "csv"}
        invalid_formats = set(request.formats) - valid_formats
        if invalid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid formats: {invalid_formats}"
            )

        # Start Celery task
        task = process_document.delay(request.file_id, request.formats)

        logger.info(f"Started processing task: {task.id} for file: {request.file_id}")

        return ProcessResponse(task_id=task.id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        raise HTTPException(status_code=500, detail="Error starting processing")


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get status of processing task.

    Args:
        task_id: Celery task ID

    Returns:
        Current task status and progress
    """
    try:
        task = celery_app.AsyncResult(task_id)

        response = TaskStatus(
            task_id=task_id,
            status=task.state
        )

        if task.state == 'PROGRESS':
            info = task.info or {}
            response.progress = info.get('progress', 0)
            response.step = info.get('step', '')
        elif task.state == 'FAILURE':
            info = task.info or {}
            response.error = str(info.get('error', 'Unknown error'))
        elif task.state == 'SUCCESS':
            response.progress = 100
            response.step = 'completed'

        return response

    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Error getting task status")
