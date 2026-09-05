from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models import PaperAccount, Trade


@dataclass
class PaperTradeResult:
    approved: bool
    trade_id: int | None
    reason: str
    cash: float
    realized_pnl: float
    status: str


class PaperTradingService:
    """
    MERY TRADER AI - Paper Trading Engine

    This service is strictly for simulated trading.
    It does NOT connect to any real exchange and does NOT
    execute real-money orders.
    """

    VALID_SIDES = {"BUY", "SELL"}

    DEFAULT_FEE_RATE = 0.001
    DEFAULT_SLIPPAGE_RATE = 0.0005

    @staticmethod
    def get_or_create_account(
        db: Session,
        user_id: str,
        starting_capital: float,
    ) -> PaperAccount:

        if not user_id:
            raise ValueError("User ID is required")

        if starting_capital <= 0:
            raise ValueError("Starting capital must be greater than zero")

        account = (
            db.query(PaperAccount)
            .filter(PaperAccount.user_id == user_id)
            .first()
        )

        if account is not None:
            return account

        account = PaperAccount(
            user_id=user_id,
            starting_capital=starting_capital,
            cash=starting_capital,
            realized_pnl=0.0,
            total_fees=0.0,
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        return account

    @staticmethod
    def open_trade(
        db: Session,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        fee_rate: float = DEFAULT_FEE_RATE,
        slippage_rate: float = DEFAULT_SLIPPAGE_RATE,
    ) -> PaperTradeResult:

        symbol = symbol.strip().upper()
        side = side.strip().upper()

        if not symbol:
            return PaperTradeResult(
                False, None, "Symbol is required", 0.0, 0.0, "REJECTED"
            )

        if side not in PaperTradingService.VALID_SIDES:
            return PaperTradeResult(
                False, None, "Side must be BUY or SELL", 0.0, 0.0, "REJECTED"
            )

        if quantity <= 0:
            return PaperTradeResult(
                False, None, "Quantity must be greater than zero",
                0.0, 0.0, "REJECTED"
            )

        if entry_price <= 0:
            return PaperTradeResult(
                False, None, "Entry price must be greater than zero",
                0.0, 0.0, "REJECTED"
            )

        if stop_loss is not None and stop_loss <= 0:
            return PaperTradeResult(
                False, None, "Stop loss must be greater than zero",
                0.0, 0.0, "REJECTED"
            )

        if take_profit is not None and take_profit <= 0:
            return PaperTradeResult(
                False, None, "Take profit must be greater than zero",
                0.0, 0.0, "REJECTED"
            )

        if fee_rate < 0 or slippage_rate < 0:
            return PaperTradeResult(
                False, None, "Fee and slippage rates cannot be negative",
                0.0, 0.0, "REJECTED"
            )

        # Validate SL direction.
        if stop_loss is not None:
            if side == "BUY" and stop_loss >= entry_price:
                return PaperTradeResult(
                    False, None,
                    "For BUY, stop loss must be below entry price",
                    0.0, 0.0, "REJECTED"
                )

            if side == "SELL" and stop_loss <= entry_price:
                return PaperTradeResult(
                    False, None,
                    "For SELL, stop loss must be above entry price",
                    0.0, 0.0, "REJECTED"
                )

        # Validate TP direction.
        if take_profit is not None:
            if side == "BUY" and take_profit <= entry_price:
                return PaperTradeResult(
                    False, None,
                    "For BUY, take profit must be above entry price",
                    0.0, 0.0, "REJECTED"
                )

            if side == "SELL" and take_profit >= entry_price:
                return PaperTradeResult(
                    False, None,
                    "For SELL, take profit must be below entry price",
                    0.0, 0.0, "REJECTED"
                )

        account = PaperTradingService.get_or_create_account(
            db=db,
            user_id=user_id,
            starting_capital=0.0 if False else 10000.0,
        )

        # Simulated execution price after slippage.
        if side == "BUY":
            execution_price = entry_price * (1 + slippage_rate)
        else:
            execution_price = entry_price * (1 - slippage_rate)

        notional = execution_price * quantity
        fee = notional * fee_rate

        total_cost = notional + fee

        if side == "BUY":
            if account.cash < total_cost:
                return PaperTradeResult(
                    False,
                    None,
                    "Insufficient paper trading cash",
                    account.cash,
                    0.0,
                    "REJECTED",
                )

            account.cash -= total_cost

        else:
            # Short selling is simulated without borrowing costs.
            # Risk controls will be enforced by the higher-level
            # order/risk layer.
            account.cash += notional - fee

        trade = Trade(
            symbol=symbol,
            side=side,
            entry_price=execution_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            status="OPEN",
            realized_pnl=0.0,
            fee=fee,
            slippage=abs(execution_price - entry_price) * quantity,
            created_at=datetime.now(timezone.utc),
        )

        account.total_fees += fee
        account.updated_at = datetime.now(timezone.utc)

        db.add(trade)
        db.add(account)
        db.commit()
        db.refresh(trade)
        db.refresh(account)

        return PaperTradeResult(
            approved=True,
            trade_id=trade.id,
            reason="Paper trade opened successfully",
            cash=account.cash,
            realized_pnl=account.realized_pnl,
            status=trade.status,
        )

    @staticmethod
    def close_trade(
        db: Session,
        user_id: str,
        trade_id: int,
        exit_price: float,
        fee_rate: float = DEFAULT_FEE_RATE,
        slippage_rate: float = DEFAULT_SLIPPAGE_RATE,
    ) -> PaperTradeResult:

        if exit_price <= 0:
            return PaperTradeResult(
                False, None,
                "Exit price must be greater than zero",
                0.0, 0.0, "REJECTED"
            )

        trade = (
            db.query(Trade)
            .filter(
                Trade.id == trade_id,
                Trade.status == "OPEN",
            )
            .first()
        )

        if trade is None:
            return PaperTradeResult(
                False, None,
                "Open paper trade not found",
                0.0, 0.0, "REJECTED"
            )

        account = (
            db.query(PaperAccount)
            .filter(PaperAccount.user_id == user_id)
            .first()
        )

        if account is None:
            return PaperTradeResult(
                False