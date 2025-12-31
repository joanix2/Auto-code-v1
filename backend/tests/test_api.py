"""
Test FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Auto-Code Platform API"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert data["status"] == "healthy"


def test_create_ticket_missing_fields():
    """Test ticket creation with missing fields"""
    response = client.post("/tickets", json={})
    assert response.status_code == 422  # Validation error


def test_create_ticket_invalid_data():
    """Test ticket creation with invalid data"""
    response = client.post("/tickets", json={
        "title": "",  # Empty title
        "description": ""  # Empty description
    })
    assert response.status_code == 422  # Validation error
