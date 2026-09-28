"""
Unit tests for FastAPI Health Endpoint
"""

import pytest
from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test GET /health returns 200 OK and valid health payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AI Smart Traffic and Blind-Corner Safety System"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
    assert data["components"]["api"] == "operational"


def test_api_health_endpoint():
    """Test GET /api/health alias returns 200 OK and valid health payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AI Smart Traffic and Blind-Corner Safety System"
