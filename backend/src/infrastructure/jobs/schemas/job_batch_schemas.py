"""Pydantic schemas for job batch API responses."""

from datetime import datetime

from pydantic import BaseModel


class JobBatchResponse(BaseModel):
    id: int
    batch_type: str
    reference_id: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    status: str
    created_at: datetime
    updated_at: datetime
