from typing import List, Optional


class TechnicalAnalysisService:
    """Basic technical analysis calculations for MERY TRADER AI."""

    @staticmethod
    def ema(prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period or period <= 0:
            return None

        multiplier = 2 / (period + 1)
        ema_value = sum(prices[:period]) / period

        for price in prices[period:]:
            ema_value = (price - ema_value) * multiplier + ema_value

        return ema_value

    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> Optional[float]:
        if len(prices) <= period or period <= 0:
            return None

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]

            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))


technical_analysis_service = TechnicalAnalysisService()
