"""
Model Inference Service for Real-Time Collision Risk Prediction
Loads trained Random Forest model and generates probabilistic risk predictions.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from ai.preprocessing import FEATURE_COLUMNS, RISK_CLASSES

CURRENT_DIR = Path(__file__).resolve().parent
MODEL_FILE = CURRENT_DIR / "models" / "risk_model.joblib"
METADATA_FILE = CURRENT_DIR / "models" / "model_metadata.json"


class RiskPredictor:
    """
    Thread-safe inference wrapper for Scikit-Learn risk classification model.
    """
    _instance: Optional["RiskPredictor"] = None

    def __init__(self):
        self.model = None
        self.metadata = None
        self._load_model()

    @classmethod
    def get_instance(cls) -> "RiskPredictor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self) -> None:
        """Load joblib model artifact and associated metadata."""
        if not MODEL_FILE.exists():
            raise FileNotFoundError(
                f"Trained model artifact not found at {MODEL_FILE}. "
                "Please run `python ai/train_model.py` first."
            )
        self.model = joblib.load(MODEL_FILE)

        if METADATA_FILE.exists():
            with open(METADATA_FILE, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "model_name": "Random Forest Classifier",
                "model_version": "1.0.0",
                "feature_importances": {}
            }

    def predict(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Execute model inference on engineered numerical feature vector.
        Returns:
            predicted_risk: str
            confidence_score: float (0.0 to 1.0)
            class_probabilities: Dict[str, float]
            feature_contributions: Dict[str, float]
        """
        if self.model is None:
            self._load_model()

        # Build single-row DataFrame with explicit columns in correct order
        input_df = pd.DataFrame([[feature_dict[col] for col in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)

        # Predict class and probabilities
        pred_label = self.model.predict(input_df)[0]
        probas = self.model.predict_proba(input_df)[0]

        # Map probabilities to classes
        classes = list(self.model.classes_)
        prob_dict = {
            cls_name: round(float(probas[classes.index(cls_name)]), 4)
            if cls_name in classes else 0.0
            for cls_name in RISK_CLASSES
        }

        # Genuine confidence is the predicted class's posterior probability
        confidence = float(prob_dict.get(pred_label, max(probas)))

        return {
            "predicted_risk": str(pred_label),
            "confidence_score": round(confidence, 4),
            "class_probabilities": prob_dict,
            "model_name": self.metadata.get("model_name", "Random Forest Classifier"),
            "model_version": self.metadata.get("model_version", "1.0.0"),
            "feature_contributions": self.metadata.get("feature_importances", {})
        }


def predict_risk(feature_dict: Dict[str, float]) -> Dict[str, Any]:
    """Helper functional wrapper for singleton predictor."""
    return RiskPredictor.get_instance().predict(feature_dict)
