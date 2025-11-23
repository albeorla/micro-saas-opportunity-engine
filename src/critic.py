from typing import Dict, Optional
import datetime

class Critic:
    """Evaluate ideas based on source credibility and recency.

    In a future implementation this class would ingest information about
    where an idea came from (e.g. official reports, company blogs, user
    communities) and assign a credibility score.  It would also parse
    publication dates to account for how current the information is.  Here
    we implement a simple heuristic: ideas may optionally include a
    ``credibility`` field ("high", "medium", or "low") and a
    ``source_date`` field in ISO format (YYYY-MM-DD).  The critic maps
    these into an adjustment added to the total score: high credibility
    ideas get a small bonus, low credibility ideas get a penalty, and
    ideas older than three years incur a recency penalty.  Missing values
    default to medium credibility and no recency penalty.
    """

    def __init__(self, current_year: Optional[int] = None) -> None:
        # Allow injection of current year for testing; default to the
        # present year.
        self.current_year = current_year or datetime.datetime.now().year

    def evaluate(self, idea_data: Dict[str, str]) -> float:
        """Return a numeric adjustment based on credibility and recency.

        Parameters
        ----------
        idea_data: Dict[str, str]
            The raw idea dictionary.  May contain optional fields
            ``credibility`` and ``source_date``.

        Returns
        -------
        float
            A small positive or negative value to be added to the idea's
            total score.  Values are capped to keep adjustments modest.
        """
        credibility = idea_data.get("credibility", "medium").lower()
        # Map credibility to a bonus/penalty: high=+2, medium=0, low=-2
        cred_map = {"high": 2.0, "medium": 0.0, "low": -2.0}
        cred_bonus = cred_map.get(credibility, 0.0)
        # Recency penalty: subtract 1 point if the source is older than 3 years
        recency_penalty = 0.0
        date_str = idea_data.get("source_date")
        if date_str:
            try:
                year = int(date_str.split("-")[0])
                if self.current_year - year > 3:
                    recency_penalty = 1.0
            except Exception:
                # Ignore invalid dates
                pass
        return cred_bonus - recency_penalty
