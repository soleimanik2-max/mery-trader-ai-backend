from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.services.auth_service import auth_service
from app.services.order_management import (
    OrderManagementService,
    OrderRequest,
)


router = APIRouter(prefix="/api/orders", tags=["Orders"])


class OrderAPIRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    side: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    entry_price: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)


class OrderSecurityRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    side: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    entry_price: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    system_enabled: bool = True
    risk_approved: bool = False


def get_authenticated_user(authorization: str | None):
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:].strip()

    if not token:
        return None

    result = auth_service.verify_token(token)

    if not result.authenticated:
        return None

    return result


def build_order(request: OrderAPIRequest | OrderSecurityRequest):
    return OrderRequest(
        symbol=request.symbol.strip(),
        side=request.side.strip().upper(),
        quantity=request.quantity,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
    )


@router.post("/validate")
async def validate_order(
    request: OrderAPIRequest,
    authorization: str | None = Header(default=None),
):
    user = get_authenticated_user(authorization)

    if user is None:
        return {
            "approved": False,
            "reason": "Authentication required",
        }

    order = build_order(request)

    result = OrderManagementService.validate_order(order)

    return {
        "approved": result.approved,
        "reason": result.reason,
        "user_id": user.user_id,
        "role": user.role,
    }


@router.post("/security-check")
async def security_check(
    request: OrderSecurityRequest,
    authorization: str | None = Header(default=None),
):
    user = get_authenticated_user(authorization)

    if user is None:
        return {
            "approved": False,
            "reason": "Authentication required",
        }

    token = authorization[7:].strip()

    permission = auth_service.authorize(
        token=token,
        permission="MANAGE_ORDERS",
    )

    if not permission.authenticated:
        return {
            "approved": False,
            "reason": permission.reason,
            "user_id": user.user_id,
            "role": user.role,
        }

    order = build_order(request)

    result = OrderManagementService.security_check(
        order=order,
        system_enabled=request.system_enabled,
        authenticated=True,
        risk_approved=request.risk_approved,
        token=token,
    )

    return {
        "approved": result.approved,
        "reason": result.reason,
        "user_id": user.user_id,
        "role": user.role,
    }
