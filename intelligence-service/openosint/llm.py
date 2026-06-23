# openosint/llm.py
"""
Multi-provider LLM utility for SQ1 OSINT.

Auto-detects which AI provider is configured and returns a unified callable.
Priority order: Anthropic → OpenAI → OpenRouter → Gemini.
Only one provider's key needs to be set.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_PROVIDER_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

_PRIORITY = ["anthropic", "openai", "openrouter", "gemini"]

_ERROR_TEMPLATE = (
    '{{"verdict": "ERROR", "confidence": 0.0, '
    '"reasoning": "{msg}", "red_flags": [], '
    '"recommended_action": "FLAG_FOR_REVIEW"}}'
)


def detect_provider() -> str | None:
    """Return the first provider whose API key is set in env, or None."""
    for provider in _PRIORITY:
        if os.environ.get(_PROVIDER_ENV[provider], "").strip():
            return provider
    return None


async def llm_complete(
    *,
    system: str,
    user: str,
    max_tokens: int = 512,
    provider: str | None = None,
) -> str:
    """
    Send a single-turn prompt to whichever LLM provider is configured.

    Parameters
    ----------
    system:
        System prompt string.
    user:
        User message string.
    max_tokens:
        Maximum tokens in the response.
    provider:
        Force a specific provider. If None, auto-detects from env.

    Returns
    -------
    str
        Raw text response from the model.

    Raises
    ------
    RuntimeError
        If no provider key is configured or the API call fails.
    """
    resolved = provider or detect_provider()
    if resolved is None:
        raise RuntimeError(
            "No AI provider API key found. Set one of: "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY."
        )

    logger.debug("llm_complete using provider: %s", resolved)

    if resolved == "anthropic":
        return await _call_anthropic(system=system, user=user, max_tokens=max_tokens)
    if resolved in ("openai", "openrouter"):
        return await _call_openai_compat(
            system=system, user=user, max_tokens=max_tokens, provider=resolved
        )
    if resolved == "gemini":
        return await _call_gemini(system=system, user=user, max_tokens=max_tokens)

    raise RuntimeError(f"Unknown provider: {resolved!r}")


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


async def _call_anthropic(*, system: str, user: str, max_tokens: int) -> str:
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic library not installed: pip install anthropic") from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")

    import asyncio

    client = anthropic.Anthropic(api_key=api_key)
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


async def _call_openai_compat(
    *, system: str, user: str, max_tokens: int, provider: str
) -> str:
    try:
        import openai
    except ImportError as exc:
        raise RuntimeError("openai library not installed: pip install openai") from exc

    if provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        base_url = "https://openrouter.ai/api/v1"
        model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        extra_headers: dict[str, str] = {
            "HTTP-Referer": "https://github.com/LakshmanS27/SQ1INT",
            "X-Title": "SQ1 OSINT",
        }
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        extra_headers = {}

    client = openai.AsyncOpenAI(base_url=base_url, api_key=api_key, default_headers=extra_headers)
    response = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


async def _call_gemini(*, system: str, user: str, max_tokens: int) -> str:
    try:
        import google.generativeai as genai  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai library not installed: pip install google-generativeai"
        ) from exc

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    import asyncio

    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system,
        generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),
    )
    response = await asyncio.to_thread(model.generate_content, user)
    return response.text
