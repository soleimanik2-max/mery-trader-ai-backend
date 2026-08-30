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
    assert response.json()["symbol"] == "BTCUSDT"
    assert response.json()["price"] == 100000


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
    assert response.json()["symbol"] == "BTCUSDT"
    assert "decision" in response.json()
    assert "confidence" in response.json()


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
    assert response.json()["approved"] is True
    assert response.json()["risk_amount"] == 20
    assert response.json()["position_size"] == 4
def test_user_role_permissions():
    response = client.post(
        "/api/auth",
        json={
            "user_id": "user-test",
            "role": "USER",
        },
    )

    assert response.status_code == 200

    token = response.json()["token"]

    result = client.post(
        "/api/authorize",
        headers={"Authorization": f"Bearer {token}"},
        json={"permission": "ANALYZE_MARKET"},
    )

    assert result.status_code == 200
    assert result.json()["authorized"] is True


def test_user_cannot_manage_orders():
    response = client.post(
        "/api/auth",
        json={
            "user_id": "user-test",
            "role": "USER",
        },
    )

    assert response.status_code == 200

    token = response.json()["token"]

    result = client.post(
        "/api/authorize",
        headers={"Authorization": f"Bearer {token}"},
        json={"permission": "MANAGE_ORDERS"},
    )

    assert result.status_code == 403
    assert result.json()["authorized"] is False


def test_trader_can_manage_orders():
    response = client.post(
        "/api/auth",
        json={
            "user_id": "trader-test",
            "role": "TRADER",
        },
    )

    assert response.status_code == 200

    token = response.json()["token"]

    result = client.post(
        "/api/authorize",
        headers={"Authorization": f"Bearer {token}"},
        json={"permission": "MANAGE_ORDERS"},
    )

    assert result.status_code == 200
    assert result.json()["authorized"] is True


def test_invalid_token_is_rejected():
    result = client.post(
        "/api/authorize",
        headers={"Authorization": "Bearer invalid-token"},
        json={"permission": "ANALYZE_MARKET"},
    )

    assert result.status_code == 401


def test_admin_has_system_admin_permission():
    response = client.post(
        "/api/auth",
        json={
            "user_id": "admin-test",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 200

    token = response.json()["token"]

    result = client.post(
        "/api/authorize",
        headers={"Authorization": f"Bearer {token}"},
        json={"permission": "SYSTEM_ADMIN"},
    )

    assert result.status_code == 200
    assert result.json()["authorized"] is True
