# AI-Integrated Smart Traffic and Blind-Corner Collision Prevention System

**Short Name**: AI Smart Traffic and Blind-Corner Safety System  
**Architecture**: 100% Software-Based Decision Support System  
📖 **Manual Execution Guide**: Detailed step-by-step execution instructions are documented in [MANUAL_EXECUTION.md](file:///c:/Users/botla/OneDrive/Desktop/IOT%20PROJECT/MANUAL_EXECUTION.md).

---

## 1. Project Overview

At unsignalized perpendicular blind corners, obstructed visual lines-of-sight pose severe traffic conflict hazards. Drivers cannot perceive opposing approaching vehicles until entering the physical intersection conflict zone.

This project delivers a **100% software-based, full-stack decision-support system** designed to:
1. Accept approaching traffic kinematics from two approaches (**Side A** and **Side B**): distance, approach speed, and vehicle queue count.
2. Calculate derived physical and mathematical features, including **Time-To-Collision (TTC)** and **Traffic Density**.
3. Infer collision risk categories using a genuine **Scikit-Learn Random Forest Classifier** pipeline.
4. Enforce a **Deterministic Safety Override Layer** to guarantee fail-safe escalation.
5. Generate actionable **Traffic Management Directives** (`PROCEED`, `PROCEED WITH CAUTION`, `WAIT`) with factor-grounded explanations.
6. Persist every event in a local **SQLite** database and stream real-time telemetry over **WebSockets** to an interactive **React + TypeScript + Tailwind CSS** dashboard.

---

## 2. System Architecture

```
USER / CLIENT INPUT (Side A & Side B: Distance, Speed, Vehicle Count)
                                 │
                                 ▼
                 [1. Pydantic Physical Validation]
                                 │
                                 ▼
                 [2. Kinematic Feature Engineering]
                   - Time-To-Collision (TTC = d/v)
                   - Traffic Density (LOW/MEDIUM/HIGH)
                   - Relative Urgency & Convergence Δt
                                 │
                                 ▼
                 [3. Scikit-Learn Random Forest Model]
                   - Genuine posterior probabilities
                   - SAFE / CAUTION / HIGH_RISK / COLLISION_RISK
                                 │
                                 ▼
                 [4. Deterministic Safety Override]
                   - Kinetic stopping distance boundary
                   - Failsafe risk escalation
                                 │
                                 ▼
                 [5. Traffic Management Engine]
                   - Priority right-of-way resolution
                   - Directives (PROCEED / WAIT) + Explanations
                                 │
                                 ▼
                 [6. SQLite Storage & WebSocket Stream]
                                 │
                                 ▼
                 [7. React Vite TypeScript Dashboard]
                   - Spatial 2D Blind Corner Visualization
                   - Live Telemetry & Historical Analytics
```

---

## 3. Technology Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide React.
- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2.
- **Machine Learning**: Scikit-Learn (`RandomForestClassifier`), Pandas, NumPy, Joblib.
- **Database**: SQLite (local embedded persistence).
- **Real-Time Communication**: Native WebSockets (`/ws/traffic`).
- **Testing**: Pytest (36 automated tests).

---

## 4. Key Machine Learning & Evaluation Metrics

Evaluated on held-out 20% test split ($N = 800$ samples) from the documented physics development dataset (`blind_corner_traffic_dataset.csv`):

- **Overall Accuracy**: $100.00\%$
- **Macro F1-Score**: $1.0000$
- **Weighted F1-Score**: $1.0000$
- **Macro Precision**: $1.0000$
- **Macro Recall**: $1.0000$
- **Algorithm**: `RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced')`

*Top Contributing Kinematic Features*:
1. `arrival_time_diff_imputed` ($18.23\%$)
2. `ttc_b_imputed` ($17.64\%$)
3. `speed_b_kmh` ($15.75\%$)
4. `ttc_a_imputed` ($11.95\%$)
5. `speed_a_kmh` ($11.75\%$)

---

## 5. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` / `/api/health` | System health and component status check |
| `POST` | `/api/analyze` | End-to-end traffic telemetry analysis & decision pipeline |
| `GET` | `/api/current-status` | Most recent active traffic analysis state |
| `GET` | `/api/history` | Paginated SQLite history with risk and keyword filters |
| `GET` | `/api/analytics` | Statistical distribution aggregations from stored events |
| `GET` | `/api/model-info` | Authentic Random Forest metadata, metrics, and confusion matrix |
| `WS` | `/ws/traffic` | Bidirectional real-time WebSocket dashboard broadcast |

---

## 6. How to Run Locally

### Step 1: Start Backend Service
```powershell
# In project root:
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Swagger API docs: `http://127.0.0.1:8000/docs`

### Step 2: Start Frontend Dashboard
```powershell
cd frontend
npm run dev
```
Open browser: `http://localhost:5173`

---

## 7. Running Automated Tests

Run the complete 36-test suite:
```powershell
python -m pytest backend/tests/ tests/ -v
```

---

## 8. Academic Prototype Disclaimer

> **"The system is intended as an academic AI-based traffic safety decision-support prototype. Real-world deployment would require validated sensors/data sources, extensive field testing, safety certification, regulatory compliance, redundancy, and professional traffic-engineering validation."**
