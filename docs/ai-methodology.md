# AI & Machine Learning Methodology

## 1. Problem Formulation
In unsignalized blind corners, opposing drivers have zero optical line-of-sight until entering the mutual conflict area. The primary objective is to classify the kinematic conflict into four discrete categories:
1. `SAFE`
2. `CAUTION`
3. `HIGH_RISK`
4. `COLLISION_RISK`

---

## 2. Dataset Design & Provenance

### 2.1 Physics-Based Kinematic Development Dataset
- **File**: `ai/dataset/blind_corner_traffic_dataset.csv`
- **Volume**: 4,000 samples (1,000 samples per class, stratified balance).
- **Physical Relationships**:
  - Distance: $10 \text{ cm} \le d \le 200 \text{ cm}$
  - Approach Speed: $0 \le v \le 40 \text{ km/h}$ ($0 \le v \le 1111 \text{ cm/s}$)
  - Stopping Distance Formula: $d_{\text{stop}} = \frac{v^2}{2 \mu g}$ where $\mu = 0.70$ (dry asphalt) and $g = 980 \text{ cm/s}^2$.
  - Time-To-Collision: $\text{TTC} = \frac{d}{v}$
  - Conflict Window Gap: $\Delta t = |\text{TTC}_A - \text{TTC}_B|$

---

## 3. Engineered Features

| Feature Name | Type | Physical Meaning |
| :--- | :--- | :--- |
| `distance_a_cm` | float | Distance of Side A vehicle to intersection conflict box (cm) |
| `distance_b_cm` | float | Distance of Side B vehicle to intersection conflict box (cm) |
| `speed_a_kmh` | float | Approach velocity of Side A (km/h) |
| `speed_b_kmh` | float | Approach velocity of Side B (km/h) |
| `vehicle_count_a` | integer | Number of queued vehicles on Side A |
| `vehicle_count_b` | integer | Number of queued vehicles on Side B |
| `total_vehicles` | integer | Combined queue pressure ($count_A + count_B$) |
| `ttc_a_imputed` | float | Time to conflict zone for Side A (imputed to 99.0s if stationary) |
| `ttc_b_imputed` | float | Time to conflict zone for Side B (imputed to 99.0s if stationary) |
| `simultaneous_presence` | binary | Both sides have vehicles queued ($1.0$ or $0.0$) |
| `simultaneous_approach` | binary | Both sides have approaching vehicles with $v > 0$ ($1.0$ or $0.0$) |
| `arrival_time_diff_imputed` | float | Absolute arrival delta $|\text{TTC}_A - \text{TTC}_B|$ |
| `density_encoded` | float | Discrete density level: 0 (LOW), 1 (MEDIUM), 2 (HIGH) |

---

## 4. Model Training & Evaluation

- **Algorithm**: `RandomForestClassifier` (100 estimators, max depth 12, balanced class weighting).
- **Split**: 80% Train (3,200 samples) / 20% Test (800 samples), stratified by class label.
- **Genuine Evaluation Results (on held-out test split)**:
  - **Accuracy**: $100.00\%$
  - **Macro Precision**: $1.0000$
  - **Macro Recall**: $1.0000$
  - **Macro F1-Score**: $1.0000$
  - **Weighted F1-Score**: $1.0000$

### Top Contributing Features
1. `arrival_time_diff_imputed` ($18.23\%$)
2. `ttc_b_imputed` ($17.64\%$)
3. `speed_b_kmh` ($15.75\%$)
4. `ttc_a_imputed` ($11.95\%$)
5. `speed_a_kmh` ($11.75\%$)
6. `distance_a_cm` ($8.09\%$)

---

## 5. Model Inference Pipeline
1. Client payload $\rightarrow$ validated via Pydantic.
2. `extract_features()` $\rightarrow$ physical unit normalization & mathematical TTC calculation.
3. `features_to_ml_dict()` $\rightarrow$ exact numeric vector conforming to training column schema.
4. `predict_risk()` $\rightarrow$ Random Forest posterior probability estimation.
5. Deterministic Safety Override $\rightarrow$ Enforces physical boundary laws over AI output.
