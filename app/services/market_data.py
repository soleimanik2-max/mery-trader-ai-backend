from datetime import datetime, timezone
from typing import Optional


class MarketDataService:
    """Basic market data service for MERY TRADER AI."""

    def __init__(self):
        self.last_data = {}

    def update(
        self,
        symbol: str,
        timeframe: str,
        price: float,
        volume: Optional[float] = None,
    ) -> dict:
        data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": price,
            "volume": volume,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.last_data[symbol] = data
        return data

    def get(self, symbol: str) -> Optional[dict]:
        return self.last_data.get(symbol)


market_data_service = MarketDataService()
