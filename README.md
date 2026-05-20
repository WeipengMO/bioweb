# BioWeb

BioWeb 是一个个人科研 Web 应用，用于把常用生信分析做成可重复、可扩展、可视化的工作台。目前重点是 TCGA PanCancer 和 gene-set enrichment。

## Current Features

- TCGA PanCancer
  - Expression view
    - 支持单基因或多基因平均表达 signature。
    - 展示输入基因在不同 TCGA 癌种 tumor 样本中的表达分布。
    - 支持按癌种字母顺序或表达量从高到低排序。
    - 输出跨癌种 boxplot 和每个癌种的表达统计表。
  - Survival analysis
    - 支持单基因或多基因平均表达 signature。
    - 支持 median split、手动 percentile、optimal threshold。
    - 使用真实 PanCanAtlas RNA 表达矩阵和 TCGA-CDR 生存结局。
    - 使用 `lifelines` 计算 Kaplan-Meier 曲线和 p value。
    - 输出 KM plot。
  - Tumor vs normal expression
    - 支持单基因。
    - 使用 TCGA barcode sample type 区分 tumor 和 normal。
    - 使用 Welch t-test 计算 p value。
    - 输出 boxplot。
- Gene Enrichment
  - ORA enrichment
    - 使用新版 `decoupler` 从 OmniPath 下载 MSigDB，并保存为本地 Parquet。
    - 支持 MSigDB collection 多选。
    - 支持 Query genes 普通 ORA。
    - 支持 Up genes / Down genes 分组 ORA。
    - 支持自定义 background genes、FDR threshold、min overlap、max terms。
    - 输出富集表和 barplot。
  - GSEA enrichment
    - 支持粘贴 `gene score` 排序表。
    - 支持 MSigDB collection 多选、FDR threshold、min overlap、max terms。
    - 使用 `decoupler.mt.gsea` 计算 gene-set enrichment。
    - 输出 GSEA score 表和 signed barplot。
- Frontend workspace
  - React/Vite 单页工作台，采用浅色 Read the Docs 风格。
  - 模块化侧边栏：TCGA 和 Enrichment 独立切换。
  - 结果图支持悬停放大镜和当前页放大预览。
  - 支持桌面、平板和移动端自适应布局。

## Stack

- Backend: FastAPI
- Analysis package: `packages/bioweb_analysis`
- Frontend: React + Vite
- Matrix data: TCGA raw TSV + processed Parquet
- Plotting: matplotlib
- Statistics: lifelines, scipy, decoupler
- Future async/persistence: Celery + Redis + PostgreSQL

## Quick Start

Backend:

```bash
cd /data/user/mowp/workspace/bioweb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e packages/bioweb_analysis
PORT=8010 ./scripts/dev_backend.sh
```

Frontend:

```bash
cd /data/user/mowp/workspace/bioweb/frontend
npm install --registry=https://registry.npmmirror.com
cd ..
./scripts/dev_frontend.sh
```

Open:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8010
API docs: http://localhost:8010/docs
```

## Data Setup

TCGA PanCanAtlas data lives under:

```text
data/tcga/pancanatlas/
```

Layout:

- `raw/`: original downloaded GDC files.
- `processed/`: Parquet files for fast reads.
- `manifests/`: GDC manifest files and publication page snapshot.
- `metadata/`: registry and download logs.

Downloaded core files in this workspace:

- `raw/EBPlusPlusAdjustPANCAN_IlluminaHiSeq_RNASeqV2.geneExp.tsv`
- `raw/TCGA-CDR-SupplementalTableS1.xlsx`
- `raw/clinical_PANCAN_patient_with_followup.tsv`
- `raw/merged_sample_quality_annotations.tsv`

Processed binary files:

- `processed/pancanatlas_rnaseq_gene_expression_wide.parquet`
- `processed/tcga_cdr_survival.parquet`

Download or refresh:

```bash
source .venv/bin/activate
export https_proxy=http://172.18.50.109:7890
export http_proxy=http://172.18.50.109:7890
python scripts/data/download_pancanatlas.py metadata
python scripts/data/download_pancanatlas.py core
python scripts/data/download_pancanatlas.py dataset rna_expression
python scripts/data/prepare_pancanatlas.py
```

Detailed notes: `docs/data/TCGA_PANCANATLAS.md`.

MSigDB data lives under:

```text
data/msigdb/msigdb.parquet
```

The normalized table has:

- `collection`
- `term`
- `gene`

Download or refresh:

```bash
source .venv/bin/activate
python scripts/data/download_msigdb.py
```

The script uses `decoupler.op.resource(name="MSigDB", license="academic")` and writes the normalized Parquet file.

## Result Files

Plots are temporary files under:

```text
data/results/
```

Cleanup policy:

- Backend startup deletes result PNG files older than 24 hours.
- Each new plot clears old PNGs for that analysis module before writing a new plot.

## Project Map

- `backend/`: FastAPI app, routes, schemas, services, static result serving.
- `packages/bioweb_analysis/`: pure Python analysis package.
- `frontend/`: React/Vite UI.
- `scripts/data/`: data download and preprocessing scripts.
- `data/`: local datasets and generated results.
- `docs/PROJECT_SPEC.md`: project rules and long-term design.
- `docs/AI_DEVELOPMENT_GUIDE.md`: focused guide for future AI coding agents.

## Development Checks

```bash
source .venv/bin/activate
pytest -q
ruff check backend packages tests scripts
cd frontend
PATH=/home/mowp/.nvm/versions/node/v24.15.0/bin:$PATH npm run build
```

## Important Rules

- Keep heavy statistical logic in `packages/bioweb_analysis`, not FastAPI route handlers.
- Keep frontend as a module-based workspace: select app module, then select an independent analysis.
- Do not commit raw TCGA files, Parquet matrices, generated plots, or local database files.
- When adding a new analysis, preserve the existing result shape:
  - `summary`
  - optional `plot_url`
  - `records`
