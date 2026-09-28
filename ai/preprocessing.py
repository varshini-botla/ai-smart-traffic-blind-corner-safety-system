"""
AI Pipeline Preprocessing and Feature Definitions
"""

from typing import List

# Features used for ML Model Training and Inference
FEATURE_COLUMNS: List[str] = [
    "distance_a_cm",
    "distance_b_cm",
    "speed_a_kmh",
    "speed_b_kmh",
    "vehicle_count_a",
    "vehicle_count_b",
    "total_vehicles",
    "ttc_a_imputed",
    "ttc_b_imputed",
    "simultaneous_presence",
    "simultaneous_approach",
    "arrival_time_diff_imputed",
    "density_encoded",
]

TARGET_COLUMN: str = "risk_label"

# Canonical Risk Classes
RISK_CLASSES: List[str] = [
    "SAFE",
    "CAUTION",
    "HIGH_RISK",
    "COLLISION_RISK"
]
