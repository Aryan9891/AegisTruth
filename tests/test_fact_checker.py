"""Unit tests for Fact Checking and Contradiction Detection."""

import pytest
from aegistruth.core.fact_checker import extract_claims, check_internal_contradictions, verify_facts

def test_extract_claims():
    text = "In 1969, Apollo 11 landed on the moon. Carbon emissions fell by 14%."
    claims = extract_claims(text)
    assert len(claims) == 2
    assert any(c["has_metric"] for c in claims)

def test_check_internal_contradictions():
    claims = [
        {"id": 1, "text": "Global semiconductor production increased by 20% in the third quarter."},
        {"id": 2, "text": "Overall semiconductor production decreased during that exact timeframe."}
    ]
    contradictions = check_internal_contradictions(claims)
    assert len(contradictions) == 1
    assert contradictions[0]["claim_a_id"] == 1
    assert contradictions[0]["claim_b_id"] == 2

def test_verify_facts_grounded():
    text = "Apollo 11 completed the first moon landing. Water freezes at 0 degrees Celsius."
    res = verify_facts(text)
    assert res["verified_grounded_count"] >= 1
    assert res["overall_factuality_score"] >= 70.0

def test_verify_facts_anachronism():
    text = "Julius Caesar checked his email before crossing the Rubicon."
    res = verify_facts(text)
    assert len(res["anachronisms_detected"]) >= 1
    assert res["overall_factuality_score"] < 50.0
