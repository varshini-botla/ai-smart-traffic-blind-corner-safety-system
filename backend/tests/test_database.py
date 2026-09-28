"""
Unit tests for SQLite Database operations
"""

import os
import tempfile
from pathlib import Path
import pytest
from backend.database import connection, repository


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Use a temporary database for testing to ensure isolation."""
    test_db = tmp_path / "test_traffic.db"
    monkeypatch.setattr(connection, "DB_PATH", test_db)
    monkeypatch.setattr(connection, "DATA_DIR", tmp_path)
    connection.init_db()
    yield test_db


def test_init_db_creates_table():
    """Verify that init_db creates the traffic_events table properly."""
    conn = connection.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traffic_events'")
    assert cursor.fetchone() is not None
    conn.close()


def test_insert_and_retrieve_event():
    """Test inserting a valid traffic event and retrieving it."""
    sample_event = {
        "timestamp": "2026-09-28T10:00:00Z",
        "source": "User Provided Traffic Data",
        "distance_a": 35.0,
        "distance_b": 40.0,
        "speed_a": 18.0,
        "speed_b": 20.0,
        "vehicle_count_a": 1,
        "vehicle_count_b": 1,
        "ttc_a": 7.0,
        "ttc_b": 7.2,
        "traffic_density": "MEDIUM",
        "ai_risk": "HIGH_RISK",
        "final_risk": "COLLISION_RISK",
        "warning": "CRITICAL COLLISION WARNING",
        "side_a_action": "WAIT",
        "side_b_action": "WAIT",
        "recommendation": "SIDE A: WAIT | SIDE B: WAIT",
        "explanation": "Both approaches have low TTC at blind corner.",
        "raw_features": {"ttc_diff": 0.2, "relative_urgency": "HIGH"}
    }

    inserted = repository.insert_event(sample_event)
    assert inserted["id"] == 1
    assert inserted["distance_a"] == 35.0
    assert inserted["final_risk"] == "COLLISION_RISK"
    assert inserted["raw_features"]["relative_urgency"] == "HIGH"

    # Test latest event
    latest = repository.get_latest_event()
    assert latest is not None
    assert latest["id"] == 1

    # Test list events
    events = repository.get_events()
    assert len(events) == 1
    assert events[0]["recommendation"] == "SIDE A: WAIT | SIDE B: WAIT"


def test_analytics_summary():
    """Test genuine calculation of analytics from stored records."""
    # When empty
    empty_summary = repository.get_analytics_summary()
    assert empty_summary["total_events"] == 0
    assert empty_summary["has_data"] is False

    # Insert events
    repository.insert_event({
        "distance_a": 100.0, "distance_b": 100.0,
        "speed_a": 0.0, "speed_b": 0.0,
        "vehicle_count_a": 0, "vehicle_count_b": 0,
        "traffic_density": "LOW",
        "ai_risk": "SAFE", "final_risk": "SAFE",
        "warning": "CLEAR",
        "side_a_action": "PROCEED", "side_b_action": "PROCEED",
        "recommendation": "NORMAL TRAFFIC FLOW",
        "explanation": "No approaching vehicles."
    })
    repository.insert_event({
        "distance_a": 20.0, "distance_b": 30.0,
        "speed_a": 25.0, "speed_b": 20.0,
        "vehicle_count_a": 2, "vehicle_count_b": 1,
        "traffic_density": "HIGH",
        "ai_risk": "COLLISION_RISK", "final_risk": "COLLISION_RISK",
        "warning": "CRITICAL",
        "side_a_action": "WAIT", "side_b_action": "WAIT",
        "recommendation": "BOTH WAIT",
        "explanation": "Imminent conflict."
    })

    summary = repository.get_analytics_summary()
    assert summary["total_events"] == 2
    assert summary["has_data"] is True
    assert summary["risk_distribution"]["SAFE"] == 1
    assert summary["risk_distribution"]["COLLISION_RISK"] == 1
    assert summary["average_speed_a"] == 12.5
    assert summary["average_distance_a"] == 60.0
