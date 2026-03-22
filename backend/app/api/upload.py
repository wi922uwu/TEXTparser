"""
File upload API endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging

from app.storage.file_manager import FileManager
from app.models import UploadResponse
from app.config import settings

router = APIRouter(tags=["upload"])
logger = logging.getLogger(__name__)
file_manager = FileManager()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a single file for OCR processing.

    Supported formats: PDF, JPG, PNG, TIFF
    Max size: 50MB
    """
    try:
        # Validate file extension
        file_ext = file.filename.split('.')[-1].lower()
        if f".{file_ext}" not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(settings.allowed_extensions)}"
            )

        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.max_file_size / 1024 / 1024}MB"
            )

        # Save file
        file_id, file_path = file_manager.save_upload(content, file.filename)

        logger.info(f"Uploaded file: {file.filename} -> {file_id}")

        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            size=len(content)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Error uploading file")


@router.post("/upload/batch", response_model=List[UploadResponse])
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple files for batch processing.

    Supported formats: PDF, JPG, PNG, TIFF
    Max size per file: 50MB
    """
    responses = []

    for file in files:
        try:
            # Validate and upload each file
            file_ext = file.filename.split('.')[-1].lower()
            if f".{file_ext}" not in settings.allowed_extensions:
                logger.warning(f"Skipping unsupported file: {file.filename}")
                continue

            content = await file.read()

            if len(content) > settings.max_file_size:
                logger.warning(f"Skipping large file: {file.filename}")
                continue

            file_id, file_path = file_manager.save_upload(content, file.filename)

            responses.append(UploadResponse(
                file_id=file_id,
                filename=file.filename,
                size=len(content)
            ))

        except Exception as e:
            logger.error(f"Error uploading {file.filename}: {e}")
            continue

    if not responses:
        raise HTTPException(status_code=400, detail="No valid files uploaded")

    return responses
