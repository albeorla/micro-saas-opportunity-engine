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
