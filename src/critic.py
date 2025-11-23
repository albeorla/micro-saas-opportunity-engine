import json
from pathlib import Path
from typing import Dict, Optional, Any
import datetime
from urllib.parse import urlparse

class Critic:
    """Evaluate ideas based on source credibility, recency, and novelty.

    This enhanced critic uses a configuration file to check domain authority
    and penalize generic ideas. It also parses dates to penalize stale content.
    """

    def __init__(self, config_path: Optional[str] = None, current_year: Optional[int] = None) -> None:
        self.current_year = current_year or datetime.datetime.now().year
        self.config = self._load_config(config_path)
        self.trusted_domains = set(self.config.get("trusted_domains", []))
        self.blocked_domains = set(self.config.get("blocked_domains", []))
        self.novelty_keywords = set(self.config.get("novelty_keywords", []))
        self.penalties = self.config.get("penalties", {"blocked_domain": -20, "novelty": -10, "stale": -5})
        self.bonuses = self.config.get("bonuses", {"trusted_domain": 5, "recent": 2})

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        default_config = {
            "trusted_domains": [],
            "blocked_domains": [],
            "novelty_keywords": [],
            "penalties": {"blocked_domain": -20, "novelty": -10, "stale": -5},
            "bonuses": {"trusted_domain": 5, "recent": 2}
        }
        if config_path:
            path = Path(config_path)
        else:
            path = Path(__file__).resolve().parent.parent / "data" / "critic_config.json"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default_config

    def _extract_domain(self, source: str) -> str:
        if source.startswith("http"):
            try:
                return urlparse(source).netloc.lower().replace("www.", "")
            except Exception:
                pass
        return source.lower()

    def evaluate(self, idea_data: Dict[str, str]) -> float:
        """Return a numeric adjustment based on credibility, recency, and novelty."""
        adjustment = 0.0
        source = idea_data.get("source", "")
        domain = self._extract_domain(source)

        # Domain Authority
        if any(trusted in domain for trusted in self.trusted_domains):
            adjustment += self.bonuses["trusted_domain"]
        if any(blocked in domain for blocked in self.blocked_domains):
            adjustment += self.penalties["blocked_domain"]

        # Explicit Credibility Field (legacy support)
        credibility = idea_data.get("credibility", "medium").lower()
        if credibility == "high":
            adjustment += 2.0
        elif credibility == "low":
            adjustment += -2.0

        # Novelty Check
        text_content = (idea_data.get("title", "") + " " + idea_data.get("solution", "")).lower()
        if any(keyword in text_content for keyword in self.novelty_keywords):
            adjustment += self.penalties["novelty"]

        # Recency Check
        date_str = idea_data.get("source_date")
        if date_str:
            try:
                year = int(date_str.split("-")[0])
                if self.current_year - year > 3:
                    adjustment += self.penalties["stale"]
                elif self.current_year - year <= 1:
                    adjustment += self.bonuses["recent"]
            except Exception:
                pass

        return adjustment
