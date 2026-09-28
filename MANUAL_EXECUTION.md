# Manual Execution & Setup Guide

**Project Title**: AI-Integrated Smart Traffic and Blind-Corner Collision Prevention System  
**Short Name**: AI Smart Traffic and Blind-Corner Safety System  
**Architecture**: 100% Software-Based Full-Stack Web Application (FastAPI + React Vite TypeScript + SQLite + Scikit-Learn Random Forest)

---

## 1. System Requirements & Prerequisites

Ensure the following runtimes are installed on your machine:

| Component | Minimum Version | Verified Version | Download Link |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10+ | `3.12.3` | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18.0+ | `22.14.0` | [nodejs.org](https://nodejs.org/) |
| **npm** | 9.0+ | `10.9.2` | Included with Node.js |
| **Operating System** | Windows 10/11, macOS, or Linux | Windows 11 (PowerShell) | — |

> [!NOTE]
> During Python installation on Windows, ensure the checkbox **"Add Python to PATH"** is selected.

---

## 2. Clean Project Directory Structure

```
IOT PROJECT/
├── MANUAL_EXECUTION.md          # Complete manual execution & operational guide (This file)
├── README.md                    # Project overview & architectural documentation
├── requirements.txt             # Python backend & ML dependencies
├── .gitignore                   # Version control ignore definitions
│
├── ai/                          # Artificial Intelligence & Machine Learning Pipeline
│   ├── dataset/
│   │   ├── DATASET_DOCUMENTATION.md      # Ground-truth physics data specification
│   │   ├── generate_dataset.py           # Synthetic kinematic dataset generator
│   │   └── blind_corner_traffic_dataset.csv # 4,000 balanced physical samples
│   ├── models/
│   │   ├── risk_model.joblib             # Serialized Scikit-Learn Random Forest model
│   │   └── model_metadata.json           # Model parameters, metrics & feature list
│   ├── train_model.py           # Model training & cross-validation script
│   ├── evaluate_model.py        # Confusion matrix, classification report & metrics
│   ├── predict.py               # Standalone CLI inference engine
│   └── preprocessing.py         # Feature scaling & preparation pipeline
│
├── backend/                     # FastAPI Real-Time Decision-Support Backend
│   ├── database/
│   │   ├── connection.py        # SQLite database connection manager
│   │   └── repository.py        # Data access layer for telemetry persistence
│   ├── models/
│   │   └── event.py             # Event domain definitions
│   ├── schemas/
│   │   └── traffic.py           # Pydantic v2 validation models & request/response schemas
│   ├── services/
│   │   ├── feature_engineering.py # Physical TTC, braking distance & density calculations
│   │   ├── prediction_service.py  # Model loading & posterior probability inference
│   │   ├── safety_layer.py        # Deterministic Layer 4 Failsafe Rule Engine
│   │   └── traffic_management.py  # Right-of-way resolution & signal directives
│   ├── tests/                   # Backend unit tests
│   │   ├── test_api_endpoints.py
│   │   ├── test_database.py
│   │   ├── test_features.py
│   │   ├── test_health.py
│   │   ├── test_model.py
│   │   ├── test_safety_traffic.py
│   │   └── test_validation.py
│   └── main.py                  # FastAPI application entry point, REST & WebSocket routes
│
├── data/                        # Persistent Storage
│   └── traffic_events.db        # SQLite database storing historical decisions
│
├── docs/                        # Formal Engineering Documentation
│   ├── ai-methodology.md        # Feature extraction & classification pipeline
│   ├── architecture.md          # In-depth component interactions & data flow
│   ├── limitations.md           # Sensor physical constraints & edge cases
│   ├── setup.md                 # Setup overview
│   └── testing.md               # Test coverage & verification methodology
│
├── frontend/                    # Modern React + Vite + TypeScript Web Dashboard
│   ├── public/
│   │   └── favicon.svg          # Application favicon
│   ├── src/
│   │   ├── components/
│   │   │   ├── CompleteHistorySection.tsx # Paginated SQLite history table & CSV export
│   │   │   └── DigitalTwinCanvas.tsx      # 2D SVG road digital twin with live 1-line directives
│   │   ├── pages/
│   │   │   └── UnifiedSystemPage.tsx      # Unified single-page responsive dashboard
│   │   ├── services/
│   │   │   └── api.ts                     # Axios REST client & WebSocket streaming helper
│   │   ├── types/
│   │   │   └── traffic.ts                 # TypeScript interfaces mirroring backend schemas
│   │   ├── App.tsx                        # Root React component with health polling
│   │   ├── main.tsx                       # React DOM entry point
│   │   └── index.css                      # Tailwind CSS & custom animations
│   ├── index.html               # Single-page HTML shell
│   ├── package.json             # Frontend dependencies & build scripts
│   ├── tsconfig.json            # TypeScript compiler configuration
│   ├── tailwind.config.js       # Tailwind CSS design system tokens
│   └── vite.config.ts           # Vite dev server configuration
│
└── tests/                       # End-to-End System Tests
    └── test_end_to_end.py       # Full-pipeline integration tests (36 total tests)
```

---

## 3. Step-by-Step Manual Execution Instructions

To run the complete system locally, open **two separate terminal windows** (Terminal 1 for the FastAPI backend, Terminal 2 for the React frontend).

### Step 3.1: Terminal 1 — Backend & Machine Learning Server

1. Open a terminal and navigate to the project root directory:
   ```powershell
   cd "C:\Users\botla\OneDrive\Desktop\IOT PROJECT"
   ```

2. *(Optional but Recommended)* Create and activate a Python virtual environment:
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(On macOS/Linux: `python3 -m venv venv && source venv/bin/activate`)*

3. Install the required backend and machine learning dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. *(Optional)* Verify or retrain the AI Model:
   The pre-trained Random Forest model (`risk_model.joblib`) is already supplied. You can optionally re-run the training pipeline:
   ```powershell
   python ai/train_model.py
   ```
   *Expected Output*: Model achieves ~99.5% accuracy across 4,000 samples.

5. Start the FastAPI backend application with Uvicorn:
   ```powershell
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```

6. Verify Backend Status:
   Open your browser or run a quick curl command:
   - **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)  
     *(Returns `{"status": "healthy", "model_loaded": true, "database": "connected"}`)*
   - **Interactive API Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **WebSocket Stream**: `ws://127.0.0.1:8000/ws/traffic`

