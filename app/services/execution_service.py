from dataclasses import dataclass
from typing import Optional

from app.services.audit_service import audit_service
from app.services.order_management import OrderRequest
from app.services.security_gate import security_gate


@dataclass
class ExecutionResult:
    executed: bool
    order_id: Optional[str]
    reason: str


class ExecutionService:
    """Safe paper-order execution layer for MERY TRADER AI."""

    def __init__(self):
        self._orders: dict[str, OrderRequest] = {}
        self._counter = 0

    def execute_paper_order(
        self,
        order: OrderRequest,
        system_enabled: bool,
        authenticated: bool,
        risk_approved: bool,
    ) -> ExecutionResult:

        validation = self._validate_order(order)

        if not validation.approved:
            return ExecutionResult(
                executed=False,
                order_id=None,
                reason=validation.reason,
            )

        security = security_gate.check(
            system_enabled=system_enabled,
            authenticated=authenticated,
            order_valid=True,
            risk_approved=risk_approved,
        )

        if not security.approved:
            audit_service.record(
                "PAPER_ORDER_EXECUTION",
                "REJECTED",
                {
                    "symbol": order.symbol,
                    "reason": security.reason,
                },
            )

            return ExecutionResult(
                executed=False,
                order_id=None,
                reason=security.reason,
            )

        self._counter += 1
        order_id = f"PAPER-{self._counter:06d}"

        self._orders[order_id] = order

        audit_service.record(
            "PAPER_ORDER_EXECUTION",
            "EXECUTED",
            {
                "order_id": order_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
            },
        )

        return ExecutionResult(
            executed=True,
            order_id=order_id,
            reason="Paper order executed successfully",
        )

    @staticmethod
    def _validate_order(order: OrderRequest):
        from app.services.order_management import (
            OrderManagementService,
        )

        return OrderManagementService.validate_order(order)

    def get_order(self, order_id: str) -> Optional[OrderRequest]:
        return self._orders.get(order_id)


execution_service = ExecutionService()
