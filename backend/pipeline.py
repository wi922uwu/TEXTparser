"""Document processing pipeline orchestrator."""
import time
import uuid
from pathlib import Path
from typing import Optional
from PIL import Image
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.config import UPLOAD_DIR, RESULT_DIR
from backend.models.schemas import (
    ProcessingResult,
    ProcessingStatus,
    DocumentType,
    TextRegion,
    TableRegion,
    ExportFormat,
)
from backend.preprocess.image import (
    preprocess_for_ocr,
    load_image_from_file,
)
from backend.ocr.engine import EasyOCREngine
from backend.export.text import export_txt, export_docx
from backend.export.table import export_xlsx


_jobs: dict[str, dict] = {}
_executor = ThreadPoolExecutor(max_workers=1)


def process_document(file_path: str) -> str:
    """Start processing a document. Returns job_id."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": ProcessingStatus(
            job_id=job_id,
            status="processing",
            progress=0,
        ),
        "result": None,
        "file_path": file_path,
    }

    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, _run_pipeline, job_id, file_path)

    return job_id


def get_job_status(job_id: str) -> Optional[ProcessingStatus]:
    """Get current processing status for a job."""
    job = _jobs.get(job_id)
    if job:
        return job["status"]
    return None


def get_job_result(job_id: str) -> Optional[ProcessingResult]:
    """Get processing result for a job."""
    job = _jobs.get(job_id)
    if job and job["result"]:
        return job["result"]
    return None


def generate_export(job_id: str, fmt: ExportFormat) -> Optional[Path]:
    """Generate export file for a completed job."""
    job = _jobs.get(job_id)
    if not job or not job["result"]:
        return None

    result: ProcessingResult = job["result"]
    output_path = RESULT_DIR / f"{job_id}.{fmt.value}"

    if fmt == ExportFormat.TXT:
        export_txt(result.text_regions, result.table_regions, output_path)
    elif fmt == ExportFormat.DOCX:
        export_docx(result.text_regions, result.table_regions, output_path)
    elif fmt == ExportFormat.XLSX:
        export_xlsx(result.table_regions, output_path)

    return output_path


def _run_pipeline(job_id: str, file_path: str):
    """Execute the full processing pipeline using EasyOCR."""
    start_time = time.time()

    try:
        _update_status(job_id, "processing", 10)

        images = load_image_from_file(file_path)
        if not images:
            _fail_job(job_id, "Failed to load images from file")
            return

        _update_status(job_id, "processing", 25)

        all_text_regions: list[TextRegion] = []
        all_table_regions: list[TableRegion] = []
        all_text_lines: list[str] = []
        has_tables = False

        ocr_engine = EasyOCREngine()

        for img_idx, image in enumerate(images):
            processed = preprocess_for_ocr(image)

            # OCR on processed (preprocessed) image
            text, confidence = ocr_engine.extract_text(processed)

            all_text_lines.append(text)
            all_text_regions.append(
                TextRegion(text=text, confidence=confidence)
            )

            progress = 25 + int(((img_idx + 1) / len(images)) * 50)
            _update_status(job_id, "processing", progress)

        if has_tables and all_text_lines:
            doc_type = DocumentType.COMBINED
        elif has_tables:
            doc_type = DocumentType.TABLE
        else:
            doc_type = DocumentType.TEXT

        elapsed_ms = int((time.time() - start_time) * 1000)

        _jobs[job_id]["result"] = ProcessingResult(
            job_id=job_id,
            document_type=doc_type,
            text_regions=all_text_regions,
            table_regions=all_table_regions,
            full_text="\n\n".join(all_text_lines),
            processing_time_ms=elapsed_ms,
        )

        _update_status(job_id, "completed", 100, doc_type)

    except Exception as e:
        _fail_job(job_id, str(e))


def _update_status(
    job_id: str,
    status: str,
    progress: int,
    doc_type: Optional[DocumentType] = None,
):
    """Update job status."""
    job = _jobs.get(job_id)
    if job:
        job["status"] = ProcessingStatus(
            job_id=job_id,
            status=status,
            progress=progress,
            document_type=doc_type,
        )


def _fail_job(job_id: str, error: str):
    """Mark job as failed."""
    job = _jobs.get(job_id)
    if job:
        job["status"] = ProcessingStatus(
            job_id=job_id,
            status="failed",
            progress=0,
            error=error,
        )