---

### Step 3.2: Terminal 2 — React Web Dashboard

1. Open a **second terminal** and navigate to the `frontend` folder:
   ```powershell
   cd "C:\Users\botla\OneDrive\Desktop\IOT PROJECT\frontend"
   ```

2. Install Node.js dependencies:
   ```powershell
   npm install
   ```

3. Launch the Vite local development server:
   ```powershell
   npm run dev
   ```

4. Open the Web Application:
   In your browser (Chrome, Edge, Firefox), open:
   👉 **`http://localhost:5173`**

---

## 4. Key UI Components & How to Operate

When the web application loads, you will see a unified, professional dashboard:

### 1. Live Blind-Corner 2D Road Digital Twin
- **Asphalt Canvas**: Shows an L-shaped perpendicular blind corner with road centerlines and calibrated stoplines.
- **Blind Obstruction**: Represents the zero direct line-of-sight visual barrier with red occlusion laser sight lines.
- **Vehicles**: Blue car (**Vehicle A**) moving down from the top lane; Green car (**Vehicle B**) moving right from the left lane.
- **Traffic Signals (SIG A & SIG B)**: Dynamically toggle between Red and Green based on right-of-way arbitration.
- **Intersection Conflict Zone**: Marked with yellow-box junction pavement hatching and live directional flow chevrons.
- **1-Line Vehicle Instruction Display**: Positioned directly inside the conflict zone:
  - `➔ B: PROCEED | 🛑 A: WAIT` *(when Side B is granted green)*
  - `➔ A: PROCEED | 🛑 B: WAIT` *(when Side A is granted green)*
  - `🛑 ALL VEHICLES STOP 🛑` *(during critical collision emergency)*
