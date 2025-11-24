import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sentence_transformers import SentenceTransformer, util

from src.models import ScoreDetail, IdeaScores

class ScoringEngine:
    """Assigns scores to ideas based on heuristic rules.

    The scoring logic is deliberately simple.  It considers the nature of
    the pain point, the potential customer base and the complexity of
    building the solution.  A more sophisticated version would use
    evidence, market data and perhaps a learned model.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config = self._load_config(config_path)
        self.maxima = self.config["maxima"]
        self.price_band_adjustments = self.config["price_band_adjustments"]
        self.price_band_buckets = self.config["price_band_buckets"]
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.demand_signals = {
            "acute": [
                "Teams are wasting hours on manual, fragmented processes that cause frustration",
                "Painful workflows are costing money and creating operational headaches",
                "Users are stuck doing inefficient, repetitive work that slows them down",
            ],
            "moderate": [
                "Work is slower than it should be and people feel stressed about it",
                "The process is confusing and takes more time than expected",
                "Users wish the task were simpler or less complex",
            ],
            "mild": [
                "The problem exists but is more of an inconvenience than a blocker",
                "There is room for improvement but current tools are acceptable",
                "Users see some friction yet can complete the task",
            ],
        }
        self.solution_complexity_signals = {
            "high": [
                "Autonomous systems orchestrating complex, safety critical workflows",
                "Digital twins or high fidelity simulations requiring heavy computation",
                "Generative design or deeply integrated internal tool builders",
            ],
            "moderate": [
                "AI assistants augmenting workflows with predictions or summarization",
                "Automation that stitches together multiple data sources and APIs",
                "Analytics dashboards that personalize insights for users",
            ],
            "low": [
                "Straightforward task automation with minimal custom logic",
                "Simple workflow coordination without deep integrations",
                "Lightweight utilities that reduce manual steps",
            ],
        }
        self._precomputed_embeddings = self._build_reference_embeddings()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Dict[str, int]]:
        default_config: Dict[str, Dict[str, int]] = {
            "maxima": {
                "demand": 30,
                "acquisition": 20,
                "mvp_complexity": 20,
                "competition": 20,
                "revenue_velocity": 10,
            },
            "price_band_buckets": {"low": 120, "mid": 500},
            "price_band_adjustments": {
                "demand": {"low": 2, "mid": 0, "high": -2},
                "acquisition": {"low": 1, "mid": 0, "high": -2},
                "mvp_complexity": {"low": -1, "mid": 0, "high": 1},
            },
        }
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path(__file__).resolve().parent.parent / "data" / "scoring_config.json"
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            # Merge user config over defaults to allow partial overrides
            for key, value in default_config.items():
                if key in user_config and isinstance(user_config[key], dict):
                    default_config[key].update(user_config[key])
            return default_config
        except FileNotFoundError:
            return default_config

    def _build_reference_embeddings(self) -> Dict[str, Dict[str, List]]:
        reference_embeddings: Dict[str, Dict[str, List]] = {"demand": {}, "complexity": {}}
        for label, phrases in self.demand_signals.items():
            reference_embeddings["demand"][label] = [
                self.embedder.encode(phrase, convert_to_tensor=True) for phrase in phrases
            ]
        for label, phrases in self.solution_complexity_signals.items():
            reference_embeddings["complexity"][label] = [
                self.embedder.encode(phrase, convert_to_tensor=True) for phrase in phrases
            ]
        return reference_embeddings

    def _semantic_match(self, text: str, reference_key: str) -> Tuple[str, float, str]:
        """Return the best matching label, similarity score and phrase."""

        text_embedding = self.embedder.encode(text, convert_to_tensor=True)
        best_label = "mild"
        best_score = -1.0
        best_phrase = ""
        references = self._precomputed_embeddings[reference_key]
        for label, embeddings in references.items():
            for idx, emb in enumerate(embeddings):
                score = util.cos_sim(text_embedding, emb).item()
                if score > best_score:
                    best_score = score
                    best_label = label
                    if reference_key == "demand":
                        best_phrase = self.demand_signals[label][idx]
                    else:
                        best_phrase = self.solution_complexity_signals[label][idx]
        return best_label, best_score, best_phrase

    def _parse_revenue_model(self, revenue_model: str) -> Dict[str, object]:
        revenue_lower = revenue_model.lower()
        contact_sales_triggers = [
            "contact sales",
            "talk to sales",
            "contact us",
            "book a demo",
            "schedule a demo",
            "request pricing",
            "request a quote",
            "call for pricing",
        ]
        contact_sales = any(trigger in revenue_lower for trigger in contact_sales_triggers)
        freemium = "freemium" in revenue_lower or "free" in revenue_lower
        price_values: List[float] = []
        price_pattern = re.compile(
            r"(?:\$|£|€)?\s*(\d+(?:[.,]\d{3})*(?:\.\d+)?)\s*(?:[–-]\s*(?:\$|£|€)?\s*(\d+(?:[.,]\d{3})*(?:\.\d+)?))?"
        )
        for match in price_pattern.finditer(revenue_model):
            start_val, end_val = match.groups()
            if start_val:
                price_values.append(float(start_val.replace(",", "")))
            if end_val:
                price_values.append(float(end_val.replace(",", "")))
        return {"prices": price_values, "contact_sales": contact_sales, "freemium": freemium}

    def _get_price_band(self, revenue_model: str) -> str:
        parsed = self._parse_revenue_model(revenue_model)
        prices = parsed["prices"]
        if parsed["contact_sales"]:
            return "high"
        if parsed["freemium"] and not prices:
            return "low"
        if not prices:
            return "mid"
        avg_price = sum(prices) / len(prices)
        if avg_price <= self.price_band_buckets.get("low", 0):
            return "low"
        if avg_price <= self.price_band_buckets.get("mid", 0):
            return "mid"
        return "high"

    def _clamp_score(self, value: int, maximum: int) -> int:
        return max(min(value, maximum), 0)

    def score_demand(self, idea: Dict[str, str]) -> ScoreDetail:
        """Compute a demand score based on qualitative attributes.

        We use semantic similarity to reference pain descriptions to
        infer demand strength.  High similarity with acute pain phrases
        like "manual, fragmented processes causing frustration" leads to
        higher scores, while alignment with milder inconvenience
        statements keeps the score lower.  Pricing still modulates the
        result to reflect acquisition friction.
        """
        pain = idea["pain"]
        price_band = self._get_price_band(idea.get("revenue_model", ""))
        adjustment = self.price_band_adjustments["demand"].get(price_band, 0)
        label, similarity, phrase = self._semantic_match(pain, "demand")
        pain_lower = pain.lower()
        mild_keywords = ["minor", "inconvenience", "nice to have", "not urgent", "small hassle"]

        # Guardrails: short or clearly low-severity descriptions can over-match to acute exemplars
        # because semantic similarity is relative. If the match confidence is low or we detect
        # explicitly mild language, force the branch to "mild" to avoid inflated scores.
        if similarity < 0.4 or any(keyword in pain_lower for keyword in mild_keywords):
            label = "mild"
            phrase = self.demand_signals["mild"][0]

        if label == "acute":
            base = 26
        elif label == "moderate":
            base = 22
        else:
            base = 16
        rationale = (
            f"Semantic match to {label} pain ('{phrase}') at similarity {similarity:.2f}; "
            f"pricing band {price_band} adjustment {adjustment:+} applies"
        )
        value = self._clamp_score(base + adjustment, self.maxima["demand"])
        return ScoreDetail(value=value, max=self.maxima["demand"], rationale=rationale)

    def score_acquisition(self, idea: Dict[str, str]) -> ScoreDetail:
        """Estimate how easy it will be to reach and acquire customers.

        We assign high scores to audiences that are broad but well defined
        (e.g. SMBs, startups) and medium scores to niche but focused
        groups such as freelancers, creators, sales teams or local
        businesses.  Highly specialized audiences like clinical labs or
        heavy industry receive lower scores due to more complex
        acquisition channels.
        """
        icp = idea["icp"].lower()
        # Groups that are large and reachable through common marketing channels
        high_keywords = ["smb", "small", "startup", "developer", "marketing", "agency", "podcaster"]
        # Groups that are more niche but still accessible via targeted outreach
        niche_keywords = [
            "freelancer",
            "creator",
            "service provider",
            "sales",
            "restaurant",
            "cafe",
            "local business",
            "content creator",
            "sales team",
            "sales reps",
            # Additional audiences added for new ideas
            "landlord",
            "real estate",
            "contractor",
            "contractors",
            "msp",
            "lawyer",
            "attorney",
            "legal",
            "accountant",
            "tax",
            "bookkeeper",
            "shopify",
            "etsy",
            "airbnb",
            "host",
            "event",
            "wedding",
            "volunteer",
            "restaurant",
            "church",
            "nonprofit",
            "creator",
            "influencer",
            "affiliate",
        ]
        # Harder audiences with specialized procurement cycles or regulatory hurdles
        hard_keywords = [
            "lab",
            "clinical",
            "construction",
            "manufacturers",
            "manufacturing",
            "compliance",
            "esg",
            "digital twin",
        ]
        price_band = self._get_price_band(idea.get("revenue_model", ""))
        adjustment = self.price_band_adjustments["acquisition"].get(price_band, 0)
        if any(keyword in icp for keyword in high_keywords):
            base = 17
            rationale = "Reachable audience with standard channels; calibrated slightly lower to reflect feedback"
        elif any(keyword in icp for keyword in niche_keywords):
            base = 15
            rationale = "Niche audience is reachable through targeted outreach"
        elif any(keyword in icp for keyword in hard_keywords):
            base = 13
            rationale = "Audience exists but is specialized and harder to reach"
        else:
            base = 11
            rationale = "Audience is broad or unclear"
        value = self._clamp_score(base + adjustment, self.maxima["acquisition"])
        rationale = (
            f"{rationale}; price band {price_band} adjustment {adjustment:+} reflects acquisition friction at that ticket size"
        )
        return ScoreDetail(value=value, max=self.maxima["acquisition"], rationale=rationale)

    def score_mvp_complexity(self, idea: Dict[str, str]) -> ScoreDetail:
        """Assign a complexity score based on the nature of the solution.

        We infer build complexity by comparing the solution description
        against representative examples.  Strong alignment with phrases
        that imply orchestration, simulation or generative systems
        reduces the score, while similarity to lightweight automation
        keeps it higher.
        """
        solution = idea["solution"]
        price_band = self._get_price_band(idea.get("revenue_model", ""))
        adjustment = self.price_band_adjustments["mvp_complexity"].get(price_band, 0)
        label, similarity, phrase = self._semantic_match(solution, "complexity")
        if label == "high":
            base = 11
        elif label == "moderate":
            base = 14
        else:
            base = 17
        rationale = (
            f"Solution aligns with {label} complexity exemplar ('{phrase}') at similarity {similarity:.2f}; "
            f"pricing band {price_band} adjustment {adjustment:+} applied"
        )
        value = self._clamp_score(base + adjustment, self.maxima["mvp_complexity"])
        return ScoreDetail(value=value, max=self.maxima["mvp_complexity"], rationale=rationale)

    def score_competition(self, idea: Dict[str, str]) -> ScoreDetail:
        """Estimate competitive pressure based on market breadth and pricing.

        We combine signals from the ICP and revenue model.  Ideas that
        target broad markets (e.g. general SMBs, marketing agencies or
        sales teams) are likely to face more competitors, while highly
        vertical or specialized solutions (e.g. compliance tools,
        construction digital twins) may encounter less competition.
        In addition, a wide pricing range (e.g. "$500+" or "$50–500")
        suggests a fragmented competitive landscape, whereas a
        narrowly defined price band indicates a more focused market.
        """
        icp = idea["icp"].lower()
        revenue = idea["revenue_model"]
        # Identify broad markets where many vendors operate
        broad_market_keywords = [
            "smb",
            "small",
            "marketing",
            "sales",
            "content creator",
            "developers",
            "agency",
        ]
        # Identify niche or vertical markets
        niche_keywords = [
            "construction",
            "clinical",
            "compliance",
            "esg",
            "digital twin",
            "internal tool",
            "script generator",
            "podcast",
            "restaurant",
            "inventory",
        ]
        # Determine competitive intensity from the ICP
        if any(k in icp for k in broad_market_keywords):
            # Broad, competitive markets
            base_value = 14
            base_rationale = "Broad addressable market likely has many competitors"
        elif any(k in icp for k in niche_keywords):
            base_value = 17
            base_rationale = "Vertical or specialized market reduces direct competition"
        else:
            base_value = 12
            base_rationale = "Market breadth unclear; assume higher competitive risk"
        # Adjust based on pricing range
        if "$" in revenue and "+" in revenue:
            # Very wide range or high end implies more varied competition
            value = max(base_value - 1, 12)
            rationale = base_rationale + "; wide pricing range indicates varied competitors"
        elif "$" in revenue and "–" in revenue:
            # Mid range pricing range; maintain base value
            value = base_value
            rationale = base_rationale + "; moderate pricing range"
        elif "$" in revenue:
            # Single price point; slight bump due to clearer niche
            value = min(base_value + 1, self.maxima["competition"])
            rationale = base_rationale + "; narrow pricing suggests clearer niche"
        else:
            # Unknown pricing; penalize slightly
            value = max(base_value - 2, 12)
            rationale = base_rationale + "; unknown pricing increases uncertainty"
        value = self._clamp_score(value, self.maxima["competition"])
        return ScoreDetail(value=value, max=self.maxima["competition"], rationale=rationale)

    def score_revenue_velocity(self, idea: Dict[str, str]) -> ScoreDetail:
        pricing = self._parse_revenue_model(idea["revenue_model"])
        price_values = pricing["prices"]
        if pricing["freemium"] and not price_values:
            value = 9
            rationale = "Freemium model suggests rapid adoption and faster velocity"
        elif pricing["contact_sales"] and not price_values:
            value = 6
            rationale = "Contact sales motion implies slower velocity despite potential high contract values"
        elif not price_values:
            value = 7
            rationale = "No explicit pricing; assume mid‑range velocity"
        else:
            avg_price = sum(price_values) / len(price_values)
            if avg_price < 100:
                value = 9
                rationale = "Low average price implies faster adoption and higher velocity"
            elif avg_price < 500:
                value = 8
                rationale = "Moderate pricing supports good revenue velocity"
            else:
                value = 6
                rationale = "High average price suggests slower customer acquisition"
        value = self._clamp_score(value, self.maxima["revenue_velocity"])
        return ScoreDetail(value=value, max=self.maxima["revenue_velocity"], rationale=rationale)

    def score_idea(self, idea: Dict[str, str]) -> IdeaScores:
        return IdeaScores(
            demand=self.score_demand(idea),
            acquisition=self.score_acquisition(idea),
            mvp_complexity=self.score_mvp_complexity(idea),
            competition=self.score_competition(idea),
            revenue_velocity=self.score_revenue_velocity(idea),
        )
