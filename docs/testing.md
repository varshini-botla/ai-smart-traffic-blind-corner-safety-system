# Testing & Validation Documentation

## 1. Automated Test Suite Summary
The project includes **36 automated test cases** spanning unit tests, integration tests, and end-to-end benchmark scenarios:

| Test File | Focus Area | Tests |
| :--- | :--- | :---: |
| `backend/tests/test_health.py` | Health endpoints (`/health`, `/api/health`) | 2 |
| `backend/tests/test_validation.py` | Pydantic physical constraints & boundary conditions | 7 |
| `backend/tests/test_features.py` | Mathematical TTC, traffic density, and feature extraction | 3 |
| `backend/tests/test_database.py` | SQLite schema, insertions, indexing, and analytics | 3 |
| `backend/tests/test_model.py` | Random Forest serialization and inference posteriors | 3 |
| `backend/tests/test_safety_traffic.py` | Deterministic safety escalation and directive assignments | 4 |
| `backend/tests/test_api_endpoints.py` | End-to-end REST routes, history, and WebSockets | 6 |
| `tests/test_end_to_end.py` | System-wide benchmark scenarios (Section 37) | 8 |
| **Total** | **All Passing** | **36** |

---

## 2. Section 37 Benchmark Test Cases

### Test Case 1: Safe Normal Traffic Flow
- **Inputs**: Side A (100cm, 0km/h, 0veh), Side B (100cm, 0km/h, 0veh)
- **Result**: `SAFE`, `NORMAL TRAFFIC FLOW`, Directives: `PROCEED` / `PROCEED`.

### Test Case 2: Single Approaching Priority
- **Inputs**: Side A (40cm, 15km/h, 1veh), Side B (100cm, 0km/h, 0veh)
- **Result**: Priority assigned to Side A (`PROCEED WITH CAUTION`), Side B yields (`WAIT`).

### Test Case 3: Dual Close Approaches
- **Inputs**: Side A (40cm, 15km/h, 1veh), Side B (40cm, 15km/h, 1veh)
- **Result**: Convergence detected; simultaneous entry halted to prevent gridlock/collision.

### Test Case 4: Imminent Dangerous Collision
- **Inputs**: Side A (20cm, 35km/h, 1veh), Side B (20cm, 35km/h, 1veh)
- **Result**: `COLLISION_RISK`, `CRITICAL STOP`, Directives: `WAIT` / `WAIT`.

---

## 3. Running Automated Tests
Execute the complete test suite from project root:
```powershell
python -m pytest backend/tests/ tests/ -v
```
