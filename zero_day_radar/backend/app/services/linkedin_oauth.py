import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config.linkedin_settings import linkedin_settings

logger = logging.getLogger(__name__)

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"


def _sign_state(nonce: str, ts: str) -> str:
    payload = f"{nonce}:{ts}".encode()
    key = linkedin_settings.session_secret.encode()
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def create_oauth_state() -> str:
    nonce = secrets.token_urlsafe(16)
    ts = str(int(time.time()))
    sig = _sign_state(nonce, ts)
    return f"{nonce}:{ts}:{sig}"


def verify_oauth_state(state: str, max_age_seconds: int = 600) -> bool:
    try:
        nonce, ts, sig = state.split(":", 2)
        if not hmac.compare_digest(_sign_state(nonce, ts), sig):
            return False
        age = int(time.time()) - int(ts)
        return 0 <= age <= max_age_seconds
    except (ValueError, TypeError):
        return False


def build_authorization_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": linkedin_settings.linkedin_client_id,
        "redirect_uri": linkedin_settings.linkedin_redirect_uri,
        "state": state,
        "scope": linkedin_settings.linkedin_scopes,
    }
    return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": linkedin_settings.linkedin_redirect_uri,
                "client_id": linkedin_settings.linkedin_client_id,
                "client_secret": linkedin_settings.linkedin_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": linkedin_settings.linkedin_client_id,
                "client_secret": linkedin_settings.linkedin_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def fetch_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


def token_expires_at(expires_in: int | None) -> datetime | None:
    if not expires_in:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))


def member_urn_from_sub(sub: str) -> str:
    if sub.startswith("urn:li:person:"):
        return sub
    return f"urn:li:person:{sub}"
