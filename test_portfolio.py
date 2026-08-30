from app.services.portfolio_service import PortfolioService


def test_set_cash_and_summary():
    portfolio = PortfolioService()

    assert portfolio.set_cash(10000) is True

    summary = portfolio.get_summary()

    assert summary.cash == 10000
    assert summary.equity == 10000
    assert summary.unrealized_pnl == 0
    assert summary.position_count == 0


def test_add_buy_position():
    portfolio = PortfolioService()

    position = portfolio.add_position(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1,
        entry_price=100000,
        stop_loss=95000,
        take_profit=110000,
    )

    assert position.symbol == "BTCUSDT"
    assert position.side == "BUY"
    assert position.quantity == 1
    assert position.entry_price == 100000

    stored = portfolio.get_position("BTCUSDT")

    assert stored is not None
    assert stored.symbol == "BTCUSDT"


def test_buy_position_profit():
    portfolio = PortfolioService()

    portfolio.add_position(
        symbol="BTCUSDT",
        side="BUY",
        quantity=2,
        entry_price=100000,
    )

    pnl = portfolio.calculate_unrealized_pnl(
        "BTCUSDT",
        105000,
    )

    assert pnl == 10000


def test_sell_position_profit():
    portfolio = PortfolioService()

    portfolio.add_position(
        symbol="BTCUSDT",
        side="SELL",
        quantity=2,
        entry_price=100000,
    )

    pnl = portfolio.calculate_unrealized_pnl(
        "BTCUSDT",
        95000,
    )

    assert pnl == 10000


def test_position_loss():
    portfolio = PortfolioService()

    portfolio.add_position(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1,
        entry_price=100000,
    )

    pnl = portfolio.calculate_unrealized_pnl(
        "BTCUSDT",
        95000,
    )

    assert pnl == -5000


def test_remove_position():
    portfolio = PortfolioService()

    portfolio.add_position(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1,
        entry_price=100000,
    )

    assert portfolio.remove_position("BTCUSDT") is True
    assert portfolio.get_position("BTCUSDT") is None
    assert portfolio.remove_position("BTCUSDT") is False


def test_portfolio_equity_includes_unrealized_pnl():
    portfolio = PortfolioService()

    portfolio.set_cash(10000)

    portfolio.add_position(
        symbol="BTCUSDT",
        side="BUY",
        quantity=1,
        entry_price=100,
    )

    summary = portfolio.get_summary(
        current_prices={"BTCUSDT": 110},
    )

    assert summary.cash == 10000
    assert summary.unrealized_pnl == 10
    assert summary.equity == 10010
    assert summary.position_count == 1
