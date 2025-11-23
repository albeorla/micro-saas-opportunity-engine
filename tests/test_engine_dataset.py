import json
import pytest
from src.engine import OpportunityEngine


def test_load_dataset_requires_array(tmp_path):
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps({"title": "Not a list"}))
    engine = OpportunityEngine.__new__(OpportunityEngine)
    with pytest.raises(ValueError, match="JSON array"):
        engine._load_dataset_from_file(path)


def test_load_dataset_validates_required_fields(tmp_path):
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps([{"title": "Idea", "icp": "Audience"}]))
    with pytest.raises(ValueError, match="missing required fields"):
        OpportunityEngine.__new__(OpportunityEngine)._load_dataset_from_file(path)


def test_load_dataset_rejects_non_list_risks(tmp_path):
    path = tmp_path / "dataset.json"
    invalid_item = {
        "title": "Idea",
        "icp": "Audience",
        "pain": "Pain point",
        "solution": "Solution",
        "revenue_model": "$50/month",
        "key_risks": "not-a-list",
    }
    path.write_text(json.dumps([invalid_item]))
    with pytest.raises(ValueError, match="must be a list"):
        OpportunityEngine.__new__(OpportunityEngine)._load_dataset_from_file(path)


def test_refine_filters_critic_and_targets_dimension():
    # Build a lightweight engine with stubbed researcher data
    engine = OpportunityEngine.__new__(OpportunityEngine)
    engine.theme = "test theme"
    from src.scoring import ScoringEngine
    engine.scoring_engine = ScoringEngine()

    class DummyResearcher:
        def __init__(self, ideas):
            self._ideas = ideas

        def search_micro_saas_ideas(self, theme):
            return list(self._ideas)

    new_ideas = [
        {
            "title": "High Demand Idea",
            "icp": "Small businesses",
            "pain": "Manual and expensive",
            "solution": "Automation",
            "revenue_model": "$50/month",
            "key_risks": [],
        },
        {
            "title": "High Acquisition Idea",
            "icp": "SMB marketing agencies",
            "pain": "Minor",
            "solution": "Tool",
            "revenue_model": "$200/month",
            "key_risks": [],
        },
    ]
    engine.researcher = DummyResearcher(new_ideas)
    # Existing dataset entries (to be filtered out)
    engine.idea_dataset = [
        {"title": "Red", "icp": "", "pain": "", "solution": "", "revenue_model": "", "key_risks": []},
        {"title": "Critic Fail", "icp": "", "pain": "", "solution": "", "revenue_model": "", "key_risks": []},
    ]
    # Construct scored ideas mirroring the dataset
    from src.models import Idea, IdeaScores, ScoreDetail

    dummy_scores = IdeaScores(
        demand=ScoreDetail(value=10, max=20, rationale=""),
        acquisition=ScoreDetail(value=8, max=20, rationale=""),
        mvp_complexity=ScoreDetail(value=10, max=20, rationale=""),
        competition=ScoreDetail(value=10, max=20, rationale=""),
        revenue_velocity=ScoreDetail(value=5, max=10, rationale=""),
    )
    scored_ideas = [
        Idea(
            title="Red",
            icp="",
            pain="",
            solution="",
            revenue_model="",
            evidence=[],
            scores=dummy_scores,
            recommendation="red_kill",
            key_risks=[],
        ),
        Idea(
            title="Critic Fail",
            icp="",
            pain="",
            solution="",
            revenue_model="",
            evidence=[],
            scores=dummy_scores,
            recommendation="yellow_validate",
            key_risks=[],
            critic_adjustment=-6,
        ),
    ]

    engine.refine_dataset(scored_ideas)
    titles = {idea["title"] for idea in engine.idea_dataset}
    # Original ideas removed, new ideas inserted
    assert "Red" not in titles
    assert "Critic Fail" not in titles
    assert "High Demand Idea" in titles
