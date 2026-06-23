from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.linkedin_settings import linkedin_settings
from app.db.database import get_session
from app.db.linkedin_repository import LinkedInTokenRepository
from app.db.unified_repository import UnifiedIntelRepository
from app.services.intel_card_renderer import render_intel_card
from app.services.intel_video_renderer import render_intel_video
from app.services.linkedin_post import LinkedInPostService

router = APIRouter(prefix="/linkedin", tags=["LinkedIn"])


class LinkedInPostRequest(BaseModel):
    unified_id: str = Field(..., min_length=1)
    human_verified: bool = Field(
        default=False,
        description="Must be true — confirms user reviewed content before posting",
    )
    commentary: str | None = Field(
        default=None,
        max_length=3000,
        description="Optional post text from detail panel preview; server validates length",
    )
    media_type: str = Field(
        default="text",
        description="text | image | video — image/video generated from unified intel detail",
    )


@router.get("/status")
async def linkedin_status(session: AsyncSession = Depends(get_session)) -> dict:
    """LinkedIn connection status for personal profile posting."""
    configured = bool(
        linkedin_settings.linkedin_client_id and linkedin_settings.linkedin_client_secret
    )
    row = await LinkedInTokenRepository(session).get_active()
    parsed = urlparse(linkedin_settings.linkedin_redirect_uri)
    login_base = f"{parsed.scheme}://{parsed.netloc}"
    return {
        "configured": configured,
        "connected": row is not None,
        "display_name": row.display_name if row else None,
        "member_urn": row.member_urn if row else None,
        "post_mode": linkedin_settings.linkedin_post_mode,
        "scopes": linkedin_settings.linkedin_scopes,
        "login_url": f"{login_base}/auth/linkedin/login" if configured else None,
    }


@router.get("/preview/{unified_id}")
async def linkedin_preview_unified(
    unified_id: str,
    media_type: str = "text",
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        return await LinkedInPostService(session).preview_unified_post(
            unified_id, media_type=media_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/post")
async def linkedin_post_unified(
    request: LinkedInPostRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not request.human_verified:
        raise HTTPException(
            status_code=400,
            detail="human_verified must be true — review the post preview before confirming",
        )
    try:
        media = request.media_type.lower().strip()
        if media not in {"text", "image", "video"}:
            raise HTTPException(status_code=400, detail="media_type must be text, image, or video")
        return await LinkedInPostService(session).post_unified_intel(
            request.unified_id,
            commentary_override=request.commentary,
            media_type=media,
        )
    except Exception as exc:
        msg = str(exc)
        if "not connected" in msg.lower():
            raise HTTPException(status_code=401, detail=msg) from exc
        if isinstance(exc, ValueError):
            raise HTTPException(status_code=400, detail=msg) from exc
        raise HTTPException(status_code=500, detail=msg) from exc


@router.get("/media/{unified_id}/image")
async def linkedin_media_image(
    unified_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Preview/download PNG card generated from unified intel detail."""
    row = await UnifiedIntelRepository(session).get(unified_id)
    if not row:
        raise HTTPException(status_code=404, detail="Unified intel record not found")
    return Response(content=render_intel_card(row), media_type="image/png")


@router.get("/media/{unified_id}/video")
async def linkedin_media_video(
    unified_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Preview/download MP4 slideshow generated from unified intel detail."""
    row = await UnifiedIntelRepository(session).get(unified_id)
    if not row:
        raise HTTPException(status_code=404, detail="Unified intel record not found")
    try:
        return Response(content=render_intel_video(row), media_type="video/mp4")
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/disconnect")
async def linkedin_disconnect(session: AsyncSession = Depends(get_session)) -> dict:
    await LinkedInTokenRepository(session).delete_all()
    return {"status": "disconnected"}
