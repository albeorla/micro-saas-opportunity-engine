import json
import pytest
from src.feedback import UserFeedbackManager


def test_loads_feedback_and_maps_keys(feedback_file):
    manager = UserFeedbackManager(str(feedback_file))
    assert manager.feedback == {"first idea": 4.5, "second idea": 1.0}
    assert manager.get_adjustment("First Idea") == (4.5 - 2.5) * 2


def test_adjustment_ranges_when_missing_or_extreme(base_idea):
    manager = UserFeedbackManager()
    assert manager.get_adjustment(base_idea["title"]) == 0.0
    manager.add_rating(base_idea["title"], 0)
    assert manager.get_adjustment(base_idea["title"]) == -5.0
    manager.add_rating(base_idea["title"], 5)
    assert manager.get_adjustment(base_idea["title"]) == 5.0


def test_save_feedback_uses_provided_path(feedback_file, tmp_path):
    manager = UserFeedbackManager(str(feedback_file))
    manager.add_rating("new idea", 3)
    target = tmp_path / "saved.json"
    manager.save_feedback(target)
    saved_data = json.loads(target.read_text())
    assert saved_data["new idea"] == 3


def test_save_feedback_without_path_raises_error():
    manager = UserFeedbackManager()
    manager.add_rating("idea", 4)
    with pytest.raises(ValueError):
        manager.save_feedback()
