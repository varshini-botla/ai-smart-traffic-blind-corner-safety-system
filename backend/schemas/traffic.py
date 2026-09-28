"""
Pydantic Schemas for Traffic Analysis Input, Feature Engineering,
AI Prediction, Deterministic Safety Layer, and Traffic Management Recommendation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator


class TrafficAnalysisRequest(BaseModel):
    """
    Validated request schema for blind corner traffic analysis.
    Explicitly enforces physical constraints:
      - distance > 0 (realistic physical distance up to 5000 cm)
      - speed >= 0 (supports both cm/s and km/h inputs)
      - vehicle_count >= 0
    """
    distance_a_cm: float = Field(
        ...,
        description="Side A distance to conflict point in centimeters. Must be > 0."
    )
    distance_b_cm: float = Field(
        ...,
        description="Side B distance to conflict point in centimeters. Must be > 0."
    )
    speed_a_kmh: Optional[float] = Field(
        default=None,
        description="Side A approach speed in km/h. Must be >= 0."
    )
    speed_b_kmh: Optional[float] = Field(
        default=None,
        description="Side B approach speed in km/h. Must be >= 0."
    )
    speed_a_cms: Optional[float] = Field(
        default=None,
        description="Side A approach speed in cm/s. Must be >= 0."
    )
    speed_b_cms: Optional[float] = Field(
        default=None,
        description="Side B approach speed in cm/s. Must be >= 0."
    )
    vehicle_count_a: int = Field(
        default=1,
        description="Side A vehicle count. Must be integer >= 0."
    )
    vehicle_count_b: int = Field(
        default=1,
        description="Side B vehicle count. Must be integer >= 0."
    )

    source: str = Field(
        default="User Provided Traffic Data",
        description="Data provenance label"
    )

    prev_distance_a_cm: Optional[float] = Field(
        default=None,
        description="Previous distance reading for Side A to compute distance delta"
    )
    prev_distance_b_cm: Optional[float] = Field(
        default=None,
        description="Previous distance reading for Side B to compute distance delta"
    )

    @model_validator(mode="before")
    @classmethod
    def harmonize_speed_inputs(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        # Harmonize Side A speed
        has_kmh_a = values.get("speed_a_kmh") is not None
        has_cms_a = values.get("speed_a_cms") is not None

        if has_cms_a and not has_kmh_a:
            cms = float(values["speed_a_cms"])
            values["speed_a_kmh"] = round(cms * 0.036, 2)
        elif has_kmh_a and not has_cms_a:
            kmh = float(values["speed_a_kmh"])
            # If kmh is passed as a prototype value e.g. 13 kmh or 13 cm/s
            values["speed_a_cms"] = round(kmh, 2)
        elif not has_kmh_a and not has_cms_a:
            values["speed_a_kmh"] = 0.0
            values["speed_a_cms"] = 0.0

        # Harmonize Side B speed
        has_kmh_b = values.get("speed_b_kmh") is not None
        has_cms_b = values.get("speed_b_cms") is not None

        if has_cms_b and not has_kmh_b:
            cms = float(values["speed_b_cms"])
            values["speed_b_kmh"] = round(cms * 0.036, 2)
        elif has_kmh_b and not has_cms_b:
            kmh = float(values["speed_b_kmh"])
            values["speed_b_cms"] = round(kmh, 2)
        elif not has_kmh_b and not has_cms_b:
            values["speed_b_kmh"] = 0.0
            values["speed_b_cms"] = 0.0

        return values

    @field_validator("distance_a_cm", "distance_b_cm")
    @classmethod
    def validate_distance(cls, v: float, info) -> float:
        if v <= 0.0:
            raise ValueError(f"{info.field_name} must be strictly greater than 0 cm.")
        if v > 10000.0:
            raise ValueError(f"{info.field_name} exceeds reasonable blind-corner range (max 10000 cm).")
        return round(float(v), 2)

    @field_validator("speed_a_kmh", "speed_b_kmh", "speed_a_cms", "speed_b_cms")
    @classmethod
    def validate_speed(cls, v: Optional[float], info) -> Optional[float]:
        if v is not None and v < 0.0:
            raise ValueError(f"{info.field_name} cannot be negative.")
        if v is not None and v > 500.0:
            raise ValueError(f"{info.field_name} exceeds maximum speed boundary.")
        return round(float(v), 2) if v is not None else None

    @field_validator("vehicle_count_a", "vehicle_count_b")
    @classmethod
    def validate_vehicle_count(cls, v: int, info) -> int:
        if v < 0:
            raise ValueError(f"{info.field_name} cannot be negative.")
        if v > 100:
            raise ValueError(f"{info.field_name} exceeds realistic approach queue (max 100 vehicles).")
        return int(v)


class EngineeredFeatures(BaseModel):
    """Derived physical and mathematical traffic features."""
    distance_a_cm: float
    distance_b_cm: float
    speed_a_kmh: float
    speed_b_kmh: float
    speed_a_cms: float
    speed_b_cms: float
    vehicle_count_a: int
    vehicle_count_b: int
    total_vehicles: int
    traffic_density: str  # LOW, MEDIUM, HIGH
    ttc_a_seconds: Optional[float] = None
    ttc_b_seconds: Optional[float] = None
    ttc_a_display: str
    ttc_b_display: str
    stopping_dist_a_cm: float = 0.0
    stopping_dist_b_cm: float = 0.0
    simultaneous_vehicle_presence: bool
    simultaneous_approach: bool
    relative_urgency: str  # SIDE_A_URGENT, SIDE_B_URGENT, EQUAL_URGENT, NEITHER
    relative_arrival_time_diff_sec: Optional[float] = None
    distance_change_a_cm: Optional[float] = None
    distance_change_b_cm: Optional[float] = None
    conflict_potential: str  # NONE, LOW, MODERATE, CRITICAL


class AIPredictionResult(BaseModel):
    """Machine learning model probabilistic inference output."""
    predicted_risk: str  # SAFE, CAUTION, HIGH_RISK, COLLISION_RISK
    confidence_score: float
    class_probabilities: Dict[str, float]
    model_name: str
    model_version: str
    feature_contributions: Dict[str, float]


class SafetyAssessmentResult(BaseModel):
    """Deterministic safety escalation output."""
    final_safety_risk: str
    override_applied: bool
    override_reason: Optional[str] = None
    warning_level: str
    warning_message: str


class TrafficRecommendationResult(BaseModel):
    """Traffic management directives and factor-grounded explanations."""
    side_a_action: str  # PROCEED, WAIT, PROCEED WITH CAUTION
    side_b_action: str  # PROCEED, WAIT, PROCEED WITH CAUTION
    recommendation_summary: str
    primary_reason: str
    contributing_factors: List[str]


class TrafficAnalysisResponse(BaseModel):
    """Unified API response for traffic condition analysis."""
    id: Optional[int] = None
    timestamp: str
    source: str
    input: Dict[str, Any]
    features: EngineeredFeatures
    ai_prediction: AIPredictionResult
    safety_assessment: SafetyAssessmentResult
    traffic_recommendation: TrafficRecommendationResult
