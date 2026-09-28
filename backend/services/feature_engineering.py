"""
Feature Engineering and Mathematical TTC Calculation Service
"""

from typing import Tuple, Optional, Dict, Any
import numpy as np
from backend.schemas.traffic import TrafficAnalysisRequest, EngineeredFeatures

# Friction and gravity constants
KMH_TO_CMS = 250.0 / 9.0  # 1 km/h = 27.7778 cm/s
MU_FRICTION = 0.70
G_GRAVITY = 980.0  # cm/s^2
STOP_DENOM = 2 * MU_FRICTION * G_GRAVITY  # 1372 cm/s^2


def compute_stopping_distance(speed_cms: float) -> float:
    """Calculate braking stopping distance in cm using v^2 / (2 * mu * g)."""
    if speed_cms <= 0:
        return 0.0
    return round((speed_cms ** 2) / STOP_DENOM, 2)


def calculate_ttc(distance_cm: float, speed_cms: float) -> Tuple[Optional[float], str]:
    """
    Calculate estimated Time-To-Collision (TTC) mathematically.
    Formula: TTC = distance / speed
    
    Examples:
      - distance = 74 cm, speed = 13 cm/s -> TTC = 5.7s
      - distance = 40 cm, speed = 15 cm/s -> TTC = 2.7s
      - distance = 10 cm, speed = 0 cm/s  -> CRITICAL (<1s)
      - distance = 100 cm, speed = 0 cm/s -> None (Stationary / Clear)
    """
    if distance_cm <= 0.0:
        return None, "Invalid distance"

    if speed_cms <= 0.0:
        if distance_cm <= 20.0:
            return 0.5, "CRITICAL (<1s)"
        return None, "Stationary / Clear"

    ttc_seconds = distance_cm / speed_cms

    if ttc_seconds < 1.0 or distance_cm <= 15.0:
        return round(ttc_seconds, 2), "CRITICAL (<1s)"

    if ttc_seconds > 120.0:
        return round(ttc_seconds, 2), f"{round(ttc_seconds, 1)} s (Low approach speed)"

    return round(ttc_seconds, 2), f"{round(ttc_seconds, 1)} s"


def calculate_traffic_density(
    count_a: int,
    count_b: int,
    dist_a_cm: float,
    dist_b_cm: float
) -> str:
    """
    Deterministically calculate traffic density category based on documented queue thresholds.
    """
    total = count_a + count_b
    if total <= 1:
        return "LOW"
    elif total <= 4:
        if (dist_a_cm <= 35.0 and count_a >= 1) and (dist_b_cm <= 35.0 and count_b >= 1):
            return "HIGH"
        return "MEDIUM"
    else:
        return "HIGH"


def calculate_relative_urgency(
    ttc_a: Optional[float],
    ttc_b: Optional[float],
    speed_a: float,
    speed_b: float,
    count_a: int,
    count_b: int
) -> str:
    """
    Determine which side has the higher immediate approach urgency.
    """
    has_a = count_a > 0 and speed_a > 0 and ttc_a is not None
    has_b = count_b > 0 and speed_b > 0 and ttc_b is not None

    if has_a and has_b:
        diff = abs(ttc_a - ttc_b)
        max_ttc = max(ttc_a, ttc_b)
        ratio_diff = (diff / max_ttc) if max_ttc > 0 else 0.0
        if diff <= 1.0 or ratio_diff <= 0.15:
            return "EQUAL_URGENT"
        elif ttc_a < ttc_b:
            return "SIDE_A_URGENT"
        else:
            return "SIDE_B_URGENT"
    elif has_a:
        return "SIDE_A_URGENT"
    elif has_b:
        return "SIDE_B_URGENT"
    else:
        return "NEITHER"


def calculate_conflict_potential(
    dist_a: float,
    dist_b: float,
    speed_a: float,
    speed_b: float,
    ttc_a: Optional[float],
    ttc_b: Optional[float],
    count_a: int,
    count_b: int
) -> str:
    """
    Physical conflict potential evaluation based on approach kinematics.
    """
    if count_a == 0 and count_b == 0:
        return "NONE"

    if ttc_a is not None and ttc_b is not None:
        arrival_window = abs(ttc_a - ttc_b)
        if (ttc_a <= 2.5 and ttc_b <= 2.5) and arrival_window <= 1.5:
            return "CRITICAL"
        elif (ttc_a <= 5.0 or ttc_b <= 5.0) and arrival_window <= 3.0:
            return "MODERATE"
        else:
            return "LOW"
    elif ttc_a is not None or ttc_b is not None:
        active_ttc = ttc_a if ttc_a is not None else ttc_b
        if active_ttc <= 2.5:
            return "MODERATE"
        return "LOW"

    return "NONE"


