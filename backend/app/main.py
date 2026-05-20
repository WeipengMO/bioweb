from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import enrichment, health, jobs, tcga
from backend.app.core.config import settings
from backend.app.services.result_cleanup import cleanup_old_result_images


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_old_result_images()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(tcga.router, prefix="/api/tcga", tags=["tcga"])
    app.include_router(enrichment.router, prefix="/api/ora", tags=["ora"])
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/results", StaticFiles(directory=settings.results_dir), name="results")
    return app


app = create_app()
