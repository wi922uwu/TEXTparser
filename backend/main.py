"""FastAPI application with document processing endpoints."""
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.config import (
    UPLOAD_DIR,
    RESULT_DIR,
    MAX_FILE_SIZE_MB,
    ALLOWED_EXTENSIONS,
)
from backend.models.schemas import (
    UploadResponse,
    ProcessingStatus,
    ProcessingResult,
    ExportFormat,
)
from backend.pipeline import (
    process_document,
    get_job_status,
    get_job_result,
    generate_export,
)

app = FastAPI(
    title="Document Processor",
    description="OCR document processing API with maximum accuracy",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for OCR processing."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {MAX_FILE_SIZE_MB}MB",
        )

    safe_filename = "".join(
        c for c in file.filename if c.isalnum() or c in "._- "
    )
    file_path = UPLOAD_DIR / safe_filename
    file_path.write_bytes(contents)

    job_id = process_document(str(file_path))

    return UploadResponse(
        job_id=job_id,
        filename=safe_filename,
    )


@app.get("/api/status/{job_id}", response_model=ProcessingStatus)
async def get_processing_status(job_id: str):
    """Get processing status for a job."""
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@app.get("/api/result/{job_id}", response_model=ProcessingResult)
async def get_processing_result(job_id: str):
    """Get processing result for a completed job."""
    result = get_job_result(job_id)
    if not result:
        status = get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        if status.status == "processing":
            raise HTTPException(status_code=202, detail="Job still processing")
        raise HTTPException(status_code=500, detail=f"Job failed: {status.error}")
    return result


@app.get("/api/download/{job_id}/{format}")
async def download_result(job_id: str, format: ExportFormat):
    """Download processed result in specified format."""
    result = get_job_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found or failed")

    output_path = generate_export(job_id, format)
    if not output_path or not output_path.exists():
        raise HTTPException(status_code=500, detail="Export generation failed")

    return FileResponse(
        path=str(output_path),
        filename=f"{job_id}.{format.value}",
        media_type=_get_media_type(format),
    )


def _get_media_type(fmt: ExportFormat) -> str:
    types = {
        ExportFormat.TXT: "text/plain",
        ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return types[fmt]
