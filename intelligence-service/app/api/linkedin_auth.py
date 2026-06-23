import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.linkedin_settings import linkedin_settings
from app.db.database import get_session
from app.db.linkedin_repository import LinkedInTokenRepository
from app.services.linkedin_oauth import (
    build_authorization_url,
    create_oauth_state,
    exchange_code_for_tokens,
    fetch_userinfo,
    member_urn_from_sub,
    token_expires_at,
    verify_oauth_state,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/linkedin", tags=["LinkedIn Auth"])


@router.get("/login")
async def linkedin_login() -> RedirectResponse:
    """Start Sign In with LinkedIn (OpenID Connect) for personal profile posting."""
    if not linkedin_settings.linkedin_client_id or not linkedin_settings.linkedin_client_secret:
        raise HTTPException(status_code=503, detail="LinkedIn OAuth is not configured")
    state = create_oauth_state()
    return RedirectResponse(build_authorization_url(state))


@router.get("/callback")
async def linkedin_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    frontend = linkedin_settings.frontend_url.rstrip("/")
    if error:
        params = urlencode({"linkedin": "error", "message": error_description or error})
        return RedirectResponse(f"{frontend}/unified?{params}")

    if not code or not state or not verify_oauth_state(state):
        params = urlencode({"linkedin": "error", "message": "Invalid OAuth state"})
        return RedirectResponse(f"{frontend}/unified?{params}")

    try:
        token_data = await exchange_code_for_tokens(code)
        access_token = token_data["access_token"]
        userinfo = await fetch_userinfo(access_token)
        sub = userinfo.get("sub", "")
        name = userinfo.get("name") or userinfo.get("given_name") or "LinkedIn member"

        repo = LinkedInTokenRepository(session)
        await repo.upsert(
            member_sub=sub,
            member_urn=member_urn_from_sub(sub),
            display_name=name,
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            expires_at=token_expires_at(token_data.get("expires_in")),
            scopes=linkedin_settings.linkedin_scopes,
        )
        params = urlencode({"linkedin": "connected", "name": name})
        return RedirectResponse(f"{frontend}/unified?{params}")
    except Exception as exc:
        logger.exception("LinkedIn OAuth callback failed")
        params = urlencode({"linkedin": "error", "message": str(exc)})
        return RedirectResponse(f"{frontend}/unified?{params}")