- **Live Vehicle Directive Banner**: Positioned right below the road canvas for clear high-contrast reading.

### 2. Sensor Telemetry Cards
- **Measured Distance**: Real-time physical distance from sensor to vehicle in centimeters (`cm`).
- **Approach Velocity**: Vehicle velocity in `cm/s`.
- **Estimated Time-To-Collision (TTC)**: Displays real physical time to intersection impact ($TTC = d/v$).
- **Stopping Distance**: Real-world kinetic stopping distance under standard tire-road friction.

### 3. AI Collision-Risk & Deterministic Safety Layer
- **Current Evaluated Risk**: Displays genuine risk classification (`SAFE`, `CAUTION`, `HIGH_RISK`, `COLLISION_RISK`).
- **AI Model Confidence**: Real posterior confidence percentage from the Random Forest model.
- **Layer 4 Fail-Safe Status**: Confirms whether the decision was AI verified or deterministically escalated.
- **Class Posterior Distribution**: Probability distribution across all 4 risk categories.

### 4. Traffic Minimization & Management
- **Recommendation Banner**: High-level system directive (e.g. `RECOMMENDATION: SIDE B PROCEED` or `RECOMMENDATION: BOTH WAIT`).
- **Signal Guidance**: Clear action boxes (`PROCEED` or `WAIT`) for each individual driver.
- **Explainability**: Plain-English physical rationale explaining why priority was granted.

### 5. Web Sensor Simulation & Test Mode
Use the interactive sliders to test any traffic scenario:
- **Side A Distance Slider**: $10\text{ cm}$ to $150\text{ cm}$.
- **Side A Approach Speed Slider**: $0\text{ cm/s}$ to $50\text{ cm/s}$.
- **Side B Distance Slider**: $10\text{ cm}$ to $150\text{ cm}$.
- **Side B Approach Speed Slider**: $0\text{ cm/s}$ to $50\text{ cm/s}$.
- **Button**: Click **`APPLY CUSTOM SENSOR DATA (POST /simulate)`** to transmit the telemetry to the backend.

### 6. Complete Telemetry & Risk Analysis History Log
- Direct SQLite table logging every analyzed event.
- Filter buttons: `ALL`, `COLLISION RISK`, `HIGH RISK`, `CAUTION`, `SAFE`.
- Search box for filtering by keyword, ID, or directive.
- **Export to CSV**: Download complete dataset for external reporting.
- **Clear History**: Reset the SQLite database records.

---

## 5. Verification & Demonstration Scenarios

Use the **Web Sensor Simulation / Test Mode** sliders to demonstrate the system's intelligence and safety guarantees:

### Scenario A: Imminent Blind-Corner Collision Risk (Critical Hazard)
- **Inputs**:
  - Side A: Distance = `10 cm`, Speed = `0 cm/s` (or `10 cm` @ `20 cm/s`)
  - Side B: Distance = `10 cm`, Speed = `0 cm/s` (or `10 cm` @ `20 cm/s`)
- **Click**: `APPLY CUSTOM SENSOR DATA`
- **Expected Results**:
  - **Evaluated Risk**: `COLLISION RISK`
  - **Digital Twin**: `BUZZER ACTIVE (2000Hz)` badge appears at top right; Red circular halo at conflict zone with `🛑 ALL VEHICLES STOP 🛑`.
  - **Traffic Lights**: Both **SIG A** and **SIG B** turn RED.
  - **Recommendation**: `RECOMMENDATION: BOTH WAIT`
  - **Directive**: `Emergency hold! Both vehicles attempting simultaneous entry into the blind corner. Signals held red to prevent collision.`

### Scenario B: Priority Right-of-Way Arbitration (Caution)
- **Inputs**:
  - Side A: Distance = `74 cm`, Speed = `13 cm/s` (TTC = `5.7 s`)
  - Side B: Distance = `30 cm`, Speed = `20 cm/s` (TTC = `1.5 s`)
