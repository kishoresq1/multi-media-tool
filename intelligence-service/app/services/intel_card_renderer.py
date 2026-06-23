"""Generate shareable PNG cards from unified intel records."""

from __future__ import annotations

import json
import textwrap
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.db.models import UnifiedIntel

# Divisible by 16 for H.264 video encoding
WIDTH = 1088
HEIGHT = 1360

COLORS = {
    "bg": (15, 23, 42),      # Professional dark slate
    "accent": (56, 189, 248),  # Sky blue accent
    "white": (248, 250, 252),  # Off-white
    "muted": (148, 163, 184),  # Slate muted text
    "danger": (244, 63, 94),   # Rose 500
    "warning": (251, 191, 36),  # Amber 400
    "success": (34, 197, 94),   # Green 500
}


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _risk_color(level: str) -> tuple[int, int, int]:
    level = (level or "").upper()
    if level in {"HIGH", "CRITICAL"}:
        return COLORS["danger"]
    if level in {"MEDIUM", "MODERATE"}:
        return COLORS["warning"]
    return COLORS["success"]


def _classification_label(value: str | None) -> str:
    if not value:
        return "Unclassified"
    return value.replace("_", " ").title()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:12]


def render_intel_card(item: UnifiedIntel, *, slide: str = "full") -> bytes:
    """
    Render PNG card. slide: full | title | summary | metrics
    Used for static image (full) or video frames.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    title_font = _load_font(46, bold=True)
    body_font = _load_font(28)
    small_font = _load_font(24)
    label_font = _load_font(22, bold=True)
    brand_font = _load_font(30, bold=True)

    margin = 64
    y = 72

    draw.text((margin, y), "ZERO DAY RADAR", font=brand_font, fill=COLORS["accent"])
    y += 56

    cls = _classification_label(item.classification)
    risk = item.risk_level or "LOW"
    draw.rounded_rectangle(
        (margin, y, margin + 340, y + 44),
        radius=22,
        fill=COLORS["danger"] if "breach" in cls.lower() else COLORS["accent"],
    )
    draw.text((margin + 16, y + 8), cls.upper(), font=label_font, fill=COLORS["white"])
    risk_bg = _risk_color(risk)
    draw.rounded_rectangle(
        (margin + 360, y, margin + 520, y + 44),
        radius=22,
        fill=risk_bg,
    )
    # White text for danger/success, dark for warning
    risk_text_fill = (20, 20, 30) if risk.upper() in {"MEDIUM", "MODERATE"} else COLORS["white"]
    draw.text((margin + 376, y + 8), f"RISK {risk}", font=label_font, fill=risk_text_fill)
    y += 72

    title = (item.title or "Security alert").strip()
    for line in _wrap(draw, title, title_font, WIDTH - margin * 2):
        draw.text((margin, y), line, font=title_font, fill=COLORS["white"])
        y += 54

    if slide in {"full", "title", "metrics"}:
        vendor = item.vendor_name or item.company_name or "—"
        y += 16
        draw.text((margin, y), f"Vendor: {vendor}", font=body_font, fill=COLORS["muted"])
        y += 40

    if slide in {"full", "metrics"}:
        metrics = (
            f"SAINT {int(item.confidence_score)}/100  ·  Threat {item.threat_score:.0f}  ·  "
            f"Compliance {item.compliance_score:.0f}  ·  Confidence {item.classification_confidence:.0f}%"
        )
        for line in textwrap.wrap(metrics, width=42):
            draw.text((margin, y), line, font=small_font, fill=COLORS["white"])
            y += 34

    if slide in {"full", "summary"}:
        body = (item.llm_summary or item.summary or item.score_reason or "").strip()
        body = body.replace("<p>", "").replace("</p>", "").replace("&nbsp;", " ")
        if len(body) > 420:
            body = body[:417] + "…"
        if body:
            y += 24
            draw.text((margin, y), "Summary", font=label_font, fill=COLORS["accent"])
            y += 36
            for line in _wrap(draw, body, body_font, WIDTH - margin * 2):
                draw.text((margin, y), line, font=body_font, fill=COLORS["muted"])
                y += 36

    if slide in {"full", "metrics"} and item.classification_reason:
        y += 20
        for line in _wrap(draw, item.classification_reason, small_font, WIDTH - margin * 2):
            draw.text((margin, y), line, font=small_font, fill=COLORS["muted"])
            y += 30

    try:
        cves = json.loads(item.cves or "[]")
        if cves and slide in {"full", "metrics"}:
            y += 12
            draw.text((margin, y), "CVEs: " + ", ".join(cves[:4]), font=small_font, fill=COLORS["white"])
    except json.JSONDecodeError:
        pass

    draw.text(
        (margin, HEIGHT - 80),
        "#CyberSecurity  #ThreatIntel  #ZeroDayRadar",
        font=small_font,
        fill=COLORS["accent"],
    )

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
