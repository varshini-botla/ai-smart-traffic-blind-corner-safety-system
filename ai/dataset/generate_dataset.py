"""
Physics-Based Synthetic Dataset Generator for Blind-Corner Collision Development
Strictly documented as a synthetic development dataset for academic prototyping.
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
DATASET_FILE = CURRENT_DIR / "blind_corner_traffic_dataset.csv"

# Friction and stopping distance constants
MU_FRICTION = 0.70
G_GRAVITY = 980.0
STOP_DENOM = 2 * MU_FRICTION * G_GRAVITY  # 1372 cm/s^2


def compute_stopping_dist(speed_cms: float) -> float:
    """Calculate braking stopping distance in cm using v^2 / (2 * mu * g)."""
    return (speed_cms ** 2) / STOP_DENOM


def generate_dataset(samples_per_class: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate physics-grounded traffic scenarios across Side A and Side B approaches.
    Ensures balanced distribution across all 4 canonical risk classes (1000 samples each = 4000 total).
    """
    rng = np.random.RandomState(seed)
    class_targets = {
        "SAFE": samples_per_class,
        "CAUTION": samples_per_class,
        "HIGH_RISK": samples_per_class,
        "COLLISION_RISK": samples_per_class,
    }
    class_counts = {k: 0 for k in class_targets}
    rows = []

    while any(class_counts[k] < class_targets[k] for k in class_targets):
        needed_classes = [k for k, v in class_counts.items() if v < class_targets[k]]
        target_class = rng.choice(needed_classes)

        if target_class == "SAFE":
            sub_type = rng.choice(["empty", "stationary", "far_slow"])
            if sub_type == "empty":
                count_a = 0
                count_b = 0
                speed_a = 0.0
                speed_b = 0.0
                dist_a = rng.uniform(80.0, 200.0)
                dist_b = rng.uniform(80.0, 200.0)
            elif sub_type == "stationary":
                count_a = rng.choice([0, 1, 2])
                count_b = rng.choice([0, 1, 2])
                speed_a = 0.0
                speed_b = 0.0
                dist_a = rng.uniform(40.0, 150.0)
                dist_b = rng.uniform(40.0, 150.0)
            else:
                count_a = rng.choice([1, 2])
                count_b = rng.choice([1, 2])
                # TTC > 8.5s
                dist_a = rng.uniform(90.0, 180.0)
                dist_b = rng.uniform(90.0, 180.0)
                speed_a = rng.uniform(4.0, 9.0)
                speed_b = rng.uniform(4.0, 9.0)

        elif target_class == "CAUTION":
            sub_type = rng.choice(["single_active", "moderate_dual", "wide_arrival_gap"])
            if sub_type == "single_active":
                active_side = rng.choice(["A", "B"])
                if active_side == "A":
                    dist_a = rng.uniform(40.0, 100.0)
                    speed_a = rng.uniform(8.0, 18.0)
                    count_a = rng.randint(1, 3)
                    dist_b = rng.uniform(70.0, 150.0)
                    speed_b = 0.0
                    count_b = rng.choice([0, 1])
                else:
                    dist_a = rng.uniform(70.0, 150.0)
                    speed_a = 0.0
                    count_a = rng.choice([0, 1])
                    dist_b = rng.uniform(40.0, 100.0)
                    speed_b = rng.uniform(8.0, 18.0)
                    count_b = rng.randint(1, 3)
            elif sub_type == "moderate_dual":
                # TTC between 4.8s and 8.5s (e.g. 74cm @ 13cm/s)
                dist_a = rng.uniform(55.0, 95.0)
                dist_b = rng.uniform(55.0, 95.0)
                speed_a = rng.uniform(9.0, 16.0)
                speed_b = rng.uniform(9.0, 16.0)
                count_a = rng.randint(1, 2)
                count_b = rng.randint(1, 2)
            else:
                # Wide arrival gap (one arrives much earlier than other)
                dist_a = rng.uniform(35.0, 60.0)
                speed_a = rng.uniform(12.0, 20.0)
                count_a = 1
                dist_b = rng.uniform(80.0, 140.0)
                speed_b = rng.uniform(8.0, 15.0)
                count_b = 1

        elif target_class == "HIGH_RISK":
            sub_type = rng.choice(["converging_mid_ttc", "aggressive_single_with_queue"])
            if sub_type == "converging_mid_ttc":
                # TTC between 2.0s and 4.5s with close arrival gap
                dist_a = rng.uniform(30.0, 50.0)
                dist_b = rng.uniform(30.0, 50.0)
                speed_a = rng.uniform(12.0, 22.0)
                speed_b = rng.uniform(12.0, 22.0)
                count_a = rng.randint(1, 2)
                count_b = rng.randint(1, 2)
            else:
                # Fast single vehicle approaching stopped/queued opposing vehicle
                active_side = rng.choice(["A", "B"])
                if active_side == "A":
                    dist_a = rng.uniform(20.0, 35.0)
                    speed_a = rng.uniform(16.0, 28.0)
                    count_a = 1
                    dist_b = rng.uniform(25.0, 45.0)
                    speed_b = rng.choice([0.0, rng.uniform(0.0, 5.0)])
                    count_b = rng.randint(1, 2)
                else:
                    dist_a = rng.uniform(25.0, 45.0)
                    speed_a = rng.choice([0.0, rng.uniform(0.0, 5.0)])
                    count_a = rng.randint(1, 2)
                    dist_b = rng.uniform(20.0, 35.0)
                    speed_b = rng.uniform(16.0, 28.0)
                    count_b = 1

        else:  # COLLISION_RISK
            # Critical low TTC (< 2.0s) and near-zero arrival window
            dist_a = rng.uniform(12.0, 30.0)
            dist_b = rng.uniform(12.0, 30.0)
            speed_a = rng.uniform(20.0, 40.0)
            speed_b = rng.uniform(20.0, 40.0)
            count_a = rng.randint(1, 2)
            count_b = rng.randint(1, 2)

        # Derived physical variables
        ttc_a = (dist_a / speed_a) if (speed_a > 0 and count_a > 0) else 99.0
        ttc_b = (dist_b / speed_b) if (speed_b > 0 and count_b > 0) else 99.0

        stop_dist_a = compute_stopping_dist(speed_a) if count_a > 0 else 0.0
        stop_dist_b = compute_stopping_dist(speed_b) if count_b > 0 else 0.0

        arrival_diff = abs(ttc_a - ttc_b)
        simul_presence = 1 if (count_a > 0 and count_b > 0) else 0
        simul_approach = 1 if (count_a > 0 and count_b > 0 and speed_a > 0 and speed_b > 0) else 0

        # Physical Ground-Truth Classification logic:
        if (count_a == 0 and count_b == 0) or (speed_a == 0.0 and speed_b == 0.0):
            computed_label = "SAFE"
        elif simul_approach == 1:
            min_ttc = min(ttc_a, ttc_b)
            if (min_ttc < 2.0 and arrival_diff < 1.5) or (dist_a < stop_dist_a * 1.5 and dist_b < stop_dist_b * 1.5 and arrival_diff < 1.5):
                computed_label = "COLLISION_RISK"
            elif (min_ttc < 4.5 and arrival_diff < 3.0):
                computed_label = "HIGH_RISK"
            elif min_ttc <= 8.5 or arrival_diff >= 3.0:
                computed_label = "CAUTION"
            else:
                computed_label = "SAFE"
        elif count_a > 0 and speed_a > 0:
            if ttc_a < 2.2 and count_b > 0 and dist_a <= 30.0:
                computed_label = "HIGH_RISK"
            elif ttc_a <= 8.5:
                computed_label = "CAUTION"
            else:
                computed_label = "SAFE"
        elif count_b > 0 and speed_b > 0:
            if ttc_b < 2.2 and count_a > 0 and dist_b <= 30.0:
                computed_label = "HIGH_RISK"
            elif ttc_b <= 8.5:
                computed_label = "CAUTION"
            else:
                computed_label = "SAFE"
        else:
            computed_label = "SAFE"

        # Check if computed label is still needed
        if class_counts[computed_label] < class_targets[computed_label]:
            class_counts[computed_label] += 1
            total_veh = count_a + count_b
            density_enc = 0.0 if total_veh <= 1 else (1.0 if total_veh <= 4 else 2.0)

            rows.append({
                "distance_a_cm": round(dist_a, 2),
                "distance_b_cm": round(dist_b, 2),
                "speed_a_kmh": round(speed_a, 2),
                "speed_b_kmh": round(speed_b, 2),
                "vehicle_count_a": count_a,
                "vehicle_count_b": count_b,
                "total_vehicles": total_veh,
                "ttc_a_imputed": round(ttc_a, 2),
                "ttc_b_imputed": round(ttc_b, 2),
                "simultaneous_presence": float(simul_presence),
                "simultaneous_approach": float(simul_approach),
                "arrival_time_diff_imputed": round(arrival_diff, 2),
                "density_encoded": density_enc,
                "risk_label": computed_label
            })

    df = pd.DataFrame(rows)
    df.to_csv(DATASET_FILE, index=False)
    print(f"Generated {len(df)} samples saved to {DATASET_FILE}")
    print("\nClass distribution:")
    print(df["risk_label"].value_counts())
    return df


if __name__ == "__main__":
    generate_dataset()
