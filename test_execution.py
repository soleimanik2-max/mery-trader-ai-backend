from app.services.execution_service import execution_service
from app.services.order_management import OrderRequest


def make_order():
    return OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1.0,
        entry_price=100000,
        stop_loss=95000,
        take_profit=110000,
    )


def test_paper_order_executes_when_all_checks_pass():
    result = execution_service.execute_paper_order(
        order=make_order(),
        system_enabled=True,
        authenticated=True,
        risk_approved=True,
    )

    assert result.executed is True
    assert result.order_id is not None
    assert result.order_id.startswith("PAPER-")
    assert result.reason == "Paper order executed successfully"


def test_paper_order_rejected_when_system_disabled():
    result = execution_service.execute_paper_order(
        order=make_order(),
        system_enabled=False,
        authenticated=True,
        risk_approved=True,
    )

    assert result.executed is False
    assert result.order_id is None
    assert result.reason == "Trading system is disabled"


def test_paper_order_rejected_without_authentication():
    result = execution_service.execute_paper_order(
        order=make_order(),
        system_enabled=True,
        authenticated=False,
        risk_approved=True,
    )

    assert result.executed is False
    assert result.order_id is None
    assert result.reason == "Authentication required"


def test_paper_order_rejected_without_risk_approval():
    result = execution_service.execute_paper_order(
        order=make_order(),
        system_enabled=True,
        authenticated=True,
        risk_approved=False,
    )

    assert result.executed is False
    assert result.order_id is None
    assert result.reason == "Risk approval required"


def test_invalid_order_is_not_executed():
    order = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=0,
        entry_price=100000,
        stop_loss=95000,
    )

    result = execution_service.execute_paper_order(
        order=order,
        system_enabled=True,
        authenticated=True,
        risk_approved=True,
    )

    assert result.executed is False
    assert result.order_id is None
    assert result.reason == "Quantity must be greater than zero"


def test_executed_paper_order_is_available():
    result = execution_service.execute_paper_order(
        order=make_order(),
        system_enabled=True,
        authenticated=True,
        risk_approved=True,
    )

    assert result.executed is True
    assert result.order_id is not None

    stored_order = execution_service.get_order(result.order_id)

    assert stored_order is not None
    assert stored_order.symbol == "BTCUSDT"
    assert stored_order.side == "BUY"
    assert stored_order.quantity == 1.0
    assert stored_order.entry_price == 100000
