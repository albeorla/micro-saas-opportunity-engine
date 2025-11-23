from typing import Dict, Optional
import json

class UserFeedbackManager:
    """Manages user feedback and provides score adjustments.

    Feedback is stored in a JSON file mapping idea titles to a
    numeric rating (0–5).  When present, a simple linear mapping
    converts the rating into a score adjustment: rating * 2.  This
    allows highly rated ideas to receive a boost and poorly rated
    ideas to be penalised.  Missing feedback yields no adjustment.
    """

    def __init__(self, feedback_path: Optional[str] = None) -> None:
        self.feedback_path = feedback_path
        self.feedback: Dict[str, float] = {}
        if feedback_path:
            try:
                with open(feedback_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # Normalize keys to lower case for matching
                    self.feedback = {k.lower(): float(v) for k, v in data.items()}
            except Exception:
                # Silently ignore errors; feedback remains empty
                self.feedback = {}

    def get_adjustment(self, title: str) -> float:
        rating = self.feedback.get(title.lower())
        if rating is None:
            return 0.0
        # Map rating (0–5) to adjustment (−5 to +5) by centering at 2.5
        # Then scale down: rating 5 -> +5, rating 0 -> -5
        adjustment = (rating - 2.5) * 2
        return adjustment

    def add_rating(self, title: str, rating: float) -> None:
        """Add or update a rating for an idea."""
        self.feedback[title.lower()] = float(rating)

    def save_feedback(self, path: Optional[str] = None) -> None:
        """Save the current feedback dictionary to a JSON file."""
        target_path = path or self.feedback_path
        if not target_path:
            raise ValueError("No feedback path specified.")
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.feedback, f, indent=2)
