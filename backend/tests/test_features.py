"""
Unit tests for Feature Engineering & Mathematical TTC Calculation
"""

import pytest
from backend.schemas.traffic import TrafficAnalysisRequest
from backend.services.feature_engineering import (
    calculate_ttc,
    calculate_traffic_density,
    calculate_relative_urgency,
    extract_features,
    features_to_ml_dict,
    KMH_TO_CMS
)


def test_ttc_calculation_mathematics():
    """Verify TTC = distance / approach_speed in cm and cm/s."""
    # 74 cm / 13 cm/s = 5.69s ≈ 5.7s
    ttc, disp = calculate_ttc(74.0, 13.0)
    assert ttc == 5.69
    assert "5.7" in disp

    # Zero speed -> No approach motion
    ttc_zero, disp_zero = calculate_ttc(50.0, 0.0)
    assert ttc_zero is None
    assert "Stationary" in disp_zero

    # Negative distance -> Invalid
    ttc_inv, disp_inv = calculate_ttc(-10.0, 20.0)
    assert ttc_inv is None


def test_traffic_density_thresholds():
    """Verify traffic density thresholds LOW, MEDIUM, HIGH."""
    # 0 or 1 vehicle -> LOW
    assert calculate_traffic_density(1, 0, 80.0, 80.0) == "LOW"
    assert calculate_traffic_density(0, 0, 100.0, 100.0) == "LOW"

    # 2 to 4 vehicles -> MEDIUM
    assert calculate_traffic_density(1, 1, 80.0, 80.0) == "MEDIUM"
    assert calculate_traffic_density(2, 2, 80.0, 80.0) == "MEDIUM"

    # >= 5 vehicles -> HIGH
    assert calculate_traffic_density(3, 2, 50.0, 50.0) == "HIGH"


def test_extract_features_pipeline():
    """Verify full feature extraction pipeline."""
    req = TrafficAnalysisRequest(
        distance_a_cm=40.0,
        speed_a_kmh=15.0,
        vehicle_count_a=1,
        distance_b_cm=80.0,
        speed_b_kmh=10.0,
        vehicle_count_b=1,
        prev_distance_a_cm=45.0,
        prev_distance_b_cm=82.0
    )
    features = extract_features(req)

    assert features.distance_a_cm == 40.0
    assert features.speed_a_cms == 15.0
    assert features.simultaneous_vehicle_presence is True
    assert features.simultaneous_approach is True
    assert features.distance_change_a_cm == -5.0  # Approached closer by 5 cm
    assert features.ttc_a_seconds is not None
    assert features.ttc_b_seconds is not None
    # Side A is closer and faster, so Side A has lower TTC and is more urgent
    assert features.relative_urgency == "SIDE_A_URGENT"

    # Convert to ML dict
    ml_dict = features_to_ml_dict(features)
    assert "distance_a_cm" in ml_dict
    assert "ttc_a_imputed" in ml_dict
    assert ml_dict["simultaneous_presence"] == 1.0
    assert ml_dict["simultaneous_approach"] == 1.0
