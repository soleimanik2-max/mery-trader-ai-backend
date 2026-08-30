from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.services.auth_service import auth_service
from app.services.execution_service import execution_service
from app.services.order_management import OrderRequest


router = APIRouter(
    prefix="/api/execution",
    tags=["Execution"],
)


class PaperOrderRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    side: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    entry_price: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    system_enabled: bool = True
    risk_approved: bool = False


def get_authenticated_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[7:].strip()

    result = auth_service.verify_token(token)

    if not result.authenticated:
        return None

    return result


@router.post("/paper-order")
async def execute_paper_order(
    request: PaperOrderRequest,
    authorization: str | None = Header(default=None),
):
    user = get_authenticated_user(authorization)

    if user is None:
        return {
            "executed": False,
            "order_id": None,
            "reason": "Authentication required",
        }

    order = OrderRequest(
        symbol=request.symbol,
        side=request.side.upper(),
        quantity=request.quantity,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
    )

    result = execution_service.execute_paper_order(
        order=order,
        system_enabled=request.system_enabled,
        authenticated=True,
        risk_approved=request.risk_approved,
    )

    return {
        "executed": result.executed,
        "order_id": result.order_id,
        "reason": result.reason,
        "user_id": user.user_id,
        "role": user.role,
  }
