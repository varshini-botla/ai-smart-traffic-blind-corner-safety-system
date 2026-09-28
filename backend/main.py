"""
AI Smart Traffic and Blind-Corner Collision Prevention System
FastAPI Backend Main Application
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.database.connection import init_db
from backend.database import repository
from backend.schemas.traffic import (
    TrafficAnalysisRequest,
    TrafficAnalysisResponse,
    AIPredictionResult,
    SafetyAssessmentResult,
    TrafficRecommendationResult,
)
from backend.services.feature_engineering import extract_features, features_to_ml_dict
from backend.services.safety_layer import evaluate_safety_override
from backend.services.traffic_management import generate_traffic_recommendation
from backend.services.websocket_manager import ws_manager
from ai.predict import predict_risk, METADATA_FILE


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema on application startup
    init_db()
    yield


app = FastAPI(
    title="AI Smart Traffic and Blind-Corner Safety System",
    description=(
        "Academic decision-support prototype providing genuine ML risk inference, "
        "deterministic safety validation, and traffic-management recommendations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
async def root():
    """Root entry point with service metadata and URLs."""
    return {
        "message": "AI Smart Traffic and Blind-Corner Safety System Backend API",
        "frontend_url": "http://localhost:5173",
        "api_docs": "/docs",
        "health_check": "/health",
        "version": "1.0.0",
        "status": "operational",
        "instructions": "Open http://localhost:5173 in your browser to access the complete React Dashboard UI."
    }


@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check endpoint verifying service operational status."""
    return {
        "status": "healthy",
        "service": "AI Smart Traffic and Blind-Corner Safety System",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "Software-Only Decision Support Prototype",
        "components": {
            "api": "operational",
            "validation": "operational",
            "database": "operational",
            "ml_engine": "operational"
        }
    }


@app.post("/api/analyze", response_model=TrafficAnalysisResponse, tags=["Traffic Analysis"])
@app.post("/api/simulate", response_model=TrafficAnalysisResponse, tags=["Traffic Analysis"])
async def analyze_traffic(request: TrafficAnalysisRequest):
    """
    Process incoming traffic data through the end-to-end AI Decision-Support pipeline:
    1. Validate inputs (Pydantic)
    2. Extract engineered features (TTC, density, relative urgency, simultaneous approach)
    3. Run Machine Learning risk prediction (Random Forest)
    4. Apply deterministic safety escalation layer
    5. Generate traffic management recommendations & explanations
    6. Persist analysis event to SQLite
    7. Broadcast update over WebSocket to connected dashboards
    """
    try:
        timestamp_str = datetime.now(timezone.utc).isoformat()

        # Step 2: Feature Engineering
        features = extract_features(request)
        ml_vector = features_to_ml_dict(features)

        # Step 3: ML Model Prediction
        ml_res = predict_risk(ml_vector)
        ai_prediction = AIPredictionResult(
            predicted_risk=ml_res["predicted_risk"],
            confidence_score=ml_res["confidence_score"],
            class_probabilities=ml_res["class_probabilities"],
            model_name=ml_res["model_name"],
            model_version=ml_res["model_version"],
            feature_contributions=ml_res["feature_contributions"]
        )

        # Step 4: Deterministic Safety Validation Layer
        safety_assessment = evaluate_safety_override(
            ai_predicted_risk=ai_prediction.predicted_risk,
            features=features
        )

        # Step 5: Traffic Management & Action Recommendation
        recommendation = generate_traffic_recommendation(
            features=features,
            safety=safety_assessment
        )

        # Step 6: Persist event to SQLite database
        db_payload = {
            "timestamp": timestamp_str,
            "source": request.source,
            "distance_a": request.distance_a_cm,
            "distance_b": request.distance_b_cm,
            "speed_a": request.speed_a_kmh,
            "speed_b": request.speed_b_kmh,
            "vehicle_count_a": request.vehicle_count_a,
            "vehicle_count_b": request.vehicle_count_b,
            "ttc_a": features.ttc_a_seconds,
            "ttc_b": features.ttc_b_seconds,
            "traffic_density": features.traffic_density,
            "ai_risk": ai_prediction.predicted_risk,
            "final_risk": safety_assessment.final_safety_risk,
            "warning": safety_assessment.warning_message,
            "side_a_action": recommendation.side_a_action,
            "side_b_action": recommendation.side_b_action,
            "recommendation": recommendation.recommendation_summary,
            "explanation": recommendation.primary_reason,
            "raw_features": {
                "contributing_factors": recommendation.contributing_factors,
                "confidence_score": ai_prediction.confidence_score,
                "override_applied": safety_assessment.override_applied,
                "override_reason": safety_assessment.override_reason,
                "relative_urgency": features.relative_urgency,
                "conflict_potential": features.conflict_potential,
                "simultaneous_approach": features.simultaneous_approach
            }
        }
        saved_record = repository.insert_event(db_payload)

        # Assemble full response
        response_data = TrafficAnalysisResponse(
            id=saved_record.get("id"),
            timestamp=timestamp_str,
            source=request.source,
            input=request.model_dump(),
            features=features,
            ai_prediction=ai_prediction,
            safety_assessment=safety_assessment,
            traffic_recommendation=recommendation
        )

        # Step 7: Broadcast to WebSocket clients
        await ws_manager.broadcast_json({
            "type": "TRAFFIC_ANALYSIS_EVENT",
            "data": response_data.model_dump()
        })

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to process traffic analysis: {str(e)}"
        )


@app.get("/api/current-status", tags=["Traffic Analysis"])
async def get_current_status():
    """
    Retrieve the most recently processed traffic state.
    Returns clear idle status if no prior analyses exist.
    """
    latest = repository.get_latest_event()
    if not latest:
        return {
            "has_active_state": False,
            "message": "Waiting for new traffic input.",
            "state": None
        }
    return {
        "has_active_state": True,
        "message": "Latest active traffic analysis state available.",
        "state": latest
    }


@app.get("/api/history", tags=["History"])
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    risk_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Retrieve paginated historical traffic events with optional risk and text search filters.
    """
    events = repository.get_events(limit=limit, offset=offset, risk_filter=risk_filter, search=search)
    total = repository.get_events_count(risk_filter=risk_filter)
    return {
        "events": events,
        "total": total,
        "limit": limit,
        "offset": offset,
        "risk_filter": risk_filter
    }


@app.delete("/api/history", tags=["History"])
async def clear_history():
    """Clear all historical traffic events."""
    deleted_count = repository.clear_all_events()
    return {"message": "History cleared successfully", "deleted_count": deleted_count}


@app.get("/api/analytics", tags=["Analytics"])
async def get_analytics():
    """
    Retrieve real calculated summary metrics and distributions from stored records.
    """
    return repository.get_analytics_summary()


@app.get("/api/model-info", tags=["AI Model"])
async def get_model_info():
    """
    Retrieve authentic metadata and evaluation metrics for the deployed Random Forest model.
    """
    if not METADATA_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metadata artifact not found. Please run training pipeline."
        )
    with open(METADATA_FILE, "r") as f:
        meta = json.load(f)
    return meta


@app.websocket("/ws/traffic")
async def websocket_traffic_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard live updates.
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial confirmation message
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to AI Smart Traffic WebSocket stream"
        }))
        while True:
            # Keep connection open and receive optional client heartbeats
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
