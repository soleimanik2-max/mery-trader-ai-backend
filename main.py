from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def get_auth_headers():
    response = client.post(
        "/api/auth",
        json={"user_id": "test-user"},
    )

    assert response.status_code == 200

    token = response.json()["token"]

    return {
        "Authorization": f"Bearer {token}",
    }


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


def test_authentication():
    response = client.post(
        "/api/auth",
        json={"user_id": "test-user"},
    )

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["token"]


def test_market_data():
    response = client.post(
        "/api/market-data",
        headers=get_auth_headers(),
        json={
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "price": 100000,
            "volume": 10,
        },
    )

    assert response.status_code == 200


def test_market_analysis():
    prices = list(range(1, 61))

    response = client.post(
        "/api/analyze",
        headers=get_auth_headers(),
        json={
            "symbol": "BTCUSDT",
            "prices": prices,
        },
    )

    assert response.status_code == 200


def test_risk_management():
    response = client.post(
        "/api/risk",
        headers=get_auth_headers(),
        json={
            "active_capital": 1000,
            "entry_price": 100,
            "stop_loss": 95,
            "risk_percent": 2,
        },
    )

    assert response.status_code == 200