- **Click**: `APPLY CUSTOM SENSOR DATA`
- **Expected Results**:
  - **Evaluated Risk**: `CAUTION`
  - **Digital Twin**: Conflict zone shows `➔ B: PROCEED | 🛑 A: WAIT`.
  - **Traffic Lights**: **SIG B** turns GREEN; **SIG A** turns RED.
  - **Recommendation**: `RECOMMENDATION: SIDE B PROCEED`
  - **Guidance**: Side B = `PROCEED`, Side A = `WAIT`.

### Scenario C: Clear Traffic Flow (Safe)
- **Inputs**:
  - Side A: Distance = `130 cm`, Speed = `10 cm/s` (TTC = `13.0 s`)
  - Side B: Distance = `140 cm`, Speed = `8 cm/s` (TTC = `17.5 s`)
- **Click**: `APPLY CUSTOM SENSOR DATA`
- **Expected Results**:
  - **Evaluated Risk**: `SAFE`
  - **Digital Twin**: Conflict zone displays `✔ ALL CLEAR: PROCEED WITH CAUTION`.
  - **Traffic Lights**: Both signals show GREEN.
  - **Recommendation**: `NORMAL TRAFFIC FLOW - PROCEED WITH CAUTION`

---

## 6. Manual Testing via CLI / cURL

You can test the backend directly via terminal without using the web frontend:

### Analyze Traffic Request via cURL:
```powershell
curl -X POST "http://127.0.0.1:8000/api/analyze" `
  -H "Content-Type: application/json" `
  -d '{
    "distance_a_cm": 25.0,
    "speed_a_cms": 30.0,
    "vehicle_count_a": 1,
    "distance_b_cm": 25.0,
    "speed_b_cms": 30.0,
    "vehicle_count_b": 1
  }'
```

### Response:
```json
{
  "timestamp": "2026-09-28T13:20:00.000000Z",
  "features": {
    "distance_a_cm": 25.0,
    "distance_b_cm": 25.0,
    "speed_a_cms": 30.0,
    "speed_b_cms": 30.0,
    "ttc_a_seconds": 0.83,
    "ttc_b_seconds": 0.83,
    "simultaneous_approach": true,
    "traffic_density": "HIGH"
  },
  "prediction": {
    "predicted_risk_level": "COLLISION_RISK",
    "model_confidence": 0.99
  },
  "safety": {
    "final_safety_risk": "COLLISION_RISK",
    "override_applied": true,
    "warning_message": "CRITICAL WARNING: Imminent blind-corner collision! Both vehicles must stop immediately."
  },
  "traffic_recommendation": {
    "side_a_action": "WAIT",
    "side_b_action": "WAIT",
    "recommendation_summary": "CRITICAL STOP: RECOMMENDATION BOTH WAIT"
  }
}
```

---

## 7. Running the Automated Test Suite

The project includes 36 automated unit and end-to-end integration tests covering physics calculations, Pydantic validations, ML inference, safety overrides, and database operations.

From the project root:
```powershell
python -m pytest backend/tests/ tests/ -v
```
*Expected Result*: **36 passed in ~3.5 seconds**.

To validate the frontend build:
```powershell
cd frontend
npm run build
```
*Expected Result*: Zero TypeScript or bundler errors; production bundle built cleanly in `< 1.0s`.

---

## 8. Troubleshooting & FAQ

1. **Port 8000 or 5173 is already in use:**
   - Terminate the conflicting process or change the port:
     ```powershell
     python -m uvicorn backend.main:app --reload --port 8001
     ```
   - In `frontend/src/services/api.ts`, update `http://127.0.0.1:8000` to your new port.

2. **Backend shows `Model file not found`:**
   - Run `python ai/train_model.py` to regenerate `risk_model.joblib` and `model_metadata.json` in `ai/models/`.

3. **Database locked error:**
   - If SQLite indicates the file is locked, close any external database viewers or restart the backend process. The database file resides at `data/traffic_events.db`.

4. **Frontend shows `Backend: OFFLINE`:**
   - Ensure the Uvicorn process in Terminal 1 is running and shows `Uvicorn running on http://127.0.0.1:8000`.
