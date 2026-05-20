from backend.app.api.routes.health import health
from backend.app.main import app
from backend.app.schemas.enrichment import GseaRequest, OraRequest
from backend.app.schemas.tcga import ExpressionRequest
from backend.app.services.enrichment_service import run_gsea, run_ora
from backend.app.services.tcga_service import run_expression


def test_health():
    assert health() == {"status": "ok"}
    assert any(route.path == "/api/health" for route in app.routes)


def test_ora_endpoint():
    job = run_ora(
        OraRequest(genes=["TP53", "MDM2", "CDKN1A"], collections=["hallmark"], min_overlap=2),
    )
    assert job.status == "succeeded"
    assert job.result
    assert job.result["records"]


def test_gsea_endpoint():
    job = run_gsea(
        GseaRequest(
            rankings=[
                {"gene": "TP53", "score": 2.0},
                {"gene": "MDM2", "score": 1.5},
                {"gene": "CDKN1A", "score": 1.2},
                {"gene": "EGFR", "score": -1.0},
            ],
            collections=["hallmark"],
            min_overlap=1,
            fdr_threshold=1,
        ),
    )
    assert job.status == "succeeded"
    assert job.result
    assert job.result["records"]


def test_tcga_expression_endpoint():
    job = run_expression(ExpressionRequest(project="ALL", genes=["TP53", "MDM2"]))
    assert job.status == "succeeded"
    assert job.result
    assert len(job.result["records"]) > 2
