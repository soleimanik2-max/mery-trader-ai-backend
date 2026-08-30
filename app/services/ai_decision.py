from dataclasses import dataclass
from typing import Optional


@dataclass
class DecisionResult:
    decision: str
    confidence: float
    reason: str


class AIDecisionService:
    """Basic decision layer for MERY TRADER AI."""

    VALID_DECISIONS = {
        "STRONG BUY",
        "BUY",
        "WAIT",
        "SELL",
        "STRONG SELL",
    }

    @staticmethod
    def analyze(
        price: float,
        ema20: Optional[float] = None,
        ema50: Optional[float] = None,
        rsi14: Optional[float] = None,
    ) -> DecisionResult:

        if price <= 0:
            return DecisionResult(
                decision="WAIT",
                confidence=0,
                reason="Invalid market price",
            )

        if ema20 is None or ema50 is None or rsi14 is None:
            return DecisionResult(
                decision="WAIT",
                confidence=20,
                reason="Insufficient technical data",
            )

        if ema20 > ema50 and rsi14 < 70:
            return DecisionResult(
                decision="BUY",
                confidence=70,
                reason="EMA20 above EMA50 with RSI below 70",
            )

        if ema20 < ema50 and rsi14 > 30:
            return DecisionResult(
                decision="SELL",
                confidence=70,
                reason="EMA20 below EMA50 with RSI above 30",
            )

        return DecisionResult(
            decision="WAIT",
            confidence=50,
            reason="No strong directional confirmation",
        )


ai_decision_service = AIDecisionService()
