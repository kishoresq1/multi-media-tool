import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_jobs_import_error: ModuleNotFoundError | None = None
try:
    from app.api.jobs import router as jobs_router
except ModuleNotFoundError as exc:
    jobs_router = None
    _jobs_import_error = exc

from app.api.linkedin import router as linkedin_router
from app.api.linkedin_auth import router as linkedin_auth_router
from app.api.routes import router
from app.api.unified import router as unified_router
from app.config.settings import settings
from app.db.database import init_db

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
if _jobs_import_error is not None:
    logging.getLogger(__name__).warning(
        "Background jobs disabled (%s). Use: ./run_api.sh or .venv/bin/uvicorn",
        _jobs_import_error,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Cyber Threat Intelligence Hunter — collects signals from researcher blogs, "
        "vendor advisories, vulnerability databases, and social sources. "
        "Scores, correlates, and returns high-confidence threat findings."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8009",
        "http://127.0.0.1:8009",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
if jobs_router is not None:
    app.include_router(jobs_router, prefix="/api/v1")
app.include_router(unified_router, prefix="/api/v1")
app.include_router(linkedin_router, prefix="/api/v1")
app.include_router(linkedin_auth_router)


@app.get("/")
async def root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
