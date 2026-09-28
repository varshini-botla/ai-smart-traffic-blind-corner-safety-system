# System Architecture

## AI-Integrated Smart Traffic and Blind-Corner Collision Prevention System
**Short Name**: AI Smart Traffic and Blind-Corner Safety System  
**Type**: 100% Software-Based Decision-Support Prototype

---

## 1. High-Level Architectural Diagram

```
                 USER / CLIENT TRAFFIC TELEMETRY
          (Side A & Side B: Distance, Speed, Vehicle Count)
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   FASTAPI WEB LAYER   │
                     │  (/api/analyze, CORS) │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  PYDANTIC VALIDATION  │
                     │ (Physical Constraints)│
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  FEATURE ENGINEERING  │
                     │  (TTC, Density, Δt)   │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   MACHINE LEARNING    │
                     │  Random Forest Model  │
                     │  Posterior Inference  │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  DETERMINISTIC SAFETY │
                     │   Failsafe Override   │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  TRAFFIC MANAGEMENT   │
                     │  (PROCEED/WAIT Rules) │
                     └───────────┬───────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
        ┌───────────────────────┐ ┌───────────────────────┐
        │     SQLITE STORE      │ │       WEBSOCKET       │
        │    (traffic_events)   │ │      (/ws/traffic)    │
        └───────────────────────┘ └───────────┬───────────┘
                                              │
                                              ▼
                                  ┌───────────────────────┐
                                  │    REACT DASHBOARD    │
                                  │   (Vite + TypeScript) │
                                  │   Spatial 2D Blind    │
                                  │     Visualization     │
                                  └───────────────────────┘
```

---

## 2. Layer-by-Layer Component Details

### 2.1 Web Service & Routing Layer (`backend/main.py`)
- Built on **FastAPI** with ASGI architecture.
- Implements CORS middleware configured for React localhost origins (`http://localhost:5173`, `http://127.0.0.1:5173`).
- Automatic database initialization via asynchronous lifespan context.
- Native WebSocket connection broadcaster (`/ws/traffic`).

### 2.2 Ingestion & Validation Layer (`backend/schemas/traffic.py`)
- Enforces strict Pydantic v2 validation constraints:
  - $\text{distance} > 0 \text{ cm}$ (Physical boundary: up to $10,000 \text{ cm}$)
  - $\text{speed} \ge 0 \text{ km/h}$ (Physical boundary: up to $200 \text{ km/h}$)
  - $\text{vehicle\_count} \ge 0$ (Physical boundary: up to $100 \text{ vehicles}$)
- Distinguishes data provenance via explicit `source` metadata.

### 2.3 Feature Engineering Layer (`backend/services/feature_engineering.py`)
- Standardizes speed into physical units ($\text{cm/s} = \text{km/h} \times \frac{250}{9}$).
- Calculates mathematical Time-To-Collision: $\text{TTC} = \frac{d}{v}$.
- Derives spatial and queue density indicators: `traffic_density` (LOW, MEDIUM, HIGH).
- Evaluates simultaneous dual approach and arrival window difference ($\Delta t = |\text{TTC}_A - \text{TTC}_B|$).

### 2.4 Machine Learning Inference Engine (`ai/predict.py`)
- Loads trained Scikit-Learn **Random Forest Classifier** (`ai/models/risk_model.joblib`).
- Generates empirical class probabilities across canonical classes: `SAFE`, `CAUTION`, `HIGH_RISK`, `COLLISION_RISK`.
- Outputs genuine posterior confidence score without fabrication.

### 2.5 Deterministic Safety Override Layer (`backend/services/safety_layer.py`)
- Guarantees fail-safe safety escalation over AI predictions when critical physical collision criteria are met:
  1. Imminent collision: $\text{TTC}_A \le 0.25\text{s}$, $\text{TTC}_B \le 0.25\text{s}$, $\Delta t \le 0.15\text{s}$, and close proximity $\rightarrow$ Escalate to `COLLISION_RISK`.
  2. Severe convergence: $\Delta t \le 0.30\text{s}$ and short TTC $\rightarrow$ Escalate to at least `HIGH_RISK`.
  3. Single aggressive approach near corner $\rightarrow$ Escalate to at least `CAUTION`.
- Can only **escalate** risk severity, never dangerously downgrade it.

### 2.6 Traffic Management Recommendation Engine (`backend/services/traffic_management.py`)
- Answers the objective: *"How can traffic congestion and collisions be minimized?"*
- Determines priority right-of-way based on relative urgency, distance, and approach speeds.
- Emits discrete approach directives: `PROCEED`, `PROCEED WITH CAUTION`, `WAIT`.
- Compiles factor-grounded explanations explaining *why* the directives were issued.

### 2.7 Persistent Event Store (`backend/database/`)
- Local **SQLite** database (`data/traffic_events.db`).
- Table: `traffic_events` with indexing on `timestamp` and `final_risk`.
- Aggregates genuine historical distributions and metrics without synthetic mock records.

### 2.8 Frontend React Dashboard (`frontend/src/`)
- Built with **React 18**, **Vite**, **TypeScript**, and **Tailwind CSS**.
- Features 7 dedicated pages: Dashboard, Traffic Analysis, Live Monitoring, Event History, Analytics, AI Model Info, and System Architecture.
- Includes interactive SVG 2D blind-corner visualization mapped directly to input distances and speeds.
