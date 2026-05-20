from fastapi import APIRouter

from backend.app.schemas.common import JobRead
from backend.app.schemas.enrichment import GseaRequest, OraRequest
from backend.app.services.enrichment_service import run_gsea, run_ora

router = APIRouter()


@router.post("/ora", response_model=JobRead)
def ora_endpoint(request: OraRequest) -> JobRead:
    return run_ora(request)


@router.post("/gsea", response_model=JobRead)
def gsea_endpoint(request: GseaRequest) -> JobRead:
    return run_gsea(request)
