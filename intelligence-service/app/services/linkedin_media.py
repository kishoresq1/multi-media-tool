"""Upload images and videos to LinkedIn for Posts API."""

from __future__ import annotations

import asyncio
import logging
import time
from io import BytesIO
from urllib.parse import quote

import httpx
from PIL import Image

from app.config.linkedin_settings import linkedin_settings

logger = logging.getLogger(__name__)

LINKEDIN_IMAGES_INIT = "https://api.linkedin.com/rest/images?action=initializeUpload"
LINKEDIN_VIDEOS_INIT = "https://api.linkedin.com/rest/videos?action=initializeUpload"
LINKEDIN_VIDEOS_FINALIZE = "https://api.linkedin.com/rest/videos?action=finalizeUpload"


def linkedin_api_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": linkedin_settings.linkedin_api_version,
    }


def _encode_urn(urn: str) -> str:
    return quote(urn, safe="")


async def _poll_asset_status(
    access_token: str,
    resource: str,
    urn: str,
    *,
    label: str,
    timeout_sec: float,
    interval_sec: float = 2.0,
) -> None:
    """Poll LinkedIn until image/video status is AVAILABLE."""
    headers = linkedin_api_headers(access_token)
    url = f"https://api.linkedin.com/rest/{resource}/{_encode_urn(urn)}"
    deadline = time.monotonic() + timeout_sec

    async with httpx.AsyncClient(timeout=30) as client:
        while time.monotonic() < deadline:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                status = response.json().get("status")
                logger.info("LinkedIn %s %s status=%s", label, urn, status)
                if status == "AVAILABLE":
                    return
                if status == "PROCESSING_FAILED":
                    reason = response.json().get("processingFailureReason", "unknown")
                    raise ValueError(f"LinkedIn {label} processing failed: {reason}")
            else:
                logger.warning(
                    "LinkedIn %s status check %s: %s",
                    label,
                    response.status_code,
                    response.text[:200],
                )
            await asyncio.sleep(interval_sec)

    raise ValueError(f"LinkedIn {label} not ready after {int(timeout_sec)}s — try again shortly")


async def wait_for_image_ready(access_token: str, image_urn: str, *, timeout_sec: float = 90) -> None:
    await _poll_asset_status(
        access_token, "images", image_urn, label="image", timeout_sec=timeout_sec
    )


async def wait_for_video_ready(access_token: str, video_urn: str, *, timeout_sec: float = 180) -> None:
    await _poll_asset_status(
        access_token, "videos", video_urn, label="video", timeout_sec=timeout_sec
    )


def _to_jpeg(image_bytes: bytes) -> bytes:
    """LinkedIn processes JPEG more reliably than PNG for feed image posts."""
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()


async def upload_image(access_token: str, owner_urn: str, image_bytes: bytes) -> str:
    """Register, upload JPEG, return urn:li:image:..."""
    jpeg = _to_jpeg(image_bytes)
    headers = linkedin_api_headers(access_token)
    async with httpx.AsyncClient(timeout=120) as client:
        init = await client.post(
            LINKEDIN_IMAGES_INIT,
            json={"initializeUploadRequest": {"owner": owner_urn}},
            headers=headers,
        )
        if init.status_code != 200:
            raise ValueError(f"LinkedIn image init failed ({init.status_code}): {init.text}")

        value = init.json().get("value", {})
        upload_url = value.get("uploadUrl")
        image_urn = value.get("image")
        if not upload_url or not image_urn:
            raise ValueError("LinkedIn image init missing uploadUrl or image URN")

        put = await client.put(
            upload_url,
            content=jpeg,
            headers={"Content-Type": "image/jpeg"},
            follow_redirects=True,
        )
        if put.status_code not in (200, 201):
            raise ValueError(f"LinkedIn image upload failed ({put.status_code}): {put.text}")

        logger.info("LinkedIn image uploaded %s (%d bytes)", image_urn, len(jpeg))
        await wait_for_image_ready(access_token, image_urn)
        return image_urn


async def upload_video(access_token: str, owner_urn: str, video_bytes: bytes) -> str:
    """Register, upload MP4 (single or multipart), finalize, return urn:li:video:..."""
    headers = linkedin_api_headers(access_token)
    file_size = len(video_bytes)

    async with httpx.AsyncClient(timeout=180) as client:
        init = await client.post(
            LINKEDIN_VIDEOS_INIT,
            json={
                "initializeUploadRequest": {
                    "owner": owner_urn,
                    "fileSizeBytes": file_size,
                    "uploadCaptions": False,
                    "uploadThumbnail": False,
                }
            },
            headers=headers,
        )
        if init.status_code != 200:
            raise ValueError(f"LinkedIn video init failed ({init.status_code}): {init.text}")

        value = init.json().get("value", {})
        video_urn = value.get("video")
        upload_token = value.get("uploadToken", "")
        instructions = value.get("uploadInstructions") or []
        if not video_urn or not instructions:
            raise ValueError("LinkedIn video init missing video URN or upload instructions")

        uploaded_part_ids: list[str] = []
        for part in instructions:
            first = int(part.get("firstByte", 0))
            last = int(part.get("lastByte", file_size - 1))
            chunk = video_bytes[first : last + 1]
            upload_url = part["uploadUrl"]
            put = await client.put(
                upload_url,
                content=chunk,
                headers={"Content-Type": "application/octet-stream"},
                follow_redirects=True,
            )
            if put.status_code not in (200, 201):
                raise ValueError(f"LinkedIn video chunk upload failed ({put.status_code}): {put.text}")
            etag = put.headers.get("etag") or put.headers.get("ETag")
            if not etag:
                raise ValueError(
                    "LinkedIn video upload missing ETag header — cannot finalize upload"
                )
            uploaded_part_ids.append(etag.strip('"'))

        fin = await client.post(
            LINKEDIN_VIDEOS_FINALIZE,
            json={
                "finalizeUploadRequest": {
                    "video": video_urn,
                    "uploadToken": upload_token,
                    "uploadedPartIds": uploaded_part_ids,
                }
            },
            headers=headers,
        )
        if fin.status_code not in (200, 201):
            raise ValueError(f"LinkedIn video finalize failed ({fin.status_code}): {fin.text}")

        logger.info("LinkedIn video finalized %s (%d bytes)", video_urn, file_size)
        await wait_for_video_ready(access_token, video_urn)
        return video_urn
