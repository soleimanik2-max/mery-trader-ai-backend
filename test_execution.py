from app.services.execution_service import execution_service
from app.services.order_management import OrderRequest


def make_buy_order():
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
        order=make_buy_order(),
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
        order=make_buy_order(),
        system_enabled=False,
        authenticated=True,
        risk_approved=True,
    )

    assert result.executed is False
    assert result.order_id is None
    assert result.reason == "Trading system is disabled"


def test_paper_order_rejected_without_authentication():
    result = execution_service.execute_paper_order(
        order=make_buy_order(),
        system_enabled=True,
        authenticated=False,
        risk_approved=True,
    )

    assert result.executed is False
    assert result.order_id is None
    assert result.reason == "Authentication required"


def test_paper_order_rejected_without_risk_approval():
    result = execution_service.execute_paper_order(
        order=make_buy_order(),
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
        order=make_buy_order(),
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


def test_executed_paper_order_creates_portfolio_position():
    from app.services.portfolio_service import portfolio_service

    portfolio_service.remove_position("BTCUSDT")

    result = execution_service.execute_paper_order(
        order=make_buy_order(),
        system_enabled=True,
        authenticated=True,
        risk_approved=True,
    )

    assert result.executed is True

    position = portfolio_service.get_position("BTCUSDT")

    assert position is not None
    assert position.symbol == "BTCUSDT"
    assert position.side == "BUY"
    assert position.quantity == 1.0
    assert position.entry_price == 100000
    assert position.stop_loss == 95000
    assert position.take_profit == 110000


def test_executed_sell_order_creates_short_position():
    from app.services.portfolio_service import portfolio_service

    portfolio_service.remove_position("ETHUSDT")

    order = OrderRequest(
        symbol="ETHUSDT",
        side="SELL",
        quantity=2.0,
        entry_price=3000,
        stop_loss=3100,
        take_profit=2800,
    )

    result = execution_service.execute_paper_order(
        order=order,
        system_enabled=True,
        authenticated=True,
        risk_approved=True,
    )

    assert result.executed is True

    position = portfolio_service.get_position("ETHUSDT")

    assert position is not None
    assert position.symbol == "ETHUSDT"
    assert position.side == "SELL"
    assert position.quantity == 2.0
    assert position.entry_price == 3000
    assert position.stop_loss == 3100
    assert position.take_profit == 2800


def test_executed_order_preserves_portfolio_pnl_logic():
    from app.services.portfolio_service import portfolio_service

    portfolio_service.remove_position("SOLUSDT")

    order = OrderRequest(
        symbol="SOLUSDT",
        side="BUY",
        quantity=2.0,
        entry_price=100,
    )

    result = execution_service.execute_paper_order(
        order=order,
        system_enabled=True,
        authenticated=True,
        risk_approved=True,
    )

    assert result.executed is True

    pnl = portfolio_service.calculate_unrealized_pnl(
        "SOLUSDT",
        110,
    )

    assert pnl == 20
