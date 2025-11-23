from copy import deepcopy
from src.scoring import ScoringEngine


def test_score_demand_branches(base_idea):
    engine = ScoringEngine()
    high = deepcopy(base_idea)
    high["pain"] = "Manual and expensive workflows"
    assert engine.score_demand(high).value == 27

    moderate = deepcopy(base_idea)
    moderate["pain"] = "Time consuming and stressful tasks"
    assert engine.score_demand(moderate).value == 20

    low = deepcopy(base_idea)
    low["pain"] = "Minor annoyance"
    assert engine.score_demand(low).value == 15


def test_score_acquisition_paths(base_idea):
    engine = ScoringEngine()
    broad = deepcopy(base_idea)
    broad["icp"] = "SMB marketing agencies"
    assert engine.score_acquisition(broad).value == 18

    niche = deepcopy(base_idea)
    niche["icp"] = "Independent freelancers"
    assert engine.score_acquisition(niche).value == 15

    hard = deepcopy(base_idea)
    hard["icp"] = "Clinical lab coordinators"
    assert engine.score_acquisition(hard).value == 14

    unclear = deepcopy(base_idea)
    unclear["icp"] = "Unspecified"
    assert engine.score_acquisition(unclear).value == 10


def test_score_mvp_complexity_routes(base_idea):
    engine = ScoringEngine()
    complex_idea = deepcopy(base_idea)
    complex_idea["solution"] = "Digital twin with autonomous AI"
    assert engine.score_mvp_complexity(complex_idea).value == 12

    moderate_idea = deepcopy(base_idea)
    moderate_idea["solution"] = "AI assistant for analytics"
    assert engine.score_mvp_complexity(moderate_idea).value == 15

    simple_idea = deepcopy(base_idea)
    simple_idea["solution"] = "Simple checklist app"
    assert engine.score_mvp_complexity(simple_idea).value == 18


def test_score_competition_pricing_and_audience(base_idea):
    engine = ScoringEngine()
    broad = deepcopy(base_idea)
    broad["icp"] = "Marketing agencies"
    broad["revenue_model"] = "$500+ per month"
    assert engine.score_competition(broad).value == 13

    niche = deepcopy(base_idea)
    niche["icp"] = "Construction compliance"
    niche["revenue_model"] = "$200/month"
    assert engine.score_competition(niche).value == 18

    unknown = deepcopy(base_idea)
    unknown["icp"] = "Unclear audience"
    unknown["revenue_model"] = "TBD"
    assert engine.score_competition(unknown).value == 12


def test_score_revenue_velocity_ranges(base_idea):
    engine = ScoringEngine()
    low_price = deepcopy(base_idea)
    low_price["revenue_model"] = "$29 per month"
    assert engine.score_revenue_velocity(low_price).value == 9

    mid_price = deepcopy(base_idea)
    mid_price["revenue_model"] = "$199 – $299 per month"
    assert engine.score_revenue_velocity(mid_price).value == 8

    high_price = deepcopy(base_idea)
    high_price["revenue_model"] = "$1000 per year"
    assert engine.score_revenue_velocity(high_price).value == 6

    unknown_price = deepcopy(base_idea)
    unknown_price["revenue_model"] = "contact us"
    assert engine.score_revenue_velocity(unknown_price).value == 6
