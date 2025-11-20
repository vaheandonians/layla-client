from pydantic import BaseModel, Field
from typing import Optional


class OcrJobResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the submitted OCR job")
    status: str = Field(..., description="Current status of the job")
    model: str = Field(..., description="OCR model used for processing")
    message: str = Field(..., description="Human-readable status message")
    result: Optional[str] = Field(None, description="OCR result in markdown format (only present if status is completed)")


class JobStatusResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the job")
    status: str = Field(..., description="Current status of the job (processing/completed/failed)")
    model: Optional[str] = Field(None, description="OCR model used for processing")
    progress: Optional[str] = Field(None, description="Progress information if job is processing")
    result: Optional[str] = Field(None, description="OCR result in markdown format (only present if status is completed)")
    error: Optional[str] = Field(None, description="Error message if job failed")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status of the service")
    redis: str = Field(..., description="Redis connection status")
    queue_size: Optional[int] = Field(None, description="Number of jobs in the queue")


class JobDeleteResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the deleted job")
    message: str = Field(..., description="Confirmation message")

