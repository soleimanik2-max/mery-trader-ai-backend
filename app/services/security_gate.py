from dataclasses import dataclass


@dataclass
class SecurityCheckResult:
    approved: bool
    reason: str


class SecurityGate:
    """Safety gate before any order execution."""

    @staticmethod
    def check(
        system_enabled: bool,
        authenticated: bool,
        order_valid: bool,
        risk_approved: bool,
    ) -> SecurityCheckResult:

        if not system_enabled:
            return SecurityCheckResult(
                approved=False,
                reason="Trading system is disabled",
            )

        if not authenticated:
            return SecurityCheckResult(
                approved=False,
                reason="Authentication required",
            )

        if not order_valid:
            return SecurityCheckResult(
                approved=False,
                reason="Order validation failed",
            )

        if not risk_approved:
            return SecurityCheckResult(
                approved=False,
                reason="Risk approval required",
            )

        return SecurityCheckResult(
            approved=True,
            reason="Security checks passed",
        )


security_gate = SecurityGate()
