"""
Tests pour l'application principale
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """Test de l'endpoint racine"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test de l'endpoint de santé"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
