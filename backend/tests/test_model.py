"""
Unit tests for AI Model Training, Serialization, and Real-Time Inference
"""

import pytest
from ai.predict import RiskPredictor, predict_risk
from ai.preprocessing import FEATURE_COLUMNS, RISK_CLASSES


def test_model_artifact_loaded():
    """Verify that the Random Forest model and metadata load successfully."""
    predictor = RiskPredictor.get_instance()
    assert predictor.model is not None
    assert predictor.metadata is not None
    assert "metrics" in predictor.metadata
    assert predictor.metadata["metrics"]["accuracy"] > 0.90


def test_predict_safe_scenario():
    """Stationary vehicles / empty road scenario should predict SAFE."""
    safe_vector = {
        "distance_a_cm": 150.0,
        "distance_b_cm": 150.0,
        "speed_a_kmh": 0.0,
        "speed_b_kmh": 0.0,
        "vehicle_count_a": 0.0,
        "vehicle_count_b": 0.0,
        "total_vehicles": 0.0,
        "ttc_a_imputed": 99.0,
        "ttc_b_imputed": 99.0,
        "simultaneous_presence": 0.0,
        "simultaneous_approach": 0.0,
        "arrival_time_diff_imputed": 99.0,
        "density_encoded": 0.0,
    }
    result = predict_risk(safe_vector)
    assert result["predicted_risk"] == "SAFE"
    assert result["confidence_score"] >= 0.50
    assert "SAFE" in result["class_probabilities"]
    assert sum(result["class_probabilities"].values()) == pytest.approx(1.0, abs=0.01)


def test_predict_critical_collision_scenario():
    """Close distances, high approach speeds, near-identical arrival times -> COLLISION_RISK."""
    critical_vector = {
        "distance_a_cm": 25.0,
        "distance_b_cm": 25.0,
        "speed_a_kmh": 35.0,
        "speed_b_kmh": 35.0,
        "vehicle_count_a": 1.0,
        "vehicle_count_b": 1.0,
        "total_vehicles": 2.0,
        "ttc_a_imputed": 0.025,
        "ttc_b_imputed": 0.025,
        "simultaneous_presence": 1.0,
        "simultaneous_approach": 1.0,
        "arrival_time_diff_imputed": 0.0,
        "density_encoded": 1.0,
    }
    result = predict_risk(critical_vector)
    assert result["predicted_risk"] in ["COLLISION_RISK", "HIGH_RISK"]
    assert result["confidence_score"] > 0.60
    assert result["class_probabilities"]["COLLISION_RISK"] > 0.40
