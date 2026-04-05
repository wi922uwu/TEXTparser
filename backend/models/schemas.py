"""API request and response schemas."""
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class ExportFormat(str, Enum):
    TXT = "txt"
    DOCX = "docx"
    XLSX = "xlsx"


class DocumentType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    COMBINED = "combined"


class UploadResponse(BaseModel):
    job_id: str
    filename: str
    status: str = "processing"


class ProcessingStatus(BaseModel):
    job_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    error: Optional[str] = None
    document_type: Optional[DocumentType] = None


class TextRegion(BaseModel):
    text: str
    confidence: float
    bbox: Optional[tuple[int, int, int, int]] = None


class TableRegion(BaseModel):
    cells: list[list[str]]
    bbox: Optional[tuple[int, int, int, int]] = None


class ProcessingResult(BaseModel):
    job_id: str
    document_type: DocumentType
    text_regions: list[TextRegion] = []
    table_regions: list[TableRegion] = []
    full_text: str = ""
    processing_time_ms: int = 0
