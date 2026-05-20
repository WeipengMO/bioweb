from fastapi import APIRouter

from backend.app.schemas.common import JobRead
from backend.app.schemas.tcga import CorrelationRequest, ExpressionRequest, SurvivalRequest, TumorNormalRequest
from backend.app.services.tcga_service import run_correlation, run_expression, run_survival, run_tumor_normal

router = APIRouter()


@router.post("/survival", response_model=JobRead)
def survival(request: SurvivalRequest) -> JobRead:
    return run_survival(request)


@router.post("/correlation", response_model=JobRead)
def correlation(request: CorrelationRequest) -> JobRead:
    return run_correlation(request)


@router.post("/tumor-normal", response_model=JobRead)
def tumor_normal(request: TumorNormalRequest) -> JobRead:
    return run_tumor_normal(request)


@router.post("/expression", response_model=JobRead)
def expression(request: ExpressionRequest) -> JobRead:
    return run_expression(request)
