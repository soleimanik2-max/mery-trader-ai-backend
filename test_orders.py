from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def create_trader_token():
    response = client.post(
        "/api/auth",
        json={
            "user_id": "trader-test",
            "role": "TRADER",
        },
    )

    assert response.status_code == 200
    return response.json()["token"]


def create_user_token():
    response = client.post(
        "/api/auth",
        json={
            "user_id": "user-test",
            "role": "USER",
        },
    )

    assert response.status_code == 200
    return response.json()["token"]


def test_order_validation_with_trader():
    token = create_trader_token()

    response = client.post(
        "/api/orders/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 1,
            "entry_price": 100000,
            "stop_loss": 95000,
            "take_profit": 110000,
        },
    )

    assert response.status_code == 200
    assert response.json()["approved"] is True


def test_order_validation_rejects_invalid_quantity():
    token = create_trader_token()

    response = client.post(
        "/api/orders/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0,
            "entry_price": 100000,
        },
    )

    assert response.status_code == 422


def test_order_security_requires_trader_permission():
    token = create_user_token()

    response = client.post(
        "/api/orders/security-check",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 1,
            "entry_price": 100000,
            "stop_loss": 95000,
            "take_profit": 110000,
            "system_enabled": True,
            "risk_approved": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["approved"] is False


def test_order_security_accepts_approved_trader_order():
    token = create_trader_token()

    response = client.post(
        "/api/orders/security-check",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 1,
            "entry_price": 100000,
            "stop_loss": 95000,
            "take_profit": 110000,
            "system_enabled": True,
            "risk_approved": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["approved"] is True
