# openosint/tools/detect_misinfo.py
"""
Misinformation detection module.

Uses the configured AI provider (Anthropic, OpenAI, OpenRouter, or Gemini)
to identify fake or misleading cybersecurity news.
Returns a JSON verdict string; never raises on failure.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a cybersecurity fact-checker for SQ1 OSINT.
Analyze the provided claim or article and determine if it contains misinformation.

Return ONLY a JSON object (no markdown, no code fences):
{
  "verdict": "LEGITIMATE | MISINFORMATION | UNVERIFIED",
  "confidence": 0.0,
  "reasoning": "2-3 sentence explanation",
  "red_flags": ["list", "of", "suspicious", "elements"],
  "recommended_action": "SURFACE | SUPPRESS | FLAG_FOR_REVIEW"
}"""

_ERROR_TEMPLATE = '{{"verdict": "ERROR", "confidence": 0.0, "reasoning": "{msg}", "red_flags": [], "recommended_action": "FLAG_FOR_REVIEW"}}'


async def run_detect_misinfo_osint(content: str, source_url: str = "") -> str:
    """
    Use an AI provider to detect if cybersecurity content is misinformation.

    Automatically selects whichever provider key is configured in env.
    Priority: ANTHROPIC_API_KEY → OPENAI_API_KEY → OPENROUTER_API_KEY → GEMINI_API_KEY.

    Parameters
    ----------
    content:
        The article text or claim to analyse.
    source_url:
        Optional URL where the content was found.

    Returns
    -------
    str
        JSON-encoded verdict object or a JSON error envelope on failure.
    """
    from openosint.llm import detect_provider, llm_complete

    logger.info("Running misinfo detection on content from: %s", source_url or "<no url>")

    provider = detect_provider()
    if provider is None:
        return _ERROR_TEMPLATE.format(
            msg="No AI provider key found. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY."
        )

    user_message = (
        f"Analyze this cybersecurity claim for misinformation:\n\n"
        f"Source: {source_url or 'Not provided'}\n"
        f"Content: {content[:2000]}\n\n"
        "Respond with the JSON schema only."
    )

    try:
        raw = await llm_complete(
            system=_SYSTEM_PROMPT,
            user=user_message,
            max_tokens=512,
            provider=provider,
        )
        raw = raw.strip()
        # Strip markdown fences if the model added them despite instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        # Validate it's parseable JSON before returning
        json.loads(raw)
        logger.info("Misinfo detection complete via %s.", provider)
        return raw
    except json.JSONDecodeError as exc:
        logger.warning("Non-JSON response from %s: %s", provider, exc)
        return _ERROR_TEMPLATE.format(msg=f"Non-JSON response from {provider}: {exc}")
    except Exception as exc:
        logger.exception("Unexpected error during misinfo detection.")
        safe = str(exc).replace('"', "'")
        return _ERROR_TEMPLATE.format(msg=safe)
