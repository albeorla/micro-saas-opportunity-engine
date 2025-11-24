from __future__ import annotations

from datetime import datetime
import json
import os
import re
from typing import List, Dict, Optional, Any

class Researcher:
    """A very simple researcher that returns new micro‑SaaS ideas.

    This class simulates automatic research by providing additional ideas
    sourced from trusted external articles.  In a full implementation this
    component would issue live web queries and scrape structured data.
    For the MVP, we hard‑code a selection of extra ideas distilled from
    credible 2025 micro‑SaaS idea lists.
    """

    def __init__(
        self,
        urls: Optional[List[str]] = None,
        config_path: Optional[str] = None,
        min_credibility: Optional[str] = None,
        search_api_key: Optional[str] = None,
        search_endpoint: Optional[str] = None,
    ) -> None:
        config = self._load_config(config_path)
        config_urls = config.get("source_urls", []) if isinstance(config, dict) else []
        config_min_cred = config.get("min_credibility") if isinstance(config, dict) else None
        self.min_credibility = (min_credibility or config_min_cred or "low").lower()
        config_search_key = config.get("search_api_key") if isinstance(config, dict) else None
        config_search_endpoint = config.get("search_endpoint") if isinstance(config, dict) else None

        self.search_api_key = (
            search_api_key
            or os.getenv("BING_SEARCH_API_KEY")
            or os.getenv("SEARCH_API_KEY")
            or config_search_key
        )
        self.search_endpoint = (
            search_endpoint
            or os.getenv("BING_SEARCH_ENDPOINT")
            or config_search_endpoint
            or "https://api.bing.microsoft.com/v7.0/search"
        )

        # Extra ideas drawn from the Upsilon article on micro‑SaaS trends
        # NOTE: All of these examples are simplified.  The "pain" and
        # "solution" fields summarize the problem and the product in a
        # self‑contained way.  Revenue models are illustrative and would
        # need validation.  Key risks highlight potential pitfalls.
        curated_ideas: List[Dict[str, Any]] = [
            {
                "title": "Candidate screening app",
                "icp": "Recruiters and HR teams at small and medium businesses",
                "pain": "Manual resume screening and shortlisting candidates consumes hours of recruiter time",
                "solution": "AI‑powered SaaS that parses resumes and ranks candidates by relevance and skills",
                "revenue_model": "$49–199/month per recruiter",
                "key_risks": [
                    "Requires accurate AI models and compliance with equal opportunity laws",
                    "Risk of algorithmic bias impacting fairness",
                ],
                "source": "curated:upsilon-2025",
                "source_date": "2025-01-01",
                "credibility": "high",
            },
            {
                "title": "SEO keyword research assistant",
                "icp": "Small marketing agencies and freelance marketers",
                "pain": "Finding profitable long‑tail keywords and assessing SEO difficulty is tedious",
                "solution": "Tool that suggests keywords, analyzes competition and surfaces low‑hanging SEO opportunities",
                "revenue_model": "$29–99/month subscription",
                "key_risks": [
                    "Crowded market with existing tools", "Requires up‑to‑date search engine data",
                ],
                "source": "curated:upsilon-2025",
                "source_date": "2025-01-01",
                "credibility": "high",
            },
            {
                "title": "Visual dashboard builder",
                "icp": "Data analysts and small business owners",
                "pain": "Non‑technical users struggle to build dashboards from diverse data sources",
                "solution": "Drag‑and‑drop SaaS that connects to spreadsheets and databases and auto‑creates interactive dashboards",
                "revenue_model": "$59–199/month depending on seats",
                "key_risks": [
                    "Integration complexity with many data sources", "Competes with established BI platforms",
                ],
                "source": "curated:upsilon-2025",
                "source_date": "2025-01-01",
                "credibility": "high",
            },
            {
                "title": "Automated customer feedback annotation tool",
                "icp": "Product managers and support teams",
                "pain": "Large volumes of customer feedback are hard to categorize and act on",
                "solution": "Micro‑SaaS that uses NLP to tag and summarize feedback, highlighting top issues and feature requests",
                "revenue_model": "$49–149/month based on data volume",
                "key_risks": [
                    "NLP accuracy must be high to be useful",
                    "Potential overlap with existing sentiment analysis platforms",
                ],
                "source": "curated:upsilon-2025",
                "source_date": "2025-01-01",
                "credibility": "high",
            },
            {
                "title": "AI detector for content origin",
                "icp": "Educators, content platforms and hiring managers",
                "pain": "It is difficult to verify whether essays, code samples or articles were generated by AI systems like ChatGPT",
                "solution": "SaaS that analyzes text and returns a likelihood score of AI authorship using models trained on synthetic vs. human data",
                "revenue_model": "$19–99/month per organization",
                "key_risks": [
                    "Rapidly evolving AI models may outpace detection algorithms", "Potential false positives impacting users",
                ],
                "source": "curated:upsilon-2025",
                "source_date": "2025-01-01",
                "credibility": "high",
            },
        ]

        self.extra_ideas: List[Dict[str, str]] = [self._normalize_idea(idea) for idea in curated_ideas]

        # Paths to local text files containing bullet‑pointed micro‑SaaS ideas.
        # Each file should use UTF‑8 encoding.  Lines beginning with a
        # bullet marker ("-", "*", "•") are parsed into idea
        # definitions.  In a complete system these files could be
        # auto‑generated by scraping trusted sources and stored in a
        # cache.  They remain empty by default.
        self.source_files: List[str] = []

        # Remote URLs to fetch and parse for additional ideas.
        configured_urls = urls or config_urls
        self.source_urls: List[str] = list(dict.fromkeys(configured_urls)) if configured_urls else []

    def _load_config(self, path: Optional[str]) -> Dict[str, Any]:
        if not path:
            return {}
        try:
            if path.lower().endswith((".yaml", ".yml")):
                import yaml  # type: ignore

                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _clean_text(self, value: str) -> str:
        """Normalize whitespace and stray bullet markers."""

        if not value:
            return ""
        cleaned = value.replace("\n", " ").replace("•", "").replace("\t", " ")
        return " ".join(cleaned.split()).strip()

    def _normalize_idea(self, idea: Dict[str, Any], source: Optional[str] = None, source_date: Optional[str] = None) -> Dict[str, str]:
        default_date = source_date or idea.get("source_date") or datetime.utcnow().date().isoformat()
        normalized = {
            "title": self._clean_text(idea.get("title", "")),
            "icp": self._clean_text(idea.get("icp", "")),
            "pain": self._clean_text(idea.get("pain", "")),
            "solution": self._clean_text(idea.get("solution", "")),
            "revenue_model": self._clean_text(idea.get("revenue_model", "")),
            "key_risks": idea.get("key_risks", []) or [],
            "source": source or idea.get("source", "unknown"),
            "source_date": default_date,
            "credibility": (idea.get("credibility") or "medium").lower(),
        }
        if isinstance(normalized["key_risks"], str):
            normalized["key_risks"] = [self._clean_text(normalized["key_risks"])]
        else:
            normalized["key_risks"] = [self._clean_text(risk) for risk in normalized["key_risks"]]
        return normalized

    def _credibility_level(self, label: str) -> int:
        ordering = {"low": 0, "medium": 1, "high": 2}
        return ordering.get(label.lower(), 0)

    def _meets_minimum_credibility(self, label: str) -> bool:
        return self._credibility_level(label) >= self._credibility_level(self.min_credibility)

    def _deduplicate_ideas(self, ideas: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Deduplicate ideas by normalized title, keeping the highest‑credibility entry."""

        deduped: Dict[str, Dict[str, str]] = {}
        for idea in ideas:
            title_key = idea.get("title", "").lower()
            if not title_key:
                continue
            current = deduped.get(title_key)
            if current is None or self._credibility_level(idea.get("credibility", "")) > self._credibility_level(current.get("credibility", "")):
                deduped[title_key] = idea
        return list(deduped.values())

    def _build_search_queries(self, theme: str) -> List[str]:
        base = theme.strip()
        if not base:
            return []
        variants = [
            f"{base} pain points",
            f"{base} alternatives",
            f"{base} automation tools",
            f"{base} SaaS solutions",
            f"{base} software ideas",
            f"{base} workflow bottlenecks",
        ]
        return list(dict.fromkeys(variants))

    def _semantic_relevance(self, text: str, theme: str) -> bool:
        lowered = text.lower()
        theme_tokens = [tok for tok in re.split(r"\W+", theme.lower()) if tok]
        theme_match = any(tok in lowered for tok in theme_tokens)
        saas_markers = [
            "saas",
            "software",
            "platform",
            "tool",
            "automation",
            "app",
            "solution",
            "service",
        ]
        pain_markers = [
            "pain",
            "problem",
            "challenge",
            "struggle",
            "manual",
            "time-consuming",
            "inefficient",
            "expensive",
            "alternatives",
        ]
        marker_match = any(marker in lowered for marker in saas_markers) and any(
            marker in lowered for marker in pain_markers
        )
        return theme_match and marker_match

    def _extract_pain_sentence(self, text: str, theme: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in ["challenge", "struggle", "problem", "pain", "costly", "manual"]):
                return self._clean_text(sentence)
        if sentences:
            return self._clean_text(sentences[0])
        return f"{theme} users face unresolved challenges."

    def _result_to_idea(self, result: Dict[str, Any], theme: str) -> Optional[Dict[str, str]]:
        title = self._clean_text(result.get("name", ""))
        snippet = self._clean_text(result.get("snippet", ""))
        if not title and not snippet:
            return None
        text_blob = f"{title}. {snippet}".strip()
        if not self._semantic_relevance(text_blob, theme):
            return None

        pain = self._extract_pain_sentence(snippet or title, theme)
        solution = f"Micro-SaaS automation that addresses '{pain}' with a lightweight {theme} tool."
        return self._normalize_idea(
            {
                "title": title or f"{theme.title()} micro-SaaS opportunity",
                "icp": f"Teams focused on {theme}",
                "pain": pain,
                "solution": solution,
                "revenue_model": "$29–199/month subscription",
                "key_risks": ["Requires validation of real-world demand", "Competition from existing software"],
                "source": result.get("url") or "search:web",
                "source_date": datetime.utcnow().date().isoformat(),
                "credibility": "medium",
            }
        )

    def _search_query(self, query: str, theme: str) -> List[Dict[str, str]]:
        if not self.search_api_key:
            return []
        try:
            import requests  # type: ignore
        except Exception:
            return []

        try:
            response = requests.get(
                self.search_endpoint,
                headers={"Ocp-Apim-Subscription-Key": self.search_api_key},
                params={"q": query, "mkt": "en-US", "count": 6, "textDecorations": False, "textFormat": "Raw"},
                timeout=10,
            )
            if response.status_code != 200:
                return []
            payload = response.json()
            results = payload.get("webPages", {}).get("value", [])
        except Exception:
            return []

        ideas: List[Dict[str, str]] = []
        for result in results:
            idea = self._result_to_idea(result, theme)
            if idea:
                ideas.append(idea)
        return ideas

    def parse_bullet_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Attempt to extract an idea from a bullet line.

        The parser searches for a pattern like:

            "Idea name – pain description. Solution description. Pricing"

        or

            "Idea name: pain description; solution description; pricing"

        It splits the line at the first dash or colon to identify the
        title.  The remainder is split on semicolons or periods to
        separate the pain and solution.  A revenue model is detected
        by searching for a currency symbol followed by numbers.  If no
        recognizable pattern is found, returns None.

        Parameters
        ----------
        line: str
            A single line beginning with a bullet marker.

        Returns
        -------
        Optional[Dict[str, str]]
            A partial idea dictionary with title, pain, solution and
            revenue_model fields, or None if parsing fails.
        """
        import re
        text = line.strip().lstrip("-*• ")
        if len(text) < 10:
            return None
        # Look for first occurrence of dash (– or -) or colon
        sep_match = re.search(r"[–-]|:", text)
        if not sep_match:
            return None
        sep_index = sep_match.start()
        title = text[:sep_index].strip()
        remainder = text[sep_index + 1:].strip()
        # Split remainder into clauses
        clauses = re.split(r"[.;]", remainder)
        clauses = [c.strip() for c in clauses if c.strip()]
        if not clauses:
            return None
        pain = clauses[0]
        solution = clauses[1] if len(clauses) > 1 else ""
        revenue_model = ""
        # Search for pricing pattern
        price_match = re.search(r"\$[0-9][0-9,]*(?:–[0-9][0-9,]*)?", line)
        if price_match:
            revenue_model = price_match.group(0)
        return {
            "title": title,
            "icp": "",
            "pain": pain,
            "solution": solution,
            "revenue_model": revenue_model,
            "key_risks": [],
            "credibility": "medium",
        }

    def load_from_file(self, path: str) -> List[Dict[str, str]]:
        """
        Load micro‑SaaS ideas from a local text file.

        Each line that begins with a recognized bullet marker is passed
        to :meth:`parse_bullet_line`.  Parsing errors or unreadable
        files result in an empty list.

        Parameters
        ----------
        path: str
            Path to the text file.

        Returns
        -------
        List[Dict[str, str]]
            The ideas extracted from the file.
        """
        ideas: List[Dict[str, str]] = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith(("-", "*", "•")):
                        idea = self.parse_bullet_line(stripped)
                        if idea:
                            ideas.append(self._normalize_idea(idea, source=os.path.basename(path)))
        except Exception:
            return []
        return ideas

    def fetch_from_url(self, url: str) -> List[Dict[str, str]]:
        """
        Fetch a webpage and extract bullet‑pointed ideas.

        This method uses the `requests` and `bs4` libraries to download
        HTML content and parse visible text.  It scans for lines that
        start with common bullet markers and extracts idea definitions
        using :meth:`parse_bullet_line`.  If network access is
        unavailable or dependencies are missing, returns an empty list.

        Parameters
        ----------
        url: str
            URL of the page to fetch.

        Returns
        -------
        List[Dict[str, str]]
            Extracted ideas from the page, or empty on failure.
        """
        ideas: List[Dict[str, str]] = []
        try:
            import requests  # type: ignore
            from bs4 import BeautifulSoup  # type: ignore
        except Exception:
            return []
        try:
            response = requests.get(url, timeout=8)
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text("\n")
            source_date = response.headers.get("Date")
            parsed_date = None
            if source_date:
                try:
                    from email.utils import parsedate_to_datetime

                    parsed_date = parsedate_to_datetime(source_date).date().isoformat()
                except Exception:
                    parsed_date = None
            for line in text.split("\n"):
                stripped = line.strip()
                if stripped.startswith(("-", "*", "•")):
                    idea = self.parse_bullet_line(stripped)
                    if idea:
                        normalized = self._normalize_idea(idea, source=url, source_date=parsed_date)
                        ideas.append(normalized)
        except Exception:
            return []
        return ideas

    def search_micro_saas_ideas(self, theme: str) -> List[Dict[str, str]]:
        """
        Return a list of additional ideas related to the given theme.

        The researcher builds themed search queries and fetches live
        search results from a web search API.  Results are semantically
        filtered to keep entries related to SaaS‑style pain points and
        automation opportunities.  Curated ideas and configured sources
        remain as a fallback.

        Parameters
        ----------
        theme: str
            A high level domain or topic provided by the user, used to
            construct targeted queries.

        Returns
        -------
        List[Dict[str, str]]
            A combined list of idea dictionaries.
        """
        combined: List[Dict[str, str]] = []

        for query in self._build_search_queries(theme):
            combined.extend(self._search_query(query, theme))

        # Fallbacks
        combined.extend(self.extra_ideas)
        for path in self.source_files:
            combined.extend(self.load_from_file(path))
        for url in self.source_urls:
            combined.extend(self.fetch_from_url(url))

        filtered = [idea for idea in combined if self._meets_minimum_credibility(idea.get("credibility", "medium"))]
        deduped = self._deduplicate_ideas(filtered)
        return deduped
