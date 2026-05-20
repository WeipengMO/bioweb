from uuid import UUID

from fastapi import APIRouter, HTTPException

from backend.app.schemas.common import JobRead
from backend.app.services.job_store import job_store

router = APIRouter()


@router.get("", response_model=list[JobRead])
def list_jobs() -> list[JobRead]:
    return job_store.list()


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: UUID) -> JobRead:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

