"""
Traffic Management and Decision-Support Recommendation Service
Generates actionable traffic management directives (PROCEED, WAIT, PROCEED WITH CAUTION)
and interpretable, factor-grounded explanations.
"""

from typing import List, Tuple
from backend.schemas.traffic import (
    EngineeredFeatures,
    SafetyAssessmentResult,
    TrafficRecommendationResult,
)


def generate_traffic_recommendation(
    features: EngineeredFeatures,
    safety: SafetyAssessmentResult
) -> TrafficRecommendationResult:
    """
    Traffic Management Engine.
    Determines priority, safe passage, and waiting conditions while minimizing congestion.
    """
    final_risk = safety.final_safety_risk
    factors: List[str] = []

    # 1. Collect genuine contributing factors from computed features
    if features.vehicle_count_a > 0:
        if features.speed_a_cms > 0:
            factors.append(f"Side A has an approaching vehicle ({features.speed_a_cms} cm/s, {features.distance_a_cm} cm).")
        else:
            factors.append(f"Side A has stationary vehicle presence (Queue: {features.vehicle_count_a}).")
    else:
        factors.append("Side A approach is clear.")

    if features.vehicle_count_b > 0:
        if features.speed_b_cms > 0:
            factors.append(f"Side B has an approaching vehicle ({features.speed_b_cms} cm/s, {features.distance_b_cm} cm).")
        else:
            factors.append(f"Side B has stationary vehicle presence (Queue: {features.vehicle_count_b}).")
    else:
        factors.append("Side B approach is clear.")

    if features.ttc_a_seconds is not None:
        factors.append(f"Side A estimated Time-To-Collision (TTC): {features.ttc_a_seconds}s.")
    if features.ttc_b_seconds is not None:
        factors.append(f"Side B estimated Time-To-Collision (TTC): {features.ttc_b_seconds}s.")

    if features.simultaneous_approach:
        diff_str = f"{features.relative_arrival_time_diff_sec}s" if features.relative_arrival_time_diff_sec is not None else "N/A"
        factors.append(f"Simultaneous dual approach detected with arrival time gap of {diff_str}.")

    if features.traffic_density != "LOW":
        factors.append(f"Traffic density pressure evaluated as {features.traffic_density} (Total: {features.total_vehicles} vehicles).")

    # 2. Decision Logic
    # Case 4: Critical Collision Risk -> Both MUST Wait
    if final_risk == "COLLISION_RISK":
        side_a_action = "WAIT"
        side_b_action = "WAIT"
        summary = "CRITICAL STOP: RECOMMENDATION BOTH WAIT"
        reason = "Emergency hold! Both vehicles attempting simultaneous entry into the blind corner. Signals held red to prevent collision."

    # Case 3: High Risk
    elif final_risk == "HIGH_RISK":
        if features.relative_urgency == "SIDE_A_URGENT":
            side_a_action = "PROCEED WITH CAUTION"
            side_b_action = "WAIT"
            summary = "RECOMMENDATION: SIDE A PROCEED"
            reason = "Side A vehicle prioritized due to closer proximity or lower Time-To-Collision. Side B held safely at stopline."
        elif features.relative_urgency == "SIDE_B_URGENT":
            side_a_action = "WAIT"
            side_b_action = "PROCEED WITH CAUTION"
            summary = "RECOMMENDATION: SIDE B PROCEED"
            reason = "Side B vehicle prioritized due to closer proximity or lower Time-To-Collision. Side A held safely at stopline."
        else:
            side_a_action = "WAIT"
            side_b_action = "WAIT"
            summary = "HIGH RISK: CONFLICT SEPARATION REQUIRED"
            reason = "Both approaches are converging simultaneously with narrow arrival gap. Both approaches must pause."

    # Case 2: Caution
    elif final_risk == "CAUTION":
        if features.vehicle_count_a > 0 and (features.vehicle_count_b == 0 or features.speed_b_cms == 0):
            side_a_action = "PROCEED WITH CAUTION"
            side_b_action = "WAIT"
            summary = "RECOMMENDATION: SIDE A PROCEED"
            reason = "Side A is actively approaching with no conflicting motion detected on Side B."
        elif features.vehicle_count_b > 0 and (features.vehicle_count_a == 0 or features.speed_a_cms == 0):
            side_a_action = "WAIT"
            side_b_action = "PROCEED WITH CAUTION"
            summary = "RECOMMENDATION: SIDE B PROCEED"
            reason = "Side B is actively approaching with no conflicting motion detected on Side A."
        elif features.relative_urgency == "SIDE_A_URGENT":
            side_a_action = "PROCEED WITH CAUTION"
            side_b_action = "WAIT"
            summary = "RECOMMENDATION: SIDE A PROCEED"
            reason = "Side A vehicle prioritized due to closer proximity or lower Time-To-Collision. Side B held safely at stopline."
        elif features.relative_urgency == "SIDE_B_URGENT":
            side_a_action = "WAIT"
            side_b_action = "PROCEED WITH CAUTION"
            summary = "RECOMMENDATION: SIDE B PROCEED"
            reason = "Side B vehicle prioritized due to closer proximity or lower Time-To-Collision. Side A held safely at stopline."
        else:
            # Equal urgency / identical approach in Caution: prioritize Side B (as in prototype default) or Side A
            side_a_action = "WAIT"
            side_b_action = "PROCEED"
            summary = "RECOMMENDATION: SIDE B PROCEED"
            reason = "Side B vehicle prioritized due to closer proximity or lower Time-To-Collision. Side A held safely at stopline."

    # Case 1: SAFE
    else:
        side_a_action = "PROCEED"
        side_b_action = "PROCEED"
        summary = "RECOMMENDATION: ALL SIDES PROCEED (NORMAL TRAFFIC FLOW)"
        reason = "Both approaches are clear or approaching vehicles are sufficiently distant. Normal movement permitted."

    return TrafficRecommendationResult(
        side_a_action=side_a_action,
        side_b_action=side_b_action,
        recommendation_summary=summary,
        primary_reason=reason,
        contributing_factors=factors
    )
