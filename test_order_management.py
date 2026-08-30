from app.services.order_management import (
    OrderManagementService,
    OrderRequest,
)


def test_valid_order_passes_validation():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1.0,
        entry_price=100000,
        stop_loss=95000,
        take_profit=110000,
    )

    result = OrderManagementService.validate_order(order)

    assert result.approved is True


def test_invalid_side_is_rejected():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="INVALID",
        quantity=1.0,
        entry_price=100000,
    )

    result = OrderManagementService.validate_order(order)

    assert result.approved is False


def test_zero_quantity_is_rejected():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0,
        entry_price=100000,
    )

    result = OrderManagementService.validate_order(order)

    assert result.approved is False


def test_equal_entry_and_stop_loss_is_rejected():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1.0,
        entry_price=100000,
        stop_loss=100000,
    )

    result = OrderManagementService.validate_order(order)

    assert result.approved is False


def test_security_gate_rejects_disabled_system():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1.0,
        entry_price=100000,
        stop_loss=95000,
    )

    result = OrderManagementService.security_check(
        order=order,
        system_enabled=False,
        authenticated=True,
        risk_approved=True,
    )

    assert result.approved is False
    assert result.reason == "Trading system is disabled"


def test_security_gate_rejects_unauthenticated_order():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1.0,
        entry_price=100000,
        stop_loss=95000,
    )

    result = OrderManagementService.security_check(
        order=order,
        system_enabled=True,
        authenticated=False,
        risk_approved=True,
    )

    assert result.approved is False
    assert result.reason == "Authentication required"


def test_security_gate_rejects_unapproved_risk():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1.0,
        entry_price=100000,
        stop_loss=95000,
    )

    result = OrderManagementService.security_check(
        order=order,
        system_enabled=True,
        authenticated=True,
        risk_approved=False,
    )

    assert result.approved is False
    assert result.reason == "Risk approval required"


def test_fully_approved_order_passes_security_gate():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1.0,
        entry_price=100000,
        stop_loss=95000,
        take_profit=110000,
    )

    result = OrderManagementService.security_check(
        order=order,
        system_enabled=True,
        authenticated=True,
        risk_approved=True,
    )

    assert result.approved is True
    assert result.reason == "Security checks passed"
