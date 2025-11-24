"""SEO data provider for search volume, keyword difficulty and trends."""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class SEODataProvider:
    """Fetch SEO keyword metrics from an external API with graceful fallbacks.

    The provider is intentionally thin; it expects two environment variables to
    be present when making real API calls:

    * ``SEO_API_BASE_URL`` – a URL that accepts ``keyword`` as a query
      parameter and returns JSON.
    * ``SEO_API_KEY`` – an API token used for bearer authentication.

    If either value is missing or the request fails, deterministic fallback
    metrics are generated so the rest of the pipeline can continue to operate
    during local development and testing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 10,
    ) -> None:
        self.api_key = api_key or os.getenv("SEO_API_KEY")
        self.base_url = base_url or os.getenv("SEO_API_BASE_URL")
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_metrics(self, keyword: str) -> Dict[str, Any]:
        """Return SEO metrics for a keyword.

        Parameters
        ----------
        keyword: str
            The keyword or idea title to evaluate.

        Returns
        -------
        Dict[str, Any]
            A mapping that always includes ``search_volume``,
            ``keyword_difficulty``, ``trend_direction`` and ``source`` keys.
        """

        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            return self._fallback_metrics("", reason="missing-keyword")

        if not self.api_key or not self.base_url:
            return self._fallback_metrics(cleaned_keyword, reason="missing-configuration")

        try:
            response = self.session.get(
                self.base_url,
                params={"keyword": cleaned_keyword},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            parsed = self._parse_payload(response.json())
            if parsed:
                parsed.setdefault("source", "api")
                return parsed
        except Exception as exc:  # noqa: BLE001
            logger.warning("SEO API lookup failed for '%s': %s", cleaned_keyword, exc)

        return self._fallback_metrics(cleaned_keyword, reason="api-fallback")

    def _parse_payload(self, payload: Any) -> Optional[Dict[str, Any]]:
        """Extract metrics from API responses with flexible structure."""

        def _extract(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            sv = obj.get("search_volume") or obj.get("searchVolume")
            kd = obj.get("keyword_difficulty") or obj.get("keywordDifficulty") or obj.get("difficulty")
            trend = obj.get("trend_direction") or obj.get("trendDirection") or obj.get("trend")
            if sv is not None and kd is not None and trend is not None:
                return {
                    "search_volume": sv,
                    "keyword_difficulty": kd,
                    "trend_direction": trend,
                }
            return None

        if isinstance(payload, dict):
            direct = _extract(payload)
            if direct:
                return direct
            for key in ("data", "result", "results"):
                nested = payload.get(key)
                if isinstance(nested, list) and nested:
                    candidate = _extract(nested[0])
                    if candidate:
                        return candidate
                if isinstance(nested, dict):
                    candidate = _extract(nested)
                    if candidate:
                        return candidate
        return None

    def _fallback_metrics(self, keyword: str, reason: str) -> Dict[str, Any]:
        """Generate deterministic placeholder metrics when real data is unavailable."""

        # Use a hash to keep numbers stable for the same keyword
        digest = hashlib.sha256(keyword.encode("utf-8")).hexdigest() or "0"
        seed = int(digest[:8], 16)
        search_volume = 100 + (seed % 900)
        keyword_difficulty = round(10 + (seed % 70) * 0.9, 1)
        trend_direction = ["upward", "flat", "downward"][seed % 3]
        return {
            "search_volume": search_volume,
            "keyword_difficulty": keyword_difficulty,
            "trend_direction": trend_direction,
            "source": reason,
        }
