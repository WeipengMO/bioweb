from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from backend.app.schemas.common import JobRead, JobStatus


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[UUID, JobRead] = {}

    def create(self, analysis_type: str, parameters: dict[str, Any]) -> JobRead:
        now = datetime.now(timezone.utc)
        job = JobRead(
            id=uuid4(),
            analysis_type=analysis_type,
            status=JobStatus.queued,
            parameters=parameters,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.id] = job
        return job

    def update(
        self,
        job_id: UUID,
        *,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> JobRead:
        job = self._jobs[job_id]
        updated = job.model_copy(
            update={
                "status": status,
                "result": result,
                "error": error,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._jobs[job_id] = updated
        if status in {JobStatus.succeeded, JobStatus.failed}:
            self._jobs.pop(job_id, None)
        return updated

    def get(self, job_id: UUID) -> JobRead | None:
        return self._jobs.get(job_id)

    def list(self) -> list[JobRead]:
        return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)


job_store = InMemoryJobStore()
