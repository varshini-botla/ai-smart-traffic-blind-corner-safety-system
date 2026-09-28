"""
Unit tests for Input Validation (Pydantic Schemas)
"""

import pytest
from pydantic import ValidationError
from backend.schemas.traffic import TrafficAnalysisRequest


def test_valid_traffic_request():
    """Verify standard valid inputs pass validation with correct field parsing."""
    payload = {
        "distance_a_cm": 30.0,
        "speed_a_kmh": 20.0,
        "vehicle_count_a": 1,
        "distance_b_cm": 60.0,
        "speed_b_kmh": 10.0,
        "vehicle_count_b": 1,
        "source": "User Provided Traffic Data"
    }
    req = TrafficAnalysisRequest(**payload)
    assert req.distance_a_cm == 30.0
    assert req.speed_a_kmh == 20.0
    assert req.vehicle_count_a == 1
    assert req.distance_b_cm == 60.0
    assert req.speed_b_kmh == 10.0
    assert req.vehicle_count_b == 1
    assert req.source == "User Provided Traffic Data"


def test_zero_distance_rejected():
    """Distance <= 0 must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        TrafficAnalysisRequest(
            distance_a_cm=0.0,
            speed_a_kmh=15.0,
            vehicle_count_a=1,
            distance_b_cm=50.0,
            speed_b_kmh=15.0,
            vehicle_count_b=1
        )
    assert "distance_a_cm must be strictly greater than 0 cm" in str(exc_info.value)


def test_negative_distance_rejected():
    """Negative distance must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        TrafficAnalysisRequest(
            distance_a_cm=-25.0,
            speed_a_kmh=15.0,
            vehicle_count_a=1,
            distance_b_cm=50.0,
            speed_b_kmh=15.0,
            vehicle_count_b=1
        )
    assert "distance_a_cm must be strictly greater than 0 cm" in str(exc_info.value)


def test_negative_speed_rejected():
    """Negative approach speed must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        TrafficAnalysisRequest(
            distance_a_cm=50.0,
            speed_a_kmh=-10.0,
            vehicle_count_a=1,
            distance_b_cm=50.0,
            speed_b_kmh=15.0,
            vehicle_count_b=1
        )
    assert "speed_a_kmh cannot be negative" in str(exc_info.value)


def test_negative_vehicle_count_rejected():
    """Negative vehicle count must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        TrafficAnalysisRequest(
            distance_a_cm=50.0,
            speed_a_kmh=10.0,
            vehicle_count_a=-1,
            distance_b_cm=50.0,
            speed_b_kmh=15.0,
            vehicle_count_b=1
        )
    assert "vehicle_count_a cannot be negative" in str(exc_info.value)


def test_zero_speed_and_zero_count_accepted():
    """Zero speed (stopped vehicle) and zero vehicle count (empty road) are valid physical states."""
    req = TrafficAnalysisRequest(
        distance_a_cm=100.0,
        speed_a_kmh=0.0,
        vehicle_count_a=0,
        distance_b_cm=100.0,
        speed_b_kmh=0.0,
        vehicle_count_b=0
    )
    assert req.speed_a_kmh == 0.0
    assert req.vehicle_count_a == 0


def test_unreasonable_values_rejected():
    """Extreme out-of-range values must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        TrafficAnalysisRequest(
            distance_a_cm=500000.0,  # 5 km away from blind corner
            speed_a_kmh=20.0,
            vehicle_count_a=1,
            distance_b_cm=50.0,
            speed_b_kmh=15.0,
            vehicle_count_b=1
        )
    assert "exceeds reasonable blind-corner range" in str(exc_info.value)
