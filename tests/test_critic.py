from src.critic import Critic


def test_credibility_mapping_and_defaults(base_idea):
    critic = Critic(current_year=2026)
    high = {**base_idea, "credibility": "high"}
    low = {**base_idea, "credibility": "low"}
    missing = {**base_idea}

    assert critic.evaluate(high) == 2.0
    assert critic.evaluate(low) == -2.0
    assert critic.evaluate(missing) == 0.0


def test_recency_penalty_applied_when_outdated(base_idea):
    critic = Critic(current_year=2026)
    outdated = {**base_idea, "source_date": "2020-01-01"}
    recent = {**base_idea, "source_date": "2024-06-15"}

    assert critic.evaluate(outdated) == -1.0
    assert critic.evaluate(recent) == 0.0


def test_invalid_dates_are_ignored(base_idea):
    critic = Critic(current_year=2026)
    invalid_date = {**base_idea, "source_date": "20XX-13-40"}
    assert critic.evaluate(invalid_date) == 0.0
