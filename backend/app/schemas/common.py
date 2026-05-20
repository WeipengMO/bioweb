from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class JobRead(BaseModel):
    id: UUID
    analysis_type: str
    status: JobStatus
    parameters: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class TableResult(BaseModel):
    records: list[dict[str, Any]] = Field(default_factory=list)

