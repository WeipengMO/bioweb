# AI Development Guide

Read this file before modifying BioWeb. It explains the project shape, current behavior, and where future AI agents should add code.

## Current Goal

BioWeb is a personal biomedical research web app. It should stay modular: each analysis is independent in the UI, backed by one API endpoint, and implemented by one pure function in the analysis package.

## Current Working Modules

### TCGA PanCancer: Expression View

Frontend:

- `frontend/src/App.tsx`
- Analysis key: `tcga_expression`
- Inputs:
  - one or more genes
  - project sorting: alphabetical or expression high-to-low
  - show data points

Backend:

- Route: `POST /api/tcga/expression`
- Schema: `backend/app/schemas/tcga.py::ExpressionRequest`
- Service: `backend/app/services/tcga_service.py::run_expression`
- Analysis: `packages/bioweb_analysis/bioweb_analysis/tcga.py::expression_visualization`

Output:

- `summary`
- `plot_url` for cross-cancer expression boxplot
- `records`, one row per TCGA project

Behavior:

- Uses tumor samples only, based on TCGA sample type codes `01-09`.
- A single gene is plotted directly.
- Multiple genes are averaged into one expression signature before comparing cancer projects.
- Default sorting is alphabetical by project.

### TCGA PanCancer: Survival Analysis

Frontend:

- `frontend/src/App.tsx`
- Analysis key: `tcga_survival`
- Inputs:
  - cancer project
  - survival endpoint: OS, DSS, PFI, DFI
  - time unit: days or months
  - grouping method: median, percentile, optimal
  - one or more genes

Backend:

- Route: `POST /api/tcga/survival`
- Schema: `backend/app/schemas/tcga.py::SurvivalRequest`
- Service: `backend/app/services/tcga_service.py::run_survival`
- Analysis: `packages/bioweb_analysis/bioweb_analysis/tcga.py::survival_analysis`

Output:

- `summary`
- `plot_url` for KM plot
- `records` for high/low groups

### TCGA PanCancer: Tumor vs Normal

Frontend:

- Analysis key: `tcga_tumor_normal`
- Inputs:
  - cancer project
  - one gene

Backend:

- Route: `POST /api/tcga/tumor-normal`
- Schema: `backend/app/schemas/tcga.py::TumorNormalRequest`
- Service: `backend/app/services/tcga_service.py::run_tumor_normal`
- Analysis: `packages/bioweb_analysis/bioweb_analysis/tcga.py::tumor_normal_compare`

Output:

- `summary`
- `plot_url` for boxplot
- `records` for tumor and normal groups

### TCGA PanCancer: Gene Correlation

Frontend:

- Analysis key: `tcga_correlation`
- Inputs:
  - cancer project
  - signature genes for x
  - signature genes for y
  - Pearson or Spearman

Backend:

- Route: `POST /api/tcga/correlation`
- Schema: `backend/app/schemas/tcga.py::CorrelationRequest`
- Service: `backend/app/services/tcga_service.py::run_correlation`
- Analysis: `packages/bioweb_analysis/bioweb_analysis/tcga.py::correlation_analysis`

Output:

- `summary`
- `plot_url` for scatter plot
- `records` with r, p value, and sample count

### Enrichment: ORA

Frontend:

- Analysis key: `enrichment_ora`
- Inputs:
  - MSigDB collection multi-select
  - query genes
  - optional up genes and down genes
  - optional background genes
  - min overlap
  - max terms
  - FDR threshold

Backend:

- Route: `POST /api/ora/ora`
- Schema: `backend/app/schemas/enrichment.py::OraRequest`
- Service: `backend/app/services/enrichment_service.py::run_ora`
- Analysis: `packages/bioweb_analysis/bioweb_analysis/enrichment.py::ora`

Output:

- `summary`
- `plot_url` for ORA barplot
- `records` with term, collection, overlap, p value, adjusted p value, and overlap genes

Behavior:

- If `up_genes` or `down_genes` are provided, ORA is run separately for those directions and `direction` is included in the table.
- If no direction-specific lists are provided, `genes` is used as one query and `direction` is `query`.
- If `background_genes` is empty, the background is all genes in the selected collections.

### Enrichment: GSEA

Frontend:

- Analysis key: `enrichment_gsea`
- Inputs:
  - MSigDB collection multi-select
  - ranked genes as `gene score` lines
  - min overlap
  - max terms
  - FDR threshold

Backend:

- Route: `POST /api/ora/gsea`
- Schema: `backend/app/schemas/enrichment.py::GseaRequest`
- Service: `backend/app/services/enrichment_service.py::run_gsea`
- Analysis: `packages/bioweb_analysis/bioweb_analysis/enrichment.py::gsea`

Output:

- `summary`
- `plot_url` for signed GSEA score barplot
- `records` with term, score, p value, adjusted p value, term size, and leading genes

Behavior:

