from dataclasses import dataclass
from typing import Optional


@dataclass
class Position:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class PortfolioSummary:
    cash: float
    equity: float
    unrealized_pnl: float
    position_count: int


class PortfolioService:
    """Paper portfolio and position management for MERY TRADER AI."""

    VALID_SIDES = {"BUY", "SELL"}

    def __init__(self):
        self._cash = 0.0
        self._positions: dict[str, Position] = {}

    def set_cash(self, amount: float) -> bool:
        if amount < 0:
            return False

        self._cash = amount
        return True

    def add_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Position:

        symbol = symbol.strip().upper()
        side = side.strip().upper()

        if not symbol:
            raise ValueError("Symbol is required")

        if side not in self.VALID_SIDES:
            raise ValueError("Invalid position side")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        if entry_price <= 0:
            raise ValueError("Entry price must be greater than zero")

        if stop_loss is not None and stop_loss <= 0:
            raise ValueError("Stop-loss must be greater than zero")

        if take_profit is not None and take_profit <= 0:
            raise ValueError("Take-profit must be greater than zero")

        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        self._positions[symbol] = position
        return position

    def get_position(self, symbol: str) -> Optional[Position]:
        return self._positions.get(symbol.strip().upper())

    def remove_position(self, symbol: str) -> bool:
        symbol = symbol.strip().upper()

        if symbol not in self._positions:
            return False

        del self._positions[symbol]
        return True

    def calculate_unrealized_pnl(
        self,
        symbol: str,
        current_price: float,
    ) -> float:

        if current_price <= 0:
            raise ValueError("Current price must be greater than zero")

        position = self.get_position(symbol)

        if position is None:
            return 0.0

        price_difference = (
            current_price - position.entry_price
        )

        if position.side == "SELL":
            price_difference = -price_difference

        return price_difference * position.quantity

    def get_summary(
        self,
        current_prices: Optional[dict[str, float]] = None,
    ) -> PortfolioSummary:

        current_prices = current_prices or {}

        unrealized_pnl = 0.0

        for symbol, position in self._positions.items():
            current_price = current_prices.get(
                symbol,
                position.entry_price,
            )

            unrealized_pnl += self.calculate_unrealized_pnl(
                symbol,
                current_price,
            )

        equity = self._cash + unrealized_pnl

        return PortfolioSummary(
            cash=self._cash,
            equity=equity,
            unrealized_pnl=unrealized_pnl,
            position_count=len(self._positions),
        )

    def get_positions(self) -> list[Position]:
        return list(self._positions.values())


portfolio_service = PortfolioService()
