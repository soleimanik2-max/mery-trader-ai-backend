from dataclasses import dataclass


@dataclass
class RiskResult:
    approved: bool
    risk_amount: float
    position_size: float
    reason: str


class RiskManagementService:
    """Capital protection rules for MERY TRADER AI."""

    MIN_RISK_PERCENT = 1.0
    MAX_RISK_PERCENT = 3.0
    MAX_OPEN_RISK_PERCENT = 5.0
    DAILY_LOSS_LIMIT_PERCENT = 3.0
    MAX_DRAWDOWN_PERCENT = 5.0

    @classmethod
    def calculate_position_size(
        cls,
        active_capital: float,
        entry_price: float,
        stop_loss: float,
        risk_percent: float,
    ) -> RiskResult:

        if active_capital <= 0:
            return RiskResult(False, 0, 0, "Invalid active capital")

        if entry_price <= 0 or stop_loss <= 0:
            return RiskResult(False, 0, 0, "Invalid entry or stop-loss")

        if risk_percent < cls.MIN_RISK_PERCENT:
            return RiskResult(False, 0, 0, "Risk is below minimum")

        if risk_percent > cls.MAX_RISK_PERCENT:
            return RiskResult(False, 0, 0, "Risk exceeds maximum")

        if entry_price == stop_loss:
            return RiskResult(
                False, 0, 0, "Entry and stop-loss cannot be equal"
            )

        risk_amount = active_capital * (risk_percent / 100)
        price_risk = abs(entry_price - stop_loss)
        position_size = risk_amount / price_risk

        return RiskResult(
            approved=True,
            risk_amount=risk_amount,
            position_size=position_size,
            reason="Risk parameters approved",
        )


risk_management_service = RiskManagementService()
