import json
from pathlib import Path
from typing import Dict, List, Optional
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

    def _extract_prices(self, revenue_model: str) -> List[float]:
        price_values: List[float] = []
        for part in revenue_model.split("$"):
            for token in part.replace("/", " ").split(" "):
                cleaned = token.strip().replace(",", "").replace("–", "-")
                if cleaned.replace("-", "").isdigit() and cleaned:
                    try:
                        price_values.append(float(cleaned.split("-")[0]))
                    except ValueError:
                        continue
        return price_values

    def _get_price_band(self, revenue_model: str) -> str:
        prices = self._extract_prices(revenue_model)
        if not prices:
            return "unknown"
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

        We look for keywords that signal that the target users are
        currently in pain.  Problems described as expensive, manual,
        fragmented or wasteful are treated as high demand.  If the
        issue relates to time, burnout, complexity or general struggle,
        we assign a moderate demand score.  Otherwise we assume lower
        demand.
        """
        pain = idea["pain"].lower()
        price_band = self._get_price_band(idea.get("revenue_model", ""))
        adjustment = self.price_band_adjustments["demand"].get(price_band, 0)
        high_signals = ["manual", "fragmented", "expensive", "costly", "waste", "inefficient"]
        moderate_signals = ["time", "complex", "struggle", "lack", "burnout", "stress", "slow"]
        if any(word in pain for word in high_signals):
            base = 26  # Calibrated down slightly from feedback to leave headroom for pricing effect
            rationale = "High pain keywords; calibrated demand baseline with price band adjustment"
        elif any(word in pain for word in moderate_signals):
            base = 22
            rationale = "Moderate demand from time, stress or complexity signals with calibrated adjustment"
        else:
            base = 16
            rationale = "Lower demand for less acute problems; pricing keeps it grounded"
        value = self._clamp_score(base + adjustment, self.maxima["demand"])
        rationale = f"{rationale} (price band: {price_band}, adjustment {adjustment:+})"
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

        We consider certain keywords that signal particularly hard
        engineering challenges: digital twins, generative design,
        autonomous AI systems and highly integrated no‑code builders.  If
        these appear in the solution, we assign a low complexity score
        (indicating a complex build).  If the solution uses AI or
        automation broadly, we assign a mid‑range score.  Otherwise we
        treat the MVP as relatively simple.
        """
        solution = idea["solution"].lower()
        # Keywords associated with high technical complexity
        high_complexity_keywords = [
            "autonomous ai",
            "digital twin",
            "generative design",
            "internal tool builder",
            "script generator",
            "smart contract",
            "esg",
            "compliance",
        ]
        # Keywords associated with moderate complexity (AI/ML or integration)
        moderate_keywords = [
            "ai",
            "predict",
            "automates",
            "analytics",
            "automation",
            "workflow",
            "dashboard",
            "assistant",
        ]
        price_band = self._get_price_band(idea.get("revenue_model", ""))
        adjustment = self.price_band_adjustments["mvp_complexity"].get(price_band, 0)
        if any(k in solution for k in high_complexity_keywords):
            base = 11
            rationale = "High‑complexity tech stack; calibrated down with sensitivity to enterprise pricing tolerance"
        elif any(k in solution for k in moderate_keywords):
            base = 14
            rationale = "AI or integration components add some complexity to the MVP"
        else:
            base = 17
            rationale = "Relatively simple automation keeps MVP complexity low"
        value = self._clamp_score(base + adjustment, self.maxima["mvp_complexity"])
        rationale = f"{rationale} (price band: {price_band}, adjustment {adjustment:+})"
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
        price_values = self._extract_prices(idea["revenue_model"])
        if not price_values:
            value = 6
            rationale = "Unknown pricing, assume moderate velocity"
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
