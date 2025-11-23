import json
import sys
from pathlib import Path
import pytest

# Ensure the src package is importable when running tests from repo root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


@pytest.fixture
def base_idea():
    return {
        "title": "Test Idea",
        "icp": "Small businesses",
        "pain": "Manual workflows are costly",
        "solution": "Simple automation",
        "revenue_model": "$10/month",
    }


@pytest.fixture
def feedback_file(tmp_path: Path):
    path = tmp_path / "feedback.json"
    data = {"First Idea": 4.5, "Second Idea": 1}
    path.write_text(json.dumps(data))
    return path
