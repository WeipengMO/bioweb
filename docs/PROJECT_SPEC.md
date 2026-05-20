# BioWeb Project Specification

This document is the first file future AI agents should read before changing the project.

## Product Goal

BioWeb is a personal biomedical research web app. It should make common analyses repeatable, inspectable, and extensible:

- TCGA PanCancer analysis:
  - Cross-cancer expression visualization by one gene or an averaged multi-gene expression signature.
  - Survival analysis by one gene or an averaged multi-gene expression signature.
  - Grouping methods: median split, manual percentile split, and optimal threshold.
  - Gene correlation analysis using one gene or averaged multi-gene signature.
  - Tumor vs normal expression comparison.
  - Future TCGA modules must fit the same analysis/job/result contract.
- Gene-set enrichment:
  - ORA enrichment from query genes or separate up/down gene lists.
  - GSEA enrichment from ranked `gene score` inputs.
  - MSigDB collection multi-select using local normalized MSigDB data.
  - Optional ORA background genes, FDR threshold, min overlap, and max returned terms.
  - Return enrichment tables and matplotlib plots.

## Architecture

Use a monorepo with stable boundaries:

- `backend/`
  - FastAPI application and HTTP schemas.
  - Owns auth, API routing, task creation, persistence, result file registration, and validation of web inputs.
  - Must not contain heavy statistical logic.
- `packages/bioweb_analysis/`
  - Independent Python package for analysis functions.
  - Receives typed inputs and returns typed/tabular outputs.
  - Must not import FastAPI, SQLAlchemy, Celery, or frontend code.
- `frontend/`
  - React client for submitting independent analyses and viewing current results.
  - Talks only to backend HTTP APIs.
- `data/`
  - Local runtime data. Do not commit large datasets.

## Dependency Direction

Allowed:

- `backend -> bioweb_analysis`
- `frontend -> backend HTTP API`
- `bioweb_analysis -> numpy/pandas/scipy/matplotlib/duckdb/lifelines/decoupler`

Forbidden:

- `bioweb_analysis -> backend`
- `bioweb_analysis -> FastAPI/Celery/SQLAlchemy`
- `frontend -> local data files`

## Backend Layout

- `backend/app/main.py`: app factory and router registration.
- `backend/app/core/config.py`: settings from environment variables.
- `backend/app/api/routes/`: thin HTTP route modules.
- `backend/app/schemas/`: Pydantic request/response models.
- `backend/app/services/`: application services that coordinate tasks, files, and analysis calls.
- `backend/app/tasks/`: Celery task definitions.
- `backend/app/models/`: SQLAlchemy ORM models.
- `backend/app/db/`: database session and initialization.

Routes should validate inputs, call a service, and return schemas. They should not directly perform heavy analysis.

## Analysis Package Layout

- `tcga.py`: TCGA analysis entry points.
- `enrichment.py`: ORA and GSEA enrichment entry points.
- `plotting.py`: matplotlib plotting helpers.
- `datasets.py`: DuckDB/Parquet loading helpers.
- `types.py`: dataclasses and shared literals.

Analysis functions should be deterministic, testable, and usable from a notebook.

## Data Contract

TCGA expression data should be stored as Parquet and queried via DuckDB. Prefer long-format tables when possible:

- `project`: TCGA cancer project, e.g. `TCGA-LUAD`.
- `sample_id`
- `sample_type`: `tumor` or `normal`
- `gene`
- `expression`

Clinical/survival metadata should include:

- `project`
- `sample_id`
- `time`
- `event`
- optional covariates

Gene-set files must use a simple tabular format:

- `collection`
- `term`
- `gene`

MSigDB is downloaded with `decoupler.op.resource(name="MSigDB", license="academic")`, normalized to the table above, and stored at:

```text
data/msigdb/msigdb.parquet
```

GSEA inputs should be represented as records with:

- `gene`
- `score`

TCGA expression visualization across cancer types should return one table row per TCGA project. If multiple genes are supplied, the analysis uses the mean expression signature across those genes.

## Result Contract

Current synchronous analysis responses use the `JobRead` wrapper for API stability, but completed in-memory job records are immediately released. The user-facing frontend does not expose a Jobs module.

Every analysis result should preserve this inner shape:

- `summary`: compact key/value facts and p values.
- `plot_url`: optional URL for generated matplotlib artifact.
- `records`: table rows for the frontend result table.

Current API responses wrap this inner result in `JobRead` for stability. The synchronous services immediately return a succeeded or failed job object.

## Future Job Contract

Long-running analyses must be represented as jobs:

- `id`
- `analysis_type`
- `status`: `queued`, `running`, `succeeded`, `failed`
- `parameters`
- `result`
- `error`
- timestamps

Production mode should replace the current synchronous wrapper with PostgreSQL-backed records only when long-running async execution is needed.

## API Principles

- All analysis endpoints should support synchronous execution for small local development inputs.
- Heavy production execution should be submitted to Celery and polled by job ID.
- Preserve response schemas when internals change.
- Return result tables as JSON records and plot artifacts as registered file paths or URLs.

Current analysis routes:

- `POST /api/tcga/expression`
- `POST /api/tcga/survival`
- `POST /api/tcga/correlation`
- `POST /api/tcga/tumor-normal`
- `POST /api/ora/ora`
- `POST /api/ora/gsea`

## Frontend Principles

- Keep the first screen as the actual research workspace, not a landing page.
- Use compact forms, tables, tabs, and result panels.
- Avoid embedding analysis formulas only in frontend code. The backend owns analysis semantics.
- Frontend route names should map to analysis modules: TCGA and ORA.
- Use a light Read-the-Docs-like workspace: light sidebar, compact panels, visible form labels, and responsive single-column behavior on narrow screens.
- The Analysis picker should align with the left analysis panel. The Result panel should start on the same row on wide screens.
- Result plots should support in-page zoom preview without navigating away.
- Loading states should be contextual per analysis and visually distinct without changing result contracts.

## Extension Rules

When adding a new analysis:

1. Add pure functionality in `packages/bioweb_analysis`.
2. Add Pydantic schemas in `backend/app/schemas`.
3. Add an application service in `backend/app/services`.
4. Add an API route in `backend/app/api/routes`.
5. Add frontend API client and page/component.
6. Add focused tests for the analysis package and route behavior.

## Environment

Use `.venv` at the repository root for Python dependencies.

Important environment variables:

- `BIOWEB_DATABASE_URL`
- `BIOWEB_REDIS_URL`
- `BIOWEB_DATA_DIR`
- `BIOWEB_RESULTS_DIR`
- `BIOWEB_SYNC_ANALYSIS`

## Coding Rules

- Prefer typed, explicit interfaces.
- Keep analysis code independent from web framework concerns.
- Do not commit raw TCGA matrices, generated figures, or local database files.
- Add comments only for non-obvious domain or statistical choices.
- Maintain backward-compatible schemas unless a migration is documented.
