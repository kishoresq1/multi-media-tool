import asyncio
import json
import logging
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.linkedin_settings import linkedin_settings
from app.db.linkedin_repository import LinkedInTokenRepository
from app.db.models import UnifiedIntel
from app.db.unified_repository import UnifiedIntelRepository
from app.services.intel_card_renderer import render_intel_card
from app.services.intel_video_renderer import render_intel_video
from app.services.linkedin_media import linkedin_api_headers, upload_image, upload_video
from app.services.linkedin_oauth import member_urn_from_sub, refresh_access_token, token_expires_at

logger = logging.getLogger(__name__)

LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"

# Characters that must be escaped for LinkedIn "little text" commentary format
_LINKEDIN_RESERVED = "\\|{}@[]()<>#*_~"


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def escape_linkedin_commentary(text: str) -> str:
    """Escape reserved chars so LinkedIn Posts API accepts full commentary."""
    out: list[str] = []
    for ch in text:
        if ch in _LINKEDIN_RESERVED:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _classification_label(value: str | None) -> str:
    if not value:
        return "Unclassified"
    return value.replace("_", " ").title()


def build_unified_post_text(item: UnifiedIntel, *, include_hashtags: bool = True) -> str:
    """Format unified intel detail fields as a LinkedIn post (max 3000 chars)."""
    parts: list[str] = [item.title.strip()]

    body = (item.llm_summary or item.summary or "").strip()
    if body:
        parts.extend(["", body[:1400]])

    parts.append("—")

    meta: list[str] = []
    if item.classification:
        meta.append(f"Type: {_classification_label(item.classification)}")
    if item.vendor_name:
        meta.append(f"Vendor: {item.vendor_name}")
    if item.product_name:
        meta.append(f"Product: {item.product_name}")
    if item.company_name:
        meta.append(f"Company: {item.company_name}")
    if item.version_name:
        meta.append(f"Version: {item.version_name}")
    if item.risk_level:
        meta.append(f"Risk: {item.risk_level}")
    meta.append(f"SAINT score: {int(item.confidence_score)}/100")
    meta.append(f"Threat: {item.threat_score:.1f}")
    meta.append(f"Compliance: {item.compliance_score:.1f}")
    if item.classification_confidence:
        meta.append(f"Classification confidence: {int(item.classification_confidence)}%")
    if item.source_count:
        meta.append(f"Sources: {item.source_count}")
    if item.latest_date:
        meta.append(f"Date: {item.latest_date.strftime('%b %d, %Y')}")

    parts.append(" · ".join(meta))

    if item.classification_reason:
        parts.extend(["", item.classification_reason])
    if item.score_reason:
        parts.extend(["", item.score_reason])

    try:
        cves = json.loads(item.cves or "[]")
        if cves:
            parts.extend(["", "CVEs: " + ", ".join(cves[:8])])
    except json.JSONDecodeError:
        pass

    try:
        frameworks = json.loads(item.frameworks or "[]")
        if frameworks:
            parts.extend(["", "Frameworks: " + ", ".join(frameworks[:6])])
    except json.JSONDecodeError:
        pass

    if include_hashtags:
        parts.extend(["", "#CyberSecurity #ThreatIntel #ZeroDayRadar"])
    return "\n".join(parts)[:3000]


def prepare_commentary_for_linkedin(text: str, *, include_hashtags: bool = True) -> str:
    """Escape commentary for LinkedIn little-text; hashtag templates must not be escaped."""
    body = text.strip()
    if not include_hashtags:
        body = re.sub(r"\n\s*#\w+(?:\s+#\w+)*\s*$", "", body).strip()

    pieces: list[str] = []
    pos = 0
    for match in re.finditer(r"#(\w+)", body):
        pieces.append(escape_linkedin_commentary(body[pos : match.start()]))
        if include_hashtags:
            pieces.append("{hashtag|\\#|" + match.group(1) + "}")
        pos = match.end()
    pieces.append(escape_linkedin_commentary(body[pos:]))
    return "".join(pieces)[:3000]


