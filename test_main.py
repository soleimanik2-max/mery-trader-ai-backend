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


def test_market_data():
    response = client.post(
        "/api/market-data",
        json={
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "price": 100000,
            "volume": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["symbol"] == "BTCUSDT"
    assert response.json()["price"] == 100000


def test_market_analysis():
    prices = list(range(1, 61))

    response = client.post(
        "/api/analyze",
        json={
            "symbol": "BTCUSDT",
            "prices": prices,
        },
    )

    assert response.status_code == 200
    assert response.json()["symbol"] == "BTCUSDT"
    assert "decision" in response.json()
    assert "confidence" in response.json()


def test_risk_management():
    response = client.post(
        "/api/risk",
        json={
            "active_capital": 1000,
            "entry_price": 100,
            "stop_loss": 95,
            "risk_percent": 2,
        },
    )

    assert response.status_code == 200
    assert response.json()["approved"] is True
    assert response.json()["risk_amount"] == 20
    assert response.json()["position_size"] == 4
