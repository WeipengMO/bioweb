# TCGA PanCanAtlas Data Plan

## Source

Official GDC page: https://gdc.cancer.gov/about-data/publications/pancanatlas

The page states that PanCanAtlas compares 33 TCGA tumor types and provides open supplemental files for RNA, RPPA, methylation, miRNA, copy number, mutation, clinical outcome, clinical follow-up, quality annotations, and PARADIGM pathway inference.

## Local Storage

All PanCanAtlas files live under:

```text
data/tcga/pancanatlas/
```

Subdirectories:

- `raw/`: original downloaded GDC files.
- `processed/`: normalized Parquet/DuckDB-ready tables for the app.
- `manifests/`: GDC manifests and source page snapshots.
- `metadata/`: registry and download logs.

## Download Registry

The machine-readable registry is:

```text
data/tcga/pancanatlas/metadata/pancanatlas_registry.json
```

Future code should read this file instead of scattering GDC UUIDs through the application.

## Download Commands

```bash
source .venv/bin/activate
export https_proxy=http://172.18.50.109:7890
export http_proxy=http://172.18.50.109:7890
python scripts/data/download_pancanatlas.py metadata
python scripts/data/download_pancanatlas.py core
```

Large expression matrix:

```bash
python scripts/data/download_pancanatlas.py dataset rna_expression
```

Downloaded in this workspace:

- RNA expression matrix, 1,882,540,959 bytes.
- TCGA-CDR outcome table.
- Clinical follow-up table.
- Merged sample quality annotations.
- Open-access and controlled-access manifest files.

Processed binary files generated in this workspace:

- `data/tcga/pancanatlas/processed/pancanatlas_rnaseq_gene_expression_wide.parquet`
- `data/tcga/pancanatlas/processed/tcga_cdr_survival.parquet`

Regenerate them with:

```bash
source .venv/bin/activate
python scripts/data/prepare_pancanatlas.py
```

All registered open small files:

```bash
python scripts/data/download_pancanatlas.py all-open
```

All registered open files, including large matrices:

```bash
python scripts/data/download_pancanatlas.py all-open --include-large
```

## Frontend Module Shape

The older `/data/user/mowp/workspace/bio_webui` app presents modules from a sidebar: ORA, GSEA, Survival, and ORA for AnnData. BioWeb should keep that idea but map it to the React workspace:

- Sidebar modules:
  - TCGA PanCancer
  - ORA Enrichment
  - Jobs
  - Future: GSEA, AnnData ORA, Mutation, Copy Number, Methylation
- Each module owns:
  - A compact input panel.
  - A result table tab.
  - A plot/result artifact tab when relevant.
  - A job history connection.

Do not copy Streamlit code from `bio_webui`; only preserve the module-oriented presentation pattern.
