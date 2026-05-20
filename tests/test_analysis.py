from bioweb_analysis.enrichment import gsea, ora
from bioweb_analysis.tcga import correlation_analysis, expression_visualization, survival_analysis, tumor_normal_compare


def test_survival_returns_groups():
    result = survival_analysis(project="TCGA-LUAD", genes=["TP53"])
    assert result["summary"]["project"] == "TCGA-LUAD"
    assert len(result["records"]) == 2


def test_correlation_returns_single_row():
    result = correlation_analysis(project="TCGA-LUAD", genes=["TP53"], target_genes=["EGFR", "MYC"])
    assert len(result["records"]) == 1
    rec = result["records"][0]
    assert rec["x_genes"] == "TP53"
    assert rec["y_genes"] == "EGFR,MYC"
    assert "r" in rec
    assert "p_value" in rec
    assert rec["n_samples"] > 0


def test_tumor_normal_returns_gene_rows():
    result = tumor_normal_compare(project="TCGA-BRCA", genes=["TP53"])
    assert len(result["records"]) == 2
    assert result["plot_url"].startswith("/results/tcga/")


def test_expression_visualization_returns_gene_rows():
    result = expression_visualization(project="ALL", genes=["TP53", "MDM2"])
    assert len(result["records"]) > 2
    assert result["plot_url"].startswith("/results/tcga/")
    assert result["summary"]["sample_type"] == "tumor"
    assert result["summary"]["n_projects"] == len(result["records"])


def test_ora_returns_overlap():
    result = ora(genes=["TP53", "MDM2", "CDKN1A"], collections=["hallmark"], min_overlap=2)
    assert result["records"]
    assert result["records"][0]["term"] == "HALLMARK_P53_PATHWAY"


def test_ora_supports_direction_and_background():
    result = ora(
        genes=["TP53"],
        up_genes=["TP53", "MDM2", "CDKN1A"],
        down_genes=["EGFR", "MYC"],
        background_genes=["TP53", "MDM2", "CDKN1A", "EGFR", "MYC"],
        collections=["hallmark"],
        min_overlap=1,
        top_n=5,
        fdr_threshold=1,
    )
    assert result["records"]
    assert {record["direction"] for record in result["records"]} <= {"up", "down"}


def test_gsea_returns_ranked_terms():
    result = gsea(
        rankings=[
            {"gene": "TP53", "score": 2.0},
            {"gene": "MDM2", "score": 1.5},
            {"gene": "CDKN1A", "score": 1.2},
            {"gene": "EGFR", "score": -1.0},
            {"gene": "MYC", "score": -1.5},
        ],
        collections=["hallmark", "kegg_pathways"],
        min_overlap=1,
        top_n=5,
        fdr_threshold=1,
    )
    assert result["records"]
    assert "score" in result["records"][0]
