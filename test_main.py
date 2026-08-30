from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["app"] == "MERY TRADER AI"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"


def test_api_version():
    response = client.get("/api/version")
    assert response.status_code == 200
    assert response.json()["version"] == "1.0.0"
