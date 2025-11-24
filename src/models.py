from dataclasses import dataclass, field
from typing import Any, Dict, List
from typing import List, Dict, Optional

@dataclass
class Evidence:
    """Represents a single piece of evidence supporting an idea.

    Attributes
    ----------
    source: str
        A short identifier for where the evidence came from (e.g. a
        website or report name).
    claim: str
        The claim extracted from the source.
    strength: str
        A qualitative measure of how strong the evidence is ("weak",
        "medium", or "strong").
    dimension: str
        The aspect of the idea this evidence supports (e.g. "demand",
        "pain", "competition", etc.).
    """

    source: str
    claim: str
    strength: str
    dimension: str


@dataclass
class ScoreDetail:
    """Stores a numeric score and a human‑readable rationale."""

    value: int
    max: int
    rationale: str


@dataclass
class IdeaScores:
    """Aggregates the different scoring dimensions for an idea."""

    demand: ScoreDetail
    acquisition: ScoreDetail
    mvp_complexity: ScoreDetail
    competition: ScoreDetail
    revenue_velocity: ScoreDetail

    @property
    def total(self) -> ScoreDetail:
        total_value = (
            self.demand.value
            + self.acquisition.value
            + self.mvp_complexity.value
            + self.competition.value
            + self.revenue_velocity.value
        )
        max_total = (
            self.demand.max
            + self.acquisition.max
            + self.mvp_complexity.max
            + self.competition.max
            + self.revenue_velocity.max
        )
        return ScoreDetail(value=total_value, max=max_total, rationale="Sum of component scores")


@dataclass
class Idea:
    """Represents a micro‑SaaS opportunity."""

    title: str
    icp: str  # ideal customer profile
    pain: str
    solution: str
    revenue_model: str
    evidence: List[Evidence]
    scores: IdeaScores
    recommendation: str
    key_risks: List[str]
    search_volume: Optional[int] = None
    keyword_difficulty: Optional[int] = None
    trend_status: str = "Unknown"
    # The adjusted total score after credibility and feedback adjustments
    final_total: float = field(default=0.0)
    critic_adjustment: float = field(default=0.0)
    feedback_adjustment: float = field(default=0.0)
    critic_rationale: str = field(default="")
    seo_metrics: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "icp": self.icp,
            "pain": self.pain,
            "solution": self.solution,
            "revenue_model": self.revenue_model,
            "search_volume": self.search_volume if self.search_volume is not None else "N/A",
            "keyword_difficulty": self.keyword_difficulty if self.keyword_difficulty is not None else "N/A",
            "trend_status": self.trend_status,
            "demand_score": f"{self.scores.demand.value}/{self.scores.demand.max}",
            "acquisition_score": f"{self.scores.acquisition.value}/{self.scores.acquisition.max}",
            "mvp_complexity_score": f"{self.scores.mvp_complexity.value}/{self.scores.mvp_complexity.max}",
            "competition_score": f"{self.scores.competition.value}/{self.scores.competition.max}",
            "revenue_velocity_score": f"{self.scores.revenue_velocity.value}/{self.scores.revenue_velocity.max}",
                # Show the adjusted total alongside the maximum; round to nearest integer
                "total_score": f"{int(round(self.final_total))}/{self.scores.total.max}",
            "recommendation": self.recommendation,
            "key_risks": "; ".join(self.key_risks),
            "critic_adjustment": f"{self.critic_adjustment:+}",
            "feedback_adjustment": f"{self.feedback_adjustment:+}",
            "critic_rationale": self.critic_rationale,
            "seo_search_volume": self.seo_metrics.get("search_volume", ""),
            "seo_keyword_difficulty": self.seo_metrics.get("keyword_difficulty", ""),
            "seo_trend_direction": self.seo_metrics.get("trend_direction", ""),
        }
