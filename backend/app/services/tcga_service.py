from backend.app.schemas.common import JobRead, JobStatus
from backend.app.schemas.tcga import CorrelationRequest, ExpressionRequest, SurvivalRequest, TumorNormalRequest
from backend.app.services.job_store import job_store
from bioweb_analysis.tcga import correlation_analysis, expression_visualization, survival_analysis, tumor_normal_compare


def run_survival(request: SurvivalRequest) -> JobRead:
    job = job_store.create("tcga_survival", request.model_dump())
    try:
        result = survival_analysis(**request.model_dump())
        return job_store.update(job.id, status=JobStatus.succeeded, result=result)
    except Exception as exc:
        return job_store.update(job.id, status=JobStatus.failed, error=str(exc))


def run_correlation(request: CorrelationRequest) -> JobRead:
    job = job_store.create("tcga_correlation", request.model_dump())
    try:
        result = correlation_analysis(**request.model_dump())
        return job_store.update(job.id, status=JobStatus.succeeded, result=result)
    except Exception as exc:
        return job_store.update(job.id, status=JobStatus.failed, error=str(exc))


def run_tumor_normal(request: TumorNormalRequest) -> JobRead:
    job = job_store.create("tcga_tumor_normal", request.model_dump())
    try:
        result = tumor_normal_compare(**request.model_dump())
        return job_store.update(job.id, status=JobStatus.succeeded, result=result)
    except Exception as exc:
        return job_store.update(job.id, status=JobStatus.failed, error=str(exc))


def run_expression(request: ExpressionRequest) -> JobRead:
    job = job_store.create("tcga_expression", request.model_dump())
    try:
        result = expression_visualization(**request.model_dump())
        return job_store.update(job.id, status=JobStatus.succeeded, result=result)
    except Exception as exc:
        return job_store.update(job.id, status=JobStatus.failed, error=str(exc))
