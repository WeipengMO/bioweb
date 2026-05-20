from backend.app.schemas.enrichment import GseaRequest, OraRequest
from backend.app.schemas.common import JobRead, JobStatus
from backend.app.services.job_store import job_store
from bioweb_analysis.enrichment import gsea, ora


def run_ora(request: OraRequest) -> JobRead:
    job = job_store.create("ora", request.model_dump())
    try:
        result = ora(**request.model_dump())
        return job_store.update(job.id, status=JobStatus.succeeded, result=result)
    except Exception as exc:
        return job_store.update(job.id, status=JobStatus.failed, error=str(exc))


def run_gsea(request: GseaRequest) -> JobRead:
    job = job_store.create("gsea", request.model_dump())
    try:
        result = gsea(**request.model_dump())
        return job_store.update(job.id, status=JobStatus.succeeded, result=result)
    except Exception as exc:
        return job_store.update(job.id, status=JobStatus.failed, error=str(exc))
