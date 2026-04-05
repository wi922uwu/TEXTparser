"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ProcessRequest(BaseModel):
    """Request to process uploaded file."""
    file_id: str = Field(..., description="Uploaded file ID")
    formats: List[str] = Field(
        default=["txt", "docx", "xlsx", "csv"],
        description="Export formats"
    )
    quality_preset: str = Field(
        default="balanced",
        description="Quality preset: fast, balanced, or high_quality"
    )


class TaskStatus(BaseModel):
    """Task status response."""
    task_id: str
    status: str
    progress: Optional[int] = None
    step: Optional[str] = None
    error: Optional[str] = None


class ProcessResponse(BaseModel):
    """Response after starting processing."""
    task_id: str
    message: str = "Processing started"


class UploadResponse(BaseModel):
    """Response after file upload."""
    file_id: str
    filename: str
    size: int
    message: str = "File uploaded successfully"


class ResultInfo(BaseModel):
    """Information about processing result."""
    file_id: str
    formats: List[str]
    page_count: int
    has_tables: bool
