#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/tcga/pancanatlas/raw"
PROCESSED_DIR = ROOT / "data/tcga/pancanatlas/processed"
EXPRESSION_TSV = RAW_DIR / "EBPlusPlusAdjustPANCAN_IlluminaHiSeq_RNASeqV2.geneExp.tsv"
EXPRESSION_PARQUET = PROCESSED_DIR / "pancanatlas_rnaseq_gene_expression_wide.parquet"
CDR_XLSX = RAW_DIR / "TCGA-CDR-SupplementalTableS1.xlsx"
CDR_PARQUET = PROCESSED_DIR / "tcga_cdr_survival.parquet"


def prepare_expression() -> None:
    if not EXPRESSION_TSV.exists():
        raise FileNotFoundError(EXPRESSION_TSV)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(EXPRESSION_TSV, sep="\t")
    frame.columns = [column.strip('"') for column in frame.columns]
    frame["gene_symbol"] = frame["gene_id"].astype(str).str.strip('"').str.split("|", n=1).str[0].str.upper()
    cols = ["gene_symbol", "gene_id", *[column for column in frame.columns if column not in {"gene_symbol", "gene_id"}]]
    frame = frame.loc[:, cols]
    frame.to_parquet(EXPRESSION_PARQUET, index=False)
    print(f"wrote {EXPRESSION_PARQUET} ({EXPRESSION_PARQUET.stat().st_size} bytes)")


def prepare_cdr() -> None:
    if not CDR_XLSX.exists():
        raise FileNotFoundError(CDR_XLSX)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_excel(CDR_XLSX, sheet_name="TCGA-CDR")
    frame["project"] = "TCGA-" + frame["type"].astype(str)
    frame.to_parquet(CDR_PARQUET, index=False)
    print(f"wrote {CDR_PARQUET} ({CDR_PARQUET.stat().st_size} bytes)")


def main() -> int:
    prepare_cdr()
    prepare_expression()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

