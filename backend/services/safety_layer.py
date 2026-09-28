"""
Deterministic Safety Validation and Override Layer
Ensures failsafe escalation if machine learning risk predictions underestimate
kinematically dangerous conflict states.
"""

from typing import Tuple, Optional
from backend.schemas.traffic import EngineeredFeatures, SafetyAssessmentResult

# Ordered severity levels
RISK_LEVEL_ORDER = {
    "SAFE": 0,
    "CAUTION": 1,
    "HIGH_RISK": 2,
    "COLLISION_RISK": 3
}

RISK_LEVEL_REVERSE = {v: k for k, v in RISK_LEVEL_ORDER.items()}


def evaluate_safety_override(
    ai_predicted_risk: str,
    features: EngineeredFeatures
) -> SafetyAssessmentResult:
    """
    Deterministic safety validation layer.
    Enforces that physical laws (proximity threshold, stopping distance, critical TTC, simultaneous arrival)
    act as a hard safety boundary over AI model predictions.
    
    The safety layer can only ESCALATE risk, never de-escalate safety criticality.
    """
    current_level = RISK_LEVEL_ORDER.get(ai_predicted_risk, 0)
    escalated_level = current_level
    override_applied = False
    override_reason: Optional[str] = None

    # Condition 0: Critical Proximity Conflict Envelope (Both vehicles at or near corner <= 22cm)
    if features.distance_a_cm <= 22.0 and features.distance_b_cm <= 22.0:
        if escalated_level < RISK_LEVEL_ORDER["COLLISION_RISK"]:
            escalated_level = RISK_LEVEL_ORDER["COLLISION_RISK"]
            override_applied = True
            override_reason = (
                "Deterministic Safety Override: Both vehicles detected in critical blind-corner "
                f"intersection envelope (Side A: {features.distance_a_cm}cm, Side B: {features.distance_b_cm}cm). "
                "Immediate collision hazard requires dual emergency stop."
            )

    # Condition 1: Imminent Dual Conflict Point Collision (Kinematic TTC < 2.0s)
    elif features.simultaneous_approach:
        ttc_a = features.ttc_a_seconds or 99.0
        ttc_b = features.ttc_b_seconds or 99.0
        arr_diff = features.relative_arrival_time_diff_sec if features.relative_arrival_time_diff_sec is not None else 99.0
        min_ttc = min(ttc_a, ttc_b)

        if (min_ttc <= 2.0 and arr_diff <= 1.5) or \
           (features.distance_a_cm <= 25.0 and features.distance_b_cm <= 25.0 and arr_diff <= 1.2):
            if escalated_level < RISK_LEVEL_ORDER["COLLISION_RISK"]:
                escalated_level = RISK_LEVEL_ORDER["COLLISION_RISK"]
                override_applied = True
                override_reason = (
                    "Deterministic Safety Override: Both vehicles approaching blind corner with critical "
                    f"TTC (A: {ttc_a}s, B: {ttc_b}s) and near-simultaneous arrival window ({arr_diff}s)."
                )

        elif (min_ttc <= 4.0 and arr_diff <= 2.5) or (ttc_a <= 3.5 and ttc_b <= 3.5):
            if escalated_level < RISK_LEVEL_ORDER["HIGH_RISK"]:
                escalated_level = RISK_LEVEL_ORDER["HIGH_RISK"]
                override_applied = True
                override_reason = (
                    "Deterministic Safety Override: Close arrival convergence at blind corner "
                    f"(Arrival time gap: {arr_diff}s)."
                )

    # Condition 2: Active vehicle in blind corner zone while opposing vehicle approaches
    elif (features.distance_a_cm <= 15.0 and features.distance_b_cm <= 35.0 and features.speed_b_cms > 0) or \
         (features.distance_b_cm <= 15.0 and features.distance_a_cm <= 35.0 and features.speed_a_cms > 0):
        if escalated_level < RISK_LEVEL_ORDER["COLLISION_RISK"]:
            escalated_level = RISK_LEVEL_ORDER["COLLISION_RISK"]
            override_applied = True
            override_reason = "Deterministic Safety Override: Vehicle in blind corner zone while opposing vehicle approaches."

    # Condition 3: High approach speed at short distance with blind approach presence
    if features.vehicle_count_a > 0 and features.speed_a_cms >= 25.0 and features.distance_a_cm <= 25.0 and features.vehicle_count_b > 0:
        if escalated_level < RISK_LEVEL_ORDER["HIGH_RISK"]:
            escalated_level = RISK_LEVEL_ORDER["HIGH_RISK"]
            override_applied = True
            override_reason = "Deterministic Safety Override: High approach speed at short distance with active blind-side queue."

    if features.vehicle_count_b > 0 and features.speed_b_cms >= 25.0 and features.distance_b_cm <= 25.0 and features.vehicle_count_a > 0:
        if escalated_level < RISK_LEVEL_ORDER["HIGH_RISK"]:
            escalated_level = RISK_LEVEL_ORDER["HIGH_RISK"]
            override_applied = True
            override_reason = "Deterministic Safety Override: High approach speed at short distance with active blind-side queue."

    # Condition 4: Active vehicle approaching blind corner within 40 cm
    if (features.speed_a_cms > 0 or features.speed_b_cms > 0) and (features.distance_a_cm <= 40.0 or features.distance_b_cm <= 40.0):
        if escalated_level < RISK_LEVEL_ORDER["CAUTION"]:
            escalated_level = RISK_LEVEL_ORDER["CAUTION"]
            override_applied = True
            override_reason = "Deterministic Safety Override: Active vehicle approaching blind corner within 40 cm."

    final_risk = RISK_LEVEL_REVERSE[escalated_level]

    # Warning text generation based on final safety risk (matching Screenshot 2)
    if final_risk == "COLLISION_RISK":
        warning_level = "COLLISION_RISK"
        warning_msg = "CRITICAL WARNING: Imminent blind-corner collision! Both vehicles must stop immediately."
    elif final_risk == "HIGH_RISK":
        warning_level = "HIGH_RISK"
        warning_msg = "WARNING: High conflict potential. Simultaneous blind-corner entry must be halted."
    elif final_risk == "CAUTION":
        warning_level = "CAUTION"
        warning_msg = "CAUTION: Traffic approaching blind corner. Reduced speed and priority adherence advised."
    else:
        warning_level = "CLEAR"
        warning_msg = "NORMAL: Safe corridor conditions. No imminent conflict detected."

    return SafetyAssessmentResult(
        final_safety_risk=final_risk,
        override_applied=override_applied,
        override_reason=override_reason,
        warning_level=warning_level,
        warning_message=warning_msg
    )