def extract_features(request: TrafficAnalysisRequest) -> EngineeredFeatures:
    """
    Primary Feature Engineering pipeline.
    Transforms raw inputs into rich physical, kinematic, and spatial features.
    """
    speed_a = request.speed_a_cms if request.speed_a_cms is not None else (request.speed_a_kmh or 0.0)
    speed_b = request.speed_b_cms if request.speed_b_cms is not None else (request.speed_b_kmh or 0.0)

    # TTC calculations
    ttc_a_val, ttc_a_disp = calculate_ttc(request.distance_a_cm, speed_a)
    ttc_b_val, ttc_b_disp = calculate_ttc(request.distance_b_cm, speed_b)

    # Stopping distances
    stop_dist_a = compute_stopping_distance(speed_a)
    stop_dist_b = compute_stopping_distance(speed_b)

    # Indicators
    simul_presence = (request.vehicle_count_a > 0 and request.vehicle_count_b > 0)
    simul_approach = (
        request.vehicle_count_a > 0 and request.vehicle_count_b > 0 and
        speed_a > 0.0 and speed_b > 0.0
    )

    rel_arrival_diff = None
    if ttc_a_val is not None and ttc_b_val is not None:
        rel_arrival_diff = round(abs(ttc_a_val - ttc_b_val), 2)

    density = calculate_traffic_density(
        request.vehicle_count_a,
        request.vehicle_count_b,
        request.distance_a_cm,
        request.distance_b_cm
    )

    urgency = calculate_relative_urgency(
        ttc_a_val,
        ttc_b_val,
        speed_a,
        speed_b,
        request.vehicle_count_a,
        request.vehicle_count_b
    )

    dist_change_a = None
    if request.prev_distance_a_cm is not None:
        dist_change_a = round(request.distance_a_cm - request.prev_distance_a_cm, 2)

    dist_change_b = None
    if request.prev_distance_b_cm is not None:
        dist_change_b = round(request.distance_b_cm - request.prev_distance_b_cm, 2)

    conflict = calculate_conflict_potential(
        request.distance_a_cm,
        request.distance_b_cm,
        speed_a,
        speed_b,
        ttc_a_val,
        ttc_b_val,
        request.vehicle_count_a,
        request.vehicle_count_b
    )

    return EngineeredFeatures(
        distance_a_cm=request.distance_a_cm,
        distance_b_cm=request.distance_b_cm,
        speed_a_kmh=round(speed_a * 0.036, 2) if speed_a > 0 else 0.0,
        speed_b_kmh=round(speed_b * 0.036, 2) if speed_b > 0 else 0.0,
        speed_a_cms=speed_a,
        speed_b_cms=speed_b,
        vehicle_count_a=request.vehicle_count_a,
        vehicle_count_b=request.vehicle_count_b,
        total_vehicles=request.vehicle_count_a + request.vehicle_count_b,
        traffic_density=density,
        ttc_a_seconds=ttc_a_val,
        ttc_b_seconds=ttc_b_val,
        ttc_a_display=ttc_a_disp,
        ttc_b_display=ttc_b_disp,
        stopping_dist_a_cm=stop_dist_a,
        stopping_dist_b_cm=stop_dist_b,
        simultaneous_vehicle_presence=simul_presence,
        simultaneous_approach=simul_approach,
        relative_urgency=urgency,
        relative_arrival_time_diff_sec=rel_arrival_diff,
        distance_change_a_cm=dist_change_a,
        distance_change_b_cm=dist_change_b,
        conflict_potential=conflict
    )


MODEL_FEATURE_NAMES = [
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


def features_to_ml_dict(features: EngineeredFeatures) -> Dict[str, float]:
    """
    Format engineered features into numerical vector for ML model inference.
    """
    density_map = {"LOW": 0.0, "MEDIUM": 1.0, "HIGH": 2.0}
    density_val = density_map.get(features.traffic_density, 0.0)

    ttc_a_clean = features.ttc_a_seconds if features.ttc_a_seconds is not None else 99.0
    ttc_b_clean = features.ttc_b_seconds if features.ttc_b_seconds is not None else 99.0
    arr_diff_clean = features.relative_arrival_time_diff_sec if features.relative_arrival_time_diff_sec is not None else 99.0

    return {
        "distance_a_cm": float(features.distance_a_cm),
        "distance_b_cm": float(features.distance_b_cm),
        "speed_a_kmh": float(features.speed_a_cms),  # Speed value
        "speed_b_kmh": float(features.speed_b_cms),
        "vehicle_count_a": float(features.vehicle_count_a),
        "vehicle_count_b": float(features.vehicle_count_b),
        "total_vehicles": float(features.total_vehicles),
        "ttc_a_imputed": float(ttc_a_clean),
        "ttc_b_imputed": float(ttc_b_clean),
        "simultaneous_presence": 1.0 if features.simultaneous_vehicle_presence else 0.0,
        "simultaneous_approach": 1.0 if features.simultaneous_approach else 0.0,
        "arrival_time_diff_imputed": float(arr_diff_clean),
        "density_encoded": density_val,
    }
