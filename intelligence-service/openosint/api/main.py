# openosint/api/main.py
"""
SQ1 OSINT FastAPI application.

Starts on port 8000. Provides REST endpoints for the React dashboard
and Person 2's marketing module integration.

Run:
    uvicorn openosint.api.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import logging

from openosint.config import load_project_env

load_project_env()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openosint.api.routes import companies, customer_intelligence, employees, intel, tracker

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SQ1 OSINT API",
    version="1.0.0",
    description="Cybersecurity threat intelligence platform REST API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intel.router, prefix="/api/intel", tags=["intel"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(employees.router, prefix="/api/employees", tags=["employees"])
app.include_router(tracker.router, prefix="/api/tracker", tags=["tracker"])
app.include_router(
    customer_intelligence.router,
    prefix="/api/customer-intelligence",
    tags=["customer-intelligence"],
)


@app.on_event("startup")
async def startup_event() -> None:
    from openosint.data.seed import seed
    from openosint.watcher.web_watcher import start_watcher

    seed()
    asyncio.create_task(start_watcher())
    logger.info("SQ1 OSINT API started.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    from openosint.watcher.web_watcher import stop_watcher

    stop_watcher()


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": "sq1-osint", "version": "1.0.0"}
