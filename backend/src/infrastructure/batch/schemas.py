from datetime import datetime

from pydantic import BaseModel


class BatchJobResponse(BaseModel):
    job_id: int
    job_type: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    created_at: datetime
    completed_at: datetime | None


class BatchJobCreatedResponse(BaseModel):
    job_id: int
    status: str
    total_items: int
