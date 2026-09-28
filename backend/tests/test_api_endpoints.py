"""
Integration tests for FastAPI REST Endpoints and WebSocket Communication
"""

import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database import connection, repository

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Use temporary SQLite database for test isolation."""
    test_db = tmp_path / "test_api.db"
    monkeypatch.setattr(connection, "DB_PATH", test_db)
    monkeypatch.setattr(connection, "DATA_DIR", tmp_path)
    connection.init_db()
    yield test_db


def test_analyze_traffic_valid_flow():
    """Test POST /api/analyze end-to-end processing pipeline."""
    payload = {
        "distance_a_cm": 35.0,
        "speed_a_kmh": 18.0,
        "vehicle_count_a": 1,
        "distance_b_cm": 40.0,
        "speed_b_kmh": 20.0,
        "vehicle_count_b": 1,
        "source": "User Provided Traffic Data"
    }

    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify input echo
    assert data["input"]["distance_a_cm"] == 35.0
    assert data["source"] == "User Provided Traffic Data"

    # Verify feature engineering
    assert "ttc_a_seconds" in data["features"]
    assert "traffic_density" in data["features"]

    # Verify genuine AI prediction
    assert data["ai_prediction"]["predicted_risk"] in ["SAFE", "CAUTION", "HIGH_RISK", "COLLISION_RISK"]
    assert data["ai_prediction"]["confidence_score"] >= 0.0

    # Verify deterministic safety assessment
    assert data["safety_assessment"]["final_safety_risk"] in ["SAFE", "CAUTION", "HIGH_RISK", "COLLISION_RISK"]
    assert "warning_message" in data["safety_assessment"]

    # Verify traffic management recommendations
    assert data["traffic_recommendation"]["side_a_action"] in ["PROCEED", "PROCEED WITH CAUTION", "WAIT"]
    assert data["traffic_recommendation"]["side_b_action"] in ["PROCEED", "PROCEED WITH CAUTION", "WAIT"]
    assert len(data["traffic_recommendation"]["contributing_factors"]) > 0


def test_analyze_traffic_validation_rejection():
    """Negative speeds or distances must return 422 with validation errors."""
    invalid_payload = {
        "distance_a_cm": -10.0,
        "speed_a_kmh": 20.0,
        "vehicle_count_a": 1,
        "distance_b_cm": 40.0,
        "speed_b_kmh": 20.0,
        "vehicle_count_b": 1
    }
    response = client.post("/api/analyze", json=invalid_payload)
    assert response.status_code == 422


def test_get_current_status_endpoint():
    """Verify /api/current-status before and after analysis."""
    # Before analysis
    resp1 = client.get("/api/current-status")
    assert resp1.status_code == 200
    assert resp1.json()["has_active_state"] is False

    # Perform analysis
    client.post("/api/analyze", json={
        "distance_a_cm": 100.0,
        "speed_a_kmh": 0.0,
        "vehicle_count_a": 0,
        "distance_b_cm": 100.0,
        "speed_b_kmh": 0.0,
        "vehicle_count_b": 0
    })

    # After analysis
    resp2 = client.get("/api/current-status")
    assert resp2.status_code == 200
    assert resp2.json()["has_active_state"] is True
    assert resp2.json()["state"]["final_risk"] == "SAFE"


def test_get_history_and_analytics_endpoints():
    """Verify /api/history and /api/analytics endpoints."""
    # Analyze an event
    client.post("/api/analyze", json={
        "distance_a_cm": 30.0,
        "speed_a_kmh": 25.0,
        "vehicle_count_a": 1,
        "distance_b_cm": 30.0,
        "speed_b_kmh": 25.0,
        "vehicle_count_b": 1
    })

    # History
    hist_resp = client.get("/api/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["total"] >= 1
    assert len(hist_data["events"]) >= 1

    # Analytics
    analytics_resp = client.get("/api/analytics")
    assert analytics_resp.status_code == 200
    analytics_data = analytics_resp.json()
    assert analytics_data["total_events"] >= 1
    assert analytics_data["has_data"] is True


def test_get_model_info_endpoint():
    """Verify /api/model-info returns authentic model metrics."""
    resp = client.get("/api/model-info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_name"] == "Random Forest Classifier"
    assert "metrics" in data
    assert "accuracy" in data["metrics"]
    assert "confusion_matrix" in data
    assert "feature_importances" in data


def test_websocket_connection():
    """Verify WebSocket connection and message stream."""
    with client.websocket_connect("/ws/traffic") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "CONNECTION_ESTABLISHED"
