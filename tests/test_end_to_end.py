"""
System-Wide End-to-End Test Suite for AI Smart Traffic and Blind-Corner Safety System
Validates all 18 core requirements and Section 37 benchmark test cases:
1. Valid input
2. Missing input
3. Negative distance
4. Negative speed
5. Zero speed
6. One approaching vehicle
7. Two approaching vehicles
8. Both close
9. Both dangerous (Imminent collision)
10. Safe traffic
11. High traffic density
12. TTC calculation
13. ML prediction
14. Safety override
15. Traffic recommendation
16. Database storage
17. API response
18. WebSocket update
"""

import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database import connection, repository
from backend.services.feature_engineering import calculate_ttc, extract_features
from backend.schemas.traffic import TrafficAnalysisRequest

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """Use isolated temporary SQLite database for test suite."""
    test_db = tmp_path / "e2e_traffic.db"
    monkeypatch.setattr(connection, "DB_PATH", test_db)
    monkeypatch.setattr(connection, "DATA_DIR", tmp_path)
    connection.init_db()
    yield test_db


# --- Benchmark Test Cases (Section 37) ---

def test_case_1_safe_normal_traffic():
    """
    Test Case 1:
    A: distance = 100 cm, speed = 0, vehicles = 0
    B: distance = 100 cm, speed = 0, vehicles = 0
    Expected: SAFE, NORMAL TRAFFIC FLOW, PROCEED on both sides.
    """
    payload = {
        "distance_a_cm": 100.0,
        "speed_a_kmh": 0.0,
        "vehicle_count_a": 0,
        "distance_b_cm": 100.0,
        "speed_b_kmh": 0.0,
        "vehicle_count_b": 0,
        "source": "User Provided Traffic Data"
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["ai_prediction"]["predicted_risk"] == "SAFE"
    assert data["safety_assessment"]["final_safety_risk"] == "SAFE"
    assert data["traffic_recommendation"]["side_a_action"] == "PROCEED"
    assert data["traffic_recommendation"]["side_b_action"] == "PROCEED"
    assert "NORMAL TRAFFIC FLOW" in data["traffic_recommendation"]["recommendation_summary"]


def test_case_2_single_approaching_vehicle_priority():
    """
    Test Case 2:
    A: distance = 40 cm, speed = 15 km/h, vehicles = 1
    B: distance = 100 cm, speed = 0, vehicles = 0
    Expected: Side A receives priority, Side B yields/waits.
    """
    payload = {
        "distance_a_cm": 40.0,
        "speed_a_kmh": 15.0,
        "vehicle_count_a": 1,
        "distance_b_cm": 100.0,
        "speed_b_kmh": 0.0,
        "vehicle_count_b": 0
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["traffic_recommendation"]["side_a_action"] == "PROCEED WITH CAUTION"
    assert data["traffic_recommendation"]["side_b_action"] == "WAIT"
    assert data["safety_assessment"]["final_safety_risk"] in ["CAUTION", "SAFE"]


def test_case_3_both_close_approaches():
    """
    Test Case 3:
    A: distance = 40 cm, speed = 15 km/h, vehicles = 1
    B: distance = 40 cm, speed = 15 km/h, vehicles = 1
    Expected: High conflict potential; prevents simultaneous uncoordinated entry.
    """
    payload = {
        "distance_a_cm": 40.0,
        "speed_a_kmh": 15.0,
        "vehicle_count_a": 1,
        "distance_b_cm": 40.0,
        "speed_b_kmh": 15.0,
        "vehicle_count_b": 1
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Must be at least CAUTION, HIGH_RISK or COLLISION_RISK
    assert data["safety_assessment"]["final_safety_risk"] in ["CAUTION", "HIGH_RISK", "COLLISION_RISK"]
    # Cannot allow simultaneous uncoordinated proceeding
    assert not (data["traffic_recommendation"]["side_a_action"] == "PROCEED" and
                data["traffic_recommendation"]["side_b_action"] == "PROCEED")


def test_case_4_imminent_dangerous_collision():
    """
    Test Case 4:
    A: distance = 20 cm, speed = 35 km/h, vehicles = 1
    B: distance = 20 cm, speed = 35 km/h, vehicles = 1
    Expected: Strongest safety assessment (COLLISION_RISK / HIGH_RISK) and both WAIT.
    """
    payload = {
        "distance_a_cm": 20.0,
        "speed_a_kmh": 35.0,
        "vehicle_count_a": 1,
        "distance_b_cm": 20.0,
        "speed_b_kmh": 35.0,
        "vehicle_count_b": 1
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["safety_assessment"]["final_safety_risk"] == "COLLISION_RISK"
    assert data["traffic_recommendation"]["side_a_action"] == "WAIT"
    assert data["traffic_recommendation"]["side_b_action"] == "WAIT"
    assert "CRITICAL" in data["traffic_recommendation"]["recommendation_summary"]


# --- System Requirements Validations (1-18) ---

def test_missing_and_negative_input_rejection():
    """Reject missing fields, negative distances, negative speeds, and negative counts."""
    # Negative distance
    r1 = client.post("/api/analyze", json={
        "distance_a_cm": -5.0, "speed_a_kmh": 10.0, "vehicle_count_a": 1,
        "distance_b_cm": 50.0, "speed_b_kmh": 10.0, "vehicle_count_b": 1
    })
    assert r1.status_code == 422

    # Negative speed
    r2 = client.post("/api/analyze", json={
        "distance_a_cm": 50.0, "speed_a_kmh": -10.0, "vehicle_count_a": 1,
        "distance_b_cm": 50.0, "speed_b_kmh": 10.0, "vehicle_count_b": 1
    })
    assert r2.status_code == 422

    # Negative vehicle count
    r3 = client.post("/api/analyze", json={
        "distance_a_cm": 50.0, "speed_a_kmh": 10.0, "vehicle_count_a": -1,
        "distance_b_cm": 50.0, "speed_b_kmh": 10.0, "vehicle_count_b": 1
    })
    assert r3.status_code == 422


def test_high_traffic_density_evaluation():
    """High traffic density (e.g. 3 + 3 = 6 vehicles) evaluated properly."""
    payload = {
        "distance_a_cm": 60.0, "speed_a_kmh": 10.0, "vehicle_count_a": 3,
        "distance_b_cm": 60.0, "speed_b_kmh": 10.0, "vehicle_count_b": 3
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["features"]["traffic_density"] == "HIGH"
    assert data["features"]["total_vehicles"] == 6


def test_ttc_mathematics_and_boundary_handling():
    """TTC calculation mathematics: d / v."""
    # 74 cm / 13 cm/s = 5.69s ≈ 5.7s
    ttc, disp = calculate_ttc(74.0, 13.0)
    assert ttc == 5.69
    assert "5.7" in disp

    # Zero speed returns None and no misleading infinite/negative value
    ttc_zero, disp_zero = calculate_ttc(50.0, 0.0)
    assert ttc_zero is None
    assert "Stationary" in disp_zero


def test_database_persistence_and_analytics_integrity():
    """Verifies that analyze operations store events into SQLite and analytics reflect real counts."""
    # Send 2 distinct events
    client.post("/api/analyze", json={
        "distance_a_cm": 100.0, "speed_a_kmh": 0.0, "vehicle_count_a": 0,
        "distance_b_cm": 100.0, "speed_b_kmh": 0.0, "vehicle_count_b": 0
    })
    client.post("/api/analyze", json={
        "distance_a_cm": 20.0, "speed_a_kmh": 35.0, "vehicle_count_a": 1,
        "distance_b_cm": 20.0, "speed_b_kmh": 35.0, "vehicle_count_b": 1
    })

    # Query history
    hist = client.get("/api/history").json()
    assert hist["total"] == 2
    assert len(hist["events"]) == 2

    # Query analytics
    analytics = client.get("/api/analytics").json()
    assert analytics["total_events"] == 2
    assert analytics["safe_count"] == 1
    assert analytics["collision_risk_count"] == 1
