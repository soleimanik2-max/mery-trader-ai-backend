from dataclasses import dataclass
from typing import Optional

from app.services.security_gate import security_gate


@dataclass
class OrderRequest:
    symbol: str
    side: str
    quantity: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class OrderValidation:
    approved: bool
    reason: str


class OrderManagementService:
    """Order validation and security-gate integration."""

    VALID_SIDES = {"BUY", "SELL"}

    @classmethod
    def validate_order(
        cls,
        order: OrderRequest,
    ) -> OrderValidation:

        if not order.symbol.strip():
            return OrderValidation(False, "Symbol is required")

        if order.side not in cls.VALID_SIDES:
            return OrderValidation(False, "Invalid order side")

        if order.quantity <= 0:
            return OrderValidation(False, "Quantity must be greater than zero")

        if order.entry_price is not None and order.entry_price <= 0:
            return OrderValidation(False, "Entry price must be greater than zero")

        if order.stop_loss is not None and order.stop_loss <= 0:
            return OrderValidation(False, "Stop-loss must be greater than zero")

        if order.take_profit is not None and order.take_profit <= 0:
            return OrderValidation(False, "Take-profit must be greater than zero")

        if (
            order.entry_price is not None
            and order.stop_loss is not None
            and order.entry_price == order.stop_loss
        ):
            return OrderValidation(
                False,
                "Entry price and stop-loss cannot be equal",
            )

        return OrderValidation(True, "Order validation passed")

    @classmethod
    def security_check(
        cls,
        order: OrderRequest,
        system_enabled: bool,
        authenticated: bool,
        risk_approved: bool,
    ) -> OrderValidation:

        validation = cls.validate_order(order)

        if not validation.approved:
            return validation

        security_result = security_gate.check(
            system_enabled=system_enabled,
            authenticated=authenticated,
            order_valid=validation.approved,
            risk_approved=risk_approved,
        )

        return OrderValidation(
            approved=security_result.approved,
            reason=security_result.reason,
        )


order_management_service = OrderManagementService()
