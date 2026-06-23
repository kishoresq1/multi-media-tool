"""Generate MP4 videos from unified intel — same full card as the image post."""

from __future__ import annotations

import logging
from io import BytesIO

import imageio.v3 as iio
import numpy as np
from PIL import Image

from app.db.models import UnifiedIntel
from app.services.intel_card_renderer import render_intel_card

logger = logging.getLogger(__name__)

FPS = 12
DURATION_SECONDS = 10


def _ken_burns_frames(png: bytes) -> list[np.ndarray]:
    """Slow zoom on the full intel card — same visual as the image post."""
    base = Image.open(BytesIO(png)).convert("RGB")
    w, h = base.size
    total = FPS * DURATION_SECONDS
    frames: list[np.ndarray] = []

    for i in range(total):
        # Gentle zoom 100% → 108% over the clip
        scale = 1.0 + (i / max(total - 1, 1)) * 0.08
        nw, nh = max(w, int(w * scale)), max(h, int(h * scale))
        zoomed = base.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - w) // 2
        top = (nh - h) // 2
        cropped = zoomed.crop((left, top, left + w, top + h))
        frames.append(np.asarray(cropped))

    return frames


def render_intel_video(item: UnifiedIntel) -> bytes:
    """
    Build MP4 from the exact same full card PNG used for image posts.
    LinkedIn feed video matches the image card layout (title, badges, summary, etc.).
    """
    png = render_intel_card(item, slide="full")
    frames = _ken_burns_frames(png)
    if not frames:
        raise ValueError("No video frames generated")

    buf = BytesIO()
    try:
        iio.imwrite(buf, frames, extension=".mp4", fps=FPS, codec="libx264", quality=8)
    except Exception as exc:
        logger.exception("MP4 encode failed")
        raise ValueError(
            "Video encoding failed. Install imageio-ffmpeg: pip install imageio-ffmpeg"
        ) from exc

    data = buf.getvalue()
    if len(data) < 10_000:
        raise ValueError("Generated video is too small — encoding may have failed")
    return data
