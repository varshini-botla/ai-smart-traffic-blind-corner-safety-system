"""
Unit tests for Deterministic Safety Override Layer and Traffic Management Engine
"""

import pytest
from backend.schemas.traffic import TrafficAnalysisRequest
from backend.services.feature_engineering import extract_features
from backend.services.safety_layer import evaluate_safety_override
from backend.services.traffic_management import generate_traffic_recommendation


def test_safety_escalation_on_critical_approach():
    """
    Even if an AI model theoretically predicted 'SAFE',
    the deterministic safety layer MUST escalate to COLLISION_RISK
    when both vehicles are rapidly converging with short TTC and close distance.
    """
    req = TrafficAnalysisRequest(
        distance_a_cm=20.0,
        speed_a_kmh=35.0,
        vehicle_count_a=1,
        distance_b_cm=20.0,
        speed_b_kmh=35.0,
        vehicle_count_b=1
    )
    features = extract_features(req)

    # Force simulated naive AI output "SAFE"
    safety = evaluate_safety_override("SAFE", features)

    assert safety.final_safety_risk == "COLLISION_RISK"
    assert safety.override_applied is True
    assert "Deterministic Safety Override" in safety.override_reason
    assert safety.warning_level == "COLLISION_RISK"


def test_traffic_management_safe_corridor():
    """When conditions are SAFE, both sides receive PROCEED."""
    req = TrafficAnalysisRequest(
        distance_a_cm=150.0,
        speed_a_kmh=0.0,
        vehicle_count_a=0,
        distance_b_cm=150.0,
        speed_b_kmh=0.0,
        vehicle_count_b=0
    )
    features = extract_features(req)
    safety = evaluate_safety_override("SAFE", features)
    rec = generate_traffic_recommendation(features, safety)

    assert rec.side_a_action == "PROCEED"
    assert rec.side_b_action == "PROCEED"
    assert "NORMAL TRAFFIC FLOW" in rec.recommendation_summary


def test_traffic_management_single_approach_priority():
    """Side A approaching while Side B is clear: Side A proceeds with caution, Side B waits."""
    req = TrafficAnalysisRequest(
        distance_a_cm=45.0,
        speed_a_kmh=12.0,
        vehicle_count_a=1,
        distance_b_cm=100.0,
        speed_b_kmh=0.0,
        vehicle_count_b=0
    )
    features = extract_features(req)
    safety = evaluate_safety_override("CAUTION", features)
    rec = generate_traffic_recommendation(features, safety)

    assert rec.side_a_action == "PROCEED WITH CAUTION"
    assert rec.side_b_action == "WAIT"
    assert len(rec.contributing_factors) >= 2


def test_traffic_management_collision_risk_both_wait():
    """Imminent collision condition forces both sides to WAIT."""
    req = TrafficAnalysisRequest(
        distance_a_cm=20.0,
        speed_a_kmh=30.0,
        vehicle_count_a=1,
        distance_b_cm=20.0,
        speed_b_kmh=30.0,
        vehicle_count_b=1
    )
    features = extract_features(req)
    safety = evaluate_safety_override("COLLISION_RISK", features)
    rec = generate_traffic_recommendation(features, safety)

    assert rec.side_a_action == "WAIT"
    assert rec.side_b_action == "WAIT"
    assert "CRITICAL STOP" in rec.recommendation_summary
