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

    Strictly simulated trading.
    This service does NOT connect to any real exchange
    and does NOT execute real-money orders.
    """

    VALID_SIDES = {"BUY", "SELL"}

    DEFAULT_FEE_RATE = 0.001
    DEFAULT_SLIPPAGE_RATE = 0.0005

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)

    @staticmethod
    def get_or_create_account(
        db: Session,
        user_id: str,
        starting_capital: float,
    ) -> PaperAccount:

        account = (
            db.query(PaperAccount)
            .filter(PaperAccount.user_id == user_id)
            .first()
        )

        if account is not None:
            return account

        if starting_capital <= 0:
            raise ValueError("Starting capital must be greater than zero.")

        account = PaperAccount(
            user_id=user_id,
            starting_capital=float(starting_capital),
            cash=float(starting_capital),
            realized_pnl=0.0,
            total_fees=0.0,
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        return account

    @staticmethod
    def get_account(
        db: Session,
        user_id: str,
    ) -> PaperAccount | None:

        return (
            db.query(PaperAccount)
            .filter(PaperAccount.user_id == user_id)
            .first()
        )

    @staticmethod
    def _validate_trade_parameters(
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float | None,
        take_profit: float | None,
    ) -> str | None:

        if not symbol or not symbol.strip():
            return "Symbol is required."

        if side not in PaperTradingService.VALID_SIDES:
            return "Side must be BUY or SELL."

        if quantity <= 0:
            return "Quantity must be greater than zero."

        if entry_price <= 0:
            return "Entry price must be greater than zero."

        if side == "BUY":
            if stop_loss is not None and stop_loss >= entry_price:
                return "For BUY, stop loss must be below entry price."

            if take_profit is not None and take_profit <= entry_price:
                return "For BUY, take profit must be above entry price."

        if side == "SELL":
            if stop_loss is not None and stop_loss <= entry_price:
                return "For SELL, stop loss must be above entry price."

            if take_profit is not None and take_profit >= entry_price:
                return "For SELL, take profit must be below entry price."

        return None

    @staticmethod
    def open_trade(
        db: Session,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        starting_capital: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        fee_rate: float = DEFAULT_FEE_RATE,
        slippage_rate: float = DEFAULT_SLIPPAGE_RATE,
    ) -> PaperTradeResult:

        error = PaperTradingService._validate_trade_parameters(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        if error:
            return PaperTradeResult(
                approved=False,
                trade_id=None,
                reason=error,
                cash=0.0,
                realized_pnl=0.0,
                status="REJECTED",
            )

        account = PaperTradingService.get_or_create_account(
            db=db,
            user_id=user_id,
            starting_capital=starting_capital,
        )

        notional = quantity * entry_price
        fee = notional * fee_rate
        slippage = notional * slippage_rate

        if side == "BUY":
            total_cost = notional + fee + slippage

            if account.cash < total_cost:
                return PaperTradeResult(
                    approved=False,
                    trade_id=None,
                    reason="Insufficient paper account cash.",
                    cash=account.cash,
                    realized_pnl=0.0,
                    status="REJECTED",
                )

            account.cash -= total_cost

        else:
            account.cash += notional - fee - slippage

        trade = Trade(
            user_id=user_id,
            symbol=symbol.upper(),
            side=side,
            entry_price=float(entry_price),
            exit_price=None,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=float(quantity),
            status="OPEN",
            realized_pnl=0.0,
            fee=float(fee),
            slippage=float(slippage),
            created_at=PaperTradingService._now(),
        )

        db.add(trade)

        account.total_fees += fee
        account.updated_at = PaperTradingService._now()

        db.commit()
        db.refresh(trade)
        db.refresh(account)

        return PaperTradeResult(
            approved=True,
            trade_id=trade.id,
            reason="Paper trade opened successfully.",
            cash=account.cash,
            realized_pnl=0.0,
            status="OPEN",
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
                approved=False,
                trade_id=trade_id,
                reason="Exit price must be greater than zero.",
                cash=0.0,
                realized_pnl=0.0,
                status="REJECTED",
            )

        trade = (
            db.query(Trade)
            .filter(
                Trade.id == trade_id,
                Trade.user_id == user_id,
            )
            .first()
        )

        if trade is None:
            return PaperTradeResult(
                approved=False,
                trade_id=trade_id,
                reason="Trade not found.",
                cash=0.0,
                realized_pnl=0.0,
                status="REJECTED",
            )

        if trade.status != "OPEN":
            return PaperTradeResult(
                approved=False,
                trade_id=trade_id,
                reason="Trade is not open.",
                cash=0.0,
                realized_pnl=0.0,
                status=trade.status,
            )

        account = PaperTradingService.get_account(
            db=db,
            user_id=user_id,
        )

        if account is None:
            return PaperTradeResult(
                approved=False,
                trade_id=trade_id,
                reason="Paper account not found.",
                cash=0.0,
                realized_pnl=0.0,
                status="REJECTED",
            )

        exit_notional = trade.quantity * exit_price
        close_fee = exit_notional * fee_rate
        close_slippage = exit_notional * slippage_rate

        if trade.side == "BUY":
            gross_pnl = (
                exit_price - trade.entry_price
            ) * trade.quantity

            account.cash += (
                exit_notional
                - close_fee
                - close_slippage
            )

        else:
            gross_pnl = (
                trade.entry_price - exit_price
            ) * trade.quantity

            account.cash -= (
                exit_notional
                + close_fee
                + close_slippage
            )

        total_trade_costs = (
            trade.fee
            + trade.slippage
            + close_fee
            + close_slippage
        )

        realized_pnl = gross_pnl - total_trade_costs

        trade.exit_price = float(exit_price)
        trade.status = "CLOSED"
        trade.realized_pnl = float(realized_pnl)
        trade.fee += float(close_fee)
        trade.slippage += float(close_slippage)
        trade.closed_at = PaperTradingService._now()

        account.realized_pnl += float(realized_pnl)
        account.total_fees += float(close_fee)
        account.updated_at = PaperTradingService._now()

        db.commit()
        db.refresh(trade)
        db.refresh(account)

        return PaperTradeResult(
            approved=True,
            trade_id=trade.id,
            reason="Paper trade closed successfully.",
            cash=account.cash,
            realized_pnl=realized_pnl,
            status="CLOSED",
        )

    @staticmethod
    def get_open_trades(
        db: Session,
        user_id: str,
    ) -> list[Trade]:

        return (
            db.query(Trade)
            .filter(
                Trade.user_id == user_id,
                Trade.status == "OPEN",
            )
            .order_by(Trade.created_at.desc())
            .all()
        )

    @staticmethod
    def get_trade_history(
        db: Session,
        user_id: str,
    ) -> list[Trade]:

        return (
            db.query(Trade)
            .filter(Trade.user_id == user_id)
            .order_by(Trade.created_at.desc())
            .all()
        )

    @staticmethod
    def get_unrealized_pnl(
        db: Session,
        user_id: str,
        current_prices: dict[str, float],
    ) -> float:

        trades = PaperTradingService.get_open_trades(
            db=db,
            user_id=user_id,
        )

        unrealized_pnl = 0.0

        for trade in trades:
            current_price = current_prices.get(
                trade.symbol.upper()
            )

            if current_price is None or current_price <= 0:
                continue

            if trade.side == "BUY":
                unrealized_pnl += (
                    current_price - trade.entry_price
                ) * trade.quantity
            else:
                unrealized_pnl += (
                    trade.entry_price - current_price
                ) * trade.quantity

        return float(unrealized_pnl)

    @staticmethod
    def calculate_equity(
        db: Session,
        user_id: str,
        current_prices: dict[str, float],
    ) -> float:

        account = PaperTradingService.get_account(
            db=db,
            user_id=user_id,
        )

        if account is None:
            return 0.0

        equity = account.cash

        open_trades = PaperTradingService.get_open_trades(
            db=db,
            user_id=user_id,
        )

        for trade in open_trades:
            current_price = current_prices.get(
                trade.symbol.upper()
            )

            if current_price is None or current_price <= 0:
                continue

            if trade.side == "BUY":
                equity += current_price * trade.quantity
            else:
                equity -= current_price * trade.quantity

        return float(equity)

    @staticmethod
    def evaluate_trade_exit(
        trade: Trade,
        current_price: float,
    ) -> str | None:

        if trade.status != "OPEN":
            return None

        if current_price <= 0:
            return None

        if trade.side == "BUY":

            if (
                trade.stop_loss is not None
                and current_price <= trade.stop_loss
            ):
                return "STOP_LOSS"

            if (
                trade.take_profit is not None
                and current_price >= trade.take_profit
            ):
                return "TAKE_PROFIT"

        if trade.side == "SELL":

            if (
                trade.stop_loss is not None
                and current_price >= trade.stop_loss
            ):
                return "STOP_LOSS"

            if (
                trade.take_profit is not None
                and current_price <= trade.take_profit
            ):
                return "TAKE_PROFIT"

        return None

    @staticmethod
    def process_market_price(
        db: Session,
        user_id: str,
        symbol: str,
        current_price: float,
    ) -> list[PaperTradeResult]:

        if current_price <= 0:
            return []

        results = []

        open_trades = PaperTradingService.get_open_trades(
            db=db,
            user_id=user_id,
        )

        for trade in open_trades:

            if trade.symbol.upper() != symbol.upper():
                continue

            exit_reason = PaperTradingService.evaluate_trade_exit(
                trade=trade,
                current_price=current_price,
            )

            if exit_reason is None:
                continue

            result = PaperTradingService.close_trade(
                db=db,
                user_id=user_id,
                trade_id=trade.id,
                exit_price=current_price,
            )

            if result.approved:
                result.reason = (
                    f"Paper trade closed by {exit_reason}."
                )

            results.append(result)

        return results