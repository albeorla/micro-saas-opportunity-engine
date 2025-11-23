import pytest
from src.critic import Critic
import json
import os

@pytest.fixture
def config_file(tmp_path):
    config = {
        "trusted_domains": ["trusted.com"],
        "blocked_domains": ["spam.com"],
        "novelty_keywords": ["wrapper"],
        "penalties": {"blocked_domain": -10, "novelty": -5, "stale": -2},
        "bonuses": {"trusted_domain": 3, "recent": 1}
    }
    path = tmp_path / "test_critic_config.json"
    with open(path, "w") as f:
        json.dump(config, f)
    return str(path)

def test_domain_authority(config_file):
    critic = Critic(config_path=config_file)
    
    # Trusted domain
    assert critic.evaluate({"source": "https://trusted.com/article"}) == 3
    
    # Blocked domain
    assert critic.evaluate({"source": "http://spam.com/list"}) == -10
    
    # Neutral domain
    assert critic.evaluate({"source": "https://unknown.com"}) == 0

def test_novelty_check(config_file):
    critic = Critic(config_path=config_file)
    
    # Novelty keyword in title
    assert critic.evaluate({"title": "ChatGPT Wrapper App", "solution": "foo"}) == -5
    
    # Novelty keyword in solution
    assert critic.evaluate({"title": "App", "solution": "Just a wrapper around API"}) == -5

def test_recency_check(config_file):
    critic = Critic(config_path=config_file, current_year=2025)
    
    # Recent (<= 1 year)
    assert critic.evaluate({"source_date": "2025-01-01"}) == 1
    assert critic.evaluate({"source_date": "2024-06-01"}) == 1
    
    # Stale (> 3 years)
    assert critic.evaluate({"source_date": "2021-01-01"}) == -2
    
    # Neutral
    assert critic.evaluate({"source_date": "2023-01-01"}) == 0

def test_combined_factors(config_file):
    critic = Critic(config_path=config_file, current_year=2025)
    
    # Trusted + Recent
    idea = {
        "source": "https://trusted.com",
        "source_date": "2025-01-01"
    }
    assert critic.evaluate(idea) == 3 + 1
    
    # Blocked + Novelty
    idea = {
        "source": "https://spam.com",
        "title": "Wrapper"
    }
    assert critic.evaluate(idea) == -10 - 5


def test_evaluate_with_rationale_matches_numeric(config_file):
    critic = Critic(config_path=config_file, current_year=2025)
    idea = {
        "source": "https://trusted.com/path",
        "source_date": "2024-12-12",
        "title": "Not a wrapper",
    }
    numeric = critic.evaluate(idea)
    numeric_with_reason, rationale = critic.evaluate_with_rationale(idea)
    assert numeric == numeric_with_reason
    # Should mention at least one signal in rationale
    assert "trusted" in rationale or "recent" in rationale
