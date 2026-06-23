"""Unified intel API — one table from all sources + Ollama + SAINT score."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.database import get_session
from app.db.unified_repository import UnifiedIntelRepository
from app.models.schemas import (
    UnifiedIntelResponse,
    UnifiedListResponse,
    UnifiedRunRequest,
    UnifiedRunResponse,
)
from app.services.unified.ollama_client import OllamaClient
from app.services.unified_intel_service import UnifiedIntelService, unified_to_response

router = APIRouter(prefix="/unified", tags=["Unified Intelligence"])
unified_service = UnifiedIntelService()


@router.get("/status")
async def unified_status() -> dict:
    """Check Ollama connectivity and unified table config."""
    ollama = OllamaClient()
    return {
        "ollama_enabled": settings.ollama_enabled,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
        "ollama_available": await ollama.is_available(),
        "table": "unified_intel",
        "classification_values": ["PRODUCT_VULNERABILITY", "COMPANY_BREACH", "UNKNOWN"],
    }


@router.post("/run", response_model=UnifiedRunResponse)
async def run_unified_pipeline(
    request: UnifiedRunRequest,
    session: AsyncSession = Depends(get_session),
) -> UnifiedRunResponse:
    """
    Full unified pipeline:

    1. Run all collection APIs (social, advisories, blogs, vulnerabilities, compliance)
    2. Load all intel tables and group by vendor/product/version/CVE
    3. Ollama LLM extracts vendor_name, product_name, version_name, summary
    4. SAINT threat + compliance scoring → confidence_score in unified_intel
    5. SAINT classifier sets `classification` (PRODUCT_VULNERABILITY | COMPANY_BREACH | UNKNOWN)
    """
    try:
        return await unified_service.run_pipeline(session, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=UnifiedListResponse)
async def list_unified_intel(
    vendor: str | None = Query(default=None),
    product: str | None = Query(default=None),
    min_score: float = Query(default=30, ge=0, le=100),
    classification: str | None = Query(
        default=None,
        description="Filter by classification (null = unclassified)",
    ),
    unclassified_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> UnifiedListResponse:
    """List consolidated unified_intel rows, latest date first."""
    repo = UnifiedIntelRepository(session)

    rows = await repo.list_items(
        vendor=vendor,
        product=product,
        min_score=min_score,
        classification=classification,
        unclassified_only=unclassified_only,
        limit=limit,
        offset=offset,
    )

    total = await repo.count(
        vendor=vendor,
        min_score=min_score,
        classification=classification,
        unclassified_only=unclassified_only,
    )

    return UnifiedListResponse(
        total=total,
        items=[unified_to_response(r) for r in rows],
    )


@router.get("/{item_id}", response_model=UnifiedIntelResponse)
async def get_unified_intel(
    item_id: str,
    session: AsyncSession = Depends(get_session),
) -> UnifiedIntelResponse:
    repo = UnifiedIntelRepository(session)
    row = await repo.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Unified intel record not found")
    return unified_to_response(row)