class LinkedInPostService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tokens = LinkedInTokenRepository(session)
        self.unified = UnifiedIntelRepository(session)

    async def get_valid_access_token(self) -> tuple[str, str]:
        row = await self.tokens.get_active()
        if not row:
            raise ValueError("LinkedIn not connected. Sign in from Unified Intelligence page.")

        access_token = row.access_token
        expires_at = _as_utc(row.expires_at)
        if expires_at and expires_at <= datetime.now(timezone.utc) and row.refresh_token:
            refreshed = await refresh_access_token(row.refresh_token)
            access_token = refreshed["access_token"]
            await self.tokens.upsert(
                member_sub=row.member_sub,
                member_urn=row.member_urn,
                display_name=row.display_name,
                access_token=access_token,
                refresh_token=refreshed.get("refresh_token", row.refresh_token),
                expires_at=token_expires_at(refreshed.get("expires_in")),
                scopes=row.scopes,
            )
        return access_token, row.member_urn

    async def preview_unified_post(self, unified_id: str, *, media_type: str = "text") -> dict:
        row = await self.unified.get(unified_id)
        if not row:
            raise ValueError("Unified intel record not found")
        include_hashtags = (media_type or "text").lower().strip() == "text"
        commentary = build_unified_post_text(row, include_hashtags=include_hashtags)
        return {
            "unified_id": unified_id,
            "title": row.title,
            "commentary": commentary,
            "char_count": len(commentary),
        }

    async def post_unified_intel(
        self,
        unified_id: str,
        commentary_override: str | None = None,
        media_type: str = "text",
    ) -> dict:
        row = await self.unified.get(unified_id)
        if not row:
            raise ValueError("Unified intel record not found")

        media_type = (media_type or "text").lower().strip()
        if media_type not in {"text", "image", "video"}:
            media_type = "text"

        include_hashtags = media_type == "text"
        raw = (commentary_override or "").strip() or build_unified_post_text(
            row, include_hashtags=include_hashtags
        )
        if len(raw) > 3000:
            raise ValueError("Post text exceeds LinkedIn 3000 character limit")
        commentary = prepare_commentary_for_linkedin(raw, include_hashtags=include_hashtags)
        access_token, member_urn = await self.get_valid_access_token()
        author = member_urn

        if linkedin_settings.linkedin_post_mode == "organization" and linkedin_settings.linkedin_organization_id:
            author = f"urn:li:organization:{linkedin_settings.linkedin_organization_id}"

        media_urn: str | None = None
        if media_type == "image":
            logger.info("Generating image for unified %s: %s", unified_id, row.title[:80])
            png = render_intel_card(row, slide="full")
            media_urn = await upload_image(access_token, author, png)
        elif media_type == "video":
            logger.info("Generating video for unified %s: %s", unified_id, row.title[:80])
            mp4 = render_intel_video(row)
            media_urn = await upload_video(access_token, author, mp4)

        payload: dict = {
            "author": author,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if media_urn:
            if media_type == "image":
                payload["content"] = {
                    "media": {
                        "id": media_urn,
                        "altText": row.title[:300],
                    }
                }
            else:
                payload["content"] = {
                    "media": {
                        "id": media_urn,
                    }
                }

        headers = linkedin_api_headers(access_token)

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(LINKEDIN_POSTS_URL, json=payload, headers=headers)

        if response.status_code not in (200, 201):
            detail = response.text
            logger.error("LinkedIn post failed %s: %s", response.status_code, detail)
            if response.status_code == 422 and "DUPLICATE_POST" in detail:
                raise ValueError(
                    "This content was already posted to your LinkedIn feed recently. "
                    "Edit the text or wait before posting again."
                )
            raise ValueError(f"LinkedIn API error ({response.status_code}): {detail}")

        post_id = response.headers.get("x-restli-id") or response.headers.get("X-RestLi-Id")
        return {
            "status": "posted",
            "linkedin_post_id": post_id,
            "unified_id": unified_id,
            "author": author,
            "media_type": media_type,
            "media_urn": media_urn,
            "commentary_preview": commentary[:200] + ("…" if len(commentary) > 200 else ""),
        }
