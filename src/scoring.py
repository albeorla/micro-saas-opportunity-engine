from typing import Dict
from src.models import ScoreDetail, IdeaScores

class ScoringEngine:
    """Assigns scores to ideas based on heuristic rules.

    The scoring logic is deliberately simple.  It considers the nature of
    the pain point, the potential customer base and the complexity of
    building the solution.  A more sophisticated version would use
    evidence, market data and perhaps a learned model.
    """

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
        high_signals = ["manual", "fragmented", "expensive", "costly", "waste", "inefficient"]
        moderate_signals = ["time", "complex", "struggle", "lack", "burnout", "stress", "slow"]
        if any(word in pain for word in high_signals):
            value = 27  # strong demand when the problem is painful and costly
            rationale = "High pain and cost indicate strong demand"
        elif any(word in pain for word in moderate_signals):
            value = 20
            rationale = "Moderate demand for time‑consuming, stressful or complex tasks"
        else:
            value = 15
            rationale = "Lower demand for less acute problems"
        return ScoreDetail(value=value, max=30, rationale=rationale)

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
        if any(keyword in icp for keyword in high_keywords):
            value = 18
            rationale = "Target audience is well defined and reachable via common channels"
        elif any(keyword in icp for keyword in niche_keywords):
            value = 15
            rationale = "Niche audience is reachable through targeted outreach"
        elif any(keyword in icp for keyword in hard_keywords):
            value = 14
            rationale = "Audience exists but is more specialized and harder to reach"
        else:
            value = 10
            rationale = "Audience is broad or unclear"
        return ScoreDetail(value=value, max=20, rationale=rationale)

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
        if any(k in solution for k in high_complexity_keywords):
            value = 12
            rationale = "Solution involves sophisticated technology or multi‑system integration, increasing build complexity"
        elif any(k in solution for k in moderate_keywords):
            value = 15
            rationale = "AI or integration components add some complexity to the MVP"
        else:
            value = 18
            rationale = "Relatively simple automation results in a lower complexity MVP"
        return ScoreDetail(value=value, max=20, rationale=rationale)

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
            value = min(base_value + 1, 20)
            rationale = base_rationale + "; narrow pricing suggests clearer niche"
        else:
            # Unknown pricing; penalize slightly
            value = max(base_value - 2, 12)
            rationale = base_rationale + "; unknown pricing increases uncertainty"
        return ScoreDetail(value=value, max=20, rationale=rationale)

    def score_revenue_velocity(self, idea: Dict[str, str]) -> ScoreDetail:
        price_values = []
        for part in idea["revenue_model"].split("$"):
            for token in part.split(" "):
                if token.strip().replace(",", "").replace("–", "-").replace("-", "").isdigit():
                    try:
                        price_values.append(float(token.strip().replace(",", "")))
                    except ValueError:
                        continue
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
        return ScoreDetail(value=value, max=10, rationale=rationale)

    def score_idea(self, idea: Dict[str, str]) -> IdeaScores:
        return IdeaScores(
            demand=self.score_demand(idea),
            acquisition=self.score_acquisition(idea),
            mvp_complexity=self.score_mvp_complexity(idea),
            competition=self.score_competition(idea),
            revenue_velocity=self.score_revenue_velocity(idea),
        )
