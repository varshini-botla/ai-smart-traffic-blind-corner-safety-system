"""
Train Random Forest Classifier for Blind-Corner Traffic Collision Risk Prediction
Uses genuine train/test evaluation on held-out test data.
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from ai.preprocessing import FEATURE_COLUMNS, RISK_CLASSES, TARGET_COLUMN

CURRENT_DIR = Path(__file__).resolve().parent
DATASET_PATH = CURRENT_DIR / "dataset" / "blind_corner_traffic_dataset.csv"
MODEL_DIR = CURRENT_DIR / "models"
MODEL_FILE = MODEL_DIR / "risk_model.joblib"
METADATA_FILE = MODEL_DIR / "model_metadata.json"


def train_and_evaluate(dataset_path: Path = DATASET_PATH) -> dict:
    """
    Execute full training and genuine evaluation pipeline.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Training dataset not found at {dataset_path}")

    # 1. Load data
    df = pd.read_csv(dataset_path)
    print(f"Loaded dataset: {len(df)} samples from {dataset_path.name}")

    # 2. Validate columns
    missing_features = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing_features:
        raise ValueError(f"Missing required feature columns: {missing_features}")
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")

    # 3. Features & Target
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # 4. Train / Test Split (Held-out 20% test set for genuine evaluation)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train split: {len(X_train)} samples | Test split: {len(X_test)} samples")

    # 5. Train Random Forest Classifier with balanced class weights
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    # 6. Predict on held-out test data
    y_pred = rf.predict(X_test)
    y_proba = rf.predict_proba(X_test)

    # 7. Genuine Metric Calculations
    acc = float(accuracy_score(y_test, y_pred))
    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    prec_weighted = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    rec_weighted = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    # Confusion Matrix mapped to RISK_CLASSES order
    conf_mat = confusion_matrix(y_test, y_pred, labels=RISK_CLASSES).tolist()

    # Per-class metrics
    class_report_dict = classification_report(
        y_test, y_pred, labels=RISK_CLASSES, output_dict=True, zero_division=0
    )

    # Feature Importances
    importances = {
        col: round(float(imp), 4)
        for col, imp in zip(FEATURE_COLUMNS, rf.feature_importances_)
    }
    # Sort feature importances descending
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

    # 8. Compile Metadata
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "model_name": "Random Forest Classifier",
        "model_version": "1.0.0",
        "algorithm": "sklearn.ensemble.RandomForestClassifier",
        "parameters": {
            "n_estimators": 100,
            "max_depth": 12,
            "class_weight": "balanced",
            "random_state": 42,
        },
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset_name": "blind_corner_traffic_dataset.csv",
        "dataset_type": "Synthetic Kinematic Development Dataset",
        "academic_disclaimer": "Academic decision-support prototype. Not certified for autonomous or real-world traffic control.",
        "sample_counts": {
            "total_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        },
        "feature_columns": FEATURE_COLUMNS,
        "classes": RISK_CLASSES,
        "metrics": {
            "accuracy": round(acc, 4),
            "precision_macro": round(prec_macro, 4),
            "recall_macro": round(rec_macro, 4),
            "f1_macro": round(f1_macro, 4),
            "precision_weighted": round(prec_weighted, 4),
            "recall_weighted": round(rec_weighted, 4),
            "f1_weighted": round(f1_weighted, 4),
        },
        "confusion_matrix": {
            "labels": RISK_CLASSES,
            "matrix": conf_mat,
        },
        "per_class_metrics": {
            cls: {
                "precision": round(class_report_dict[cls]["precision"], 4),
                "recall": round(class_report_dict[cls]["recall"], 4),
                "f1_score": round(class_report_dict[cls]["f1-score"], 4),
                "support": int(class_report_dict[cls]["support"]),
            }
            for cls in RISK_CLASSES
            if cls in class_report_dict
        },
        "feature_importances": sorted_importances,
    }

    # 9. Save Model and Metadata
    joblib.dump(rf, MODEL_FILE)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 50)
    print("MODEL TRAINING & EVALUATION REPORT")
    print("=" * 50)
    print(f"Accuracy:           {metadata['metrics']['accuracy'] * 100:.2f}%")
    print(f"F1-Score (Macro):   {metadata['metrics']['f1_macro']:.4f}")
    print(f"F1-Score (Weighted):{metadata['metrics']['f1_weighted']:.4f}")
    print(f"Precision (Macro):  {metadata['metrics']['precision_macro']:.4f}")
    print(f"Recall (Macro):     {metadata['metrics']['recall_macro']:.4f}")
    print("\nTop 5 Contributing Features:")
    for feat, val in list(sorted_importances.items())[:5]:
        print(f"  - {feat}: {val:.4f}")
    print(f"\nModel saved to:    {MODEL_FILE}")
    print(f"Metadata saved to: {METADATA_FILE}")
    print("=" * 50)

    return metadata


if __name__ == "__main__":
    train_and_evaluate()
