"""Ollama LLM client for unified intel enrichment."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)

ENRICHMENT_PROMPT = """You are a cyber threat and compliance intelligence analyst.
Given grouped intelligence records, extract structured metadata.

Return ONLY valid JSON with these fields:
{{
  "vendor_name": "string",
  "product_name": "string",
  "version_name": "string or null",
  "summary": "2-3 sentence summary of the finding",
  "primary_cve": "CVE-YYYY-NNNN or null"
}}

Records:
{records}
"""


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    async def is_available(self) -> bool:
        if not settings.ollama_enabled:
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def enrich_cluster(
        self,
        vendor_hint: str,
        product_hint: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not settings.ollama_enabled:
            return None

        records_text = json.dumps(records[:8], indent=2, default=str)[:6000]
        prompt = ENRICHMENT_PROMPT.format(records=records_text)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                resp.raise_for_status()
                body = resp.json()
                raw = body.get("response", "")
                parsed = json.loads(raw)
                return {
                    "vendor_name": parsed.get("vendor_name") or vendor_hint,
                    "product_name": parsed.get("product_name") or product_hint,
                    "version_name": parsed.get("version_name"),
                    "summary": parsed.get("summary", ""),
                    "primary_cve": parsed.get("primary_cve"),
                    "llm_model": self.model,
                }
        except Exception as exc:
            logger.warning("Ollama enrichment failed: %s", exc)
            return None