- Uses `decoupler.mt.gsea`.
- Positive scores are shown as up/enriched direction with light red bars.
- Negative scores are shown as down direction with light blue bars.

## Data Files

Raw TCGA files:

```text
data/tcga/pancanatlas/raw/
```

Processed files used by analysis code:

```text
data/tcga/pancanatlas/processed/pancanatlas_rnaseq_gene_expression_wide.parquet
data/tcga/pancanatlas/processed/tcga_cdr_survival.parquet
```

MSigDB file used by enrichment code:

```text
data/msigdb/msigdb.parquet
```

The MSigDB Parquet must have:

- `collection`
- `term`
- `gene`

Regenerate processed files:

```bash
source .venv/bin/activate
python scripts/data/prepare_pancanatlas.py
```

Refresh MSigDB:

```bash
source .venv/bin/activate
python scripts/data/download_msigdb.py
```

The analysis package should prefer processed Parquet files. Raw TSV/XLSX should be fallback or preprocessing input, not the default runtime path.

## Architecture Rules

Dependency direction:

- `frontend -> backend HTTP`
- `backend -> bioweb_analysis`
- `bioweb_analysis -> pandas/numpy/scipy/lifelines/matplotlib/decoupler`

Forbidden:

- `bioweb_analysis` must not import FastAPI, SQLAlchemy, Celery, or frontend code.
- Frontend must not read local files directly.
- Route handlers must not contain statistics or plotting logic.

## Frontend Pattern

Use `frontend/src/App.tsx` as the current module workspace.

The pattern is:

1. Sidebar selects top-level app module, e.g. TCGA or Enrichment.
2. The left panel starts with an editable dropdown for independent analysis selection.
3. Each analysis has its own panel component under that picker.
4. The right Result panel aligns with the left panel on wide screens and renders:
   - summary
   - optional plot
   - records table
5. On narrow screens, the sidebar becomes a top horizontal nav and the analysis/result panels stack.

Combobox requirements:

- User can type to filter.
- Clicking the triangle should show all options even when an input has text.
- TCGA cancer project options show abbreviation on the first line and full name on the second line.
- Selected cancer project displays only the abbreviation.
- Multi-select collection controls should behave like a tag input: selected pills, type-to-filter, and checkable menu items.

## Plot Rules

Temporary plots are served from:

```text
/results/...
```

Local files live under:

```text
data/results/
```

Cleanup rules:

- Backend startup removes PNG files older than 24 hours.
- New plots clear existing PNGs for that result module before writing the next plot.

KM plot style:

- Legend order: High above Low.
- Legend labels: `High (n=...)`, `Low (n=...)`.
- No legend frame.
- p value is shown in lower left as `p = ...`.
- If one gene, title includes the gene.
- If multiple genes, title omits gene names.

Tumor-normal boxplot style:

- Tumor and Normal groups.
- p value shown as `p = ...`.
- Keep plot readable for a single gene.

Expression view plot style:

- One box per TCGA project.
- Use tumor samples only.
- Light blue boxes.
- If multiple genes are supplied, label y-axis as mean expression.
- Project labels may rotate to keep the plot readable.

ORA plot style:

- Horizontal barplot of `-log10(p value)`.
- Bars use `#ADD8E6` with no outline.
- Term labels are drawn on top of bars, black text, underscores replaced with spaces, wrapped as needed.

GSEA plot style:

- Horizontal signed barplot of GSEA score.
- Up/positive terms use light red bars.
- Down/negative terms use `#ADD8E6`.
- No bar outlines.
- Positive term labels are placed to the right of the zero axis and left-aligned.
- Negative term labels are placed to the left of the zero axis and right-aligned.

Frontend plot interaction:

- Result plots show a zoom button on hover.
- Clicking the zoom button opens an in-page modal preview with a short fade/scale animation.

## Adding A New Analysis

Follow this sequence:

1. Add or update request schema in `backend/app/schemas/`.
2. Add pure analysis function in `packages/bioweb_analysis/bioweb_analysis/`.
3. Add service wrapper in `backend/app/services/`.
4. Add API route in `backend/app/api/routes/`.
5. Add frontend API client in `frontend/src/api/client.ts`.
6. Add an independent frontend panel in `frontend/src/App.tsx` or a component file if App grows too large.
7. Add tests in `tests/`.
8. Run:

```bash
pytest -q
ruff check backend packages tests scripts
cd frontend
PATH=/home/mowp/.nvm/versions/node/v24.15.0/bin:$PATH npm run build
```

## Current Caveats

- Jobs are not a visible module. The backend still wraps responses in `JobRead` for a stable API shape, but completed in-memory records are immediately released.
- Celery, Redis, and PostgreSQL are scaffolded for future growth but not required for current synchronous local analysis.
- Analysis execution is synchronous. Very large future analyses should move to Celery-backed jobs before exposing them broadly.
- The current React app still lives mainly in `frontend/src/App.tsx`; split components into separate files once the workspace grows further.
