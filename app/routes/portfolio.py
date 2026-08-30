from fastapi import APIRouter, Header, HTTPException

from app.services.portfolio_service import portfolio_service
from app.services.auth_service import auth_service
from app.services.audit_service import audit_service


router = APIRouter(
    prefix="/api/portfolio",
    tags=["Portfolio"],
)


def require_auth(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format",
        )

    token = authorization[7:].strip()

    result = auth_service.verify_token(token)

    if not result.authenticated:
        audit_service.record(
            "PORTFOLIO_AUTHORIZATION",
            "REJECTED",
            {"reason": result.reason},
        )

        raise HTTPException(
            status_code=401,
            detail=result.reason,
        )

    return token


@router.get("/summary")
async def get_portfolio_summary(
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)

    summary = portfolio_service.get_summary()

    audit_service.record(
        "PORTFOLIO_SUMMARY",
        "SUCCESS",
        {
            "position_count": summary.position_count,
        },
    )

    return {
        "cash": summary.cash,
        "equity": summary.equity,
        "unrealized_pnl": summary.unrealized_pnl,
        "position_count": summary.position_count,
    }


@router.get("/positions")
async def get_portfolio_positions(
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)

    positions = portfolio_service.get_positions()

    audit_service.record(
        "PORTFOLIO_POSITIONS",
        "SUCCESS",
        {
            "position_count": len(positions),
        },
    )

    return {
        "positions": [
            {
                "symbol": position.symbol,
                "side": position.side,
                "quantity": position.quantity,
                "entry_price": position.entry_price,
                "stop_loss": position.stop_loss,
                "take_profit": position.take_profit,
            }
            for position in positions
        ]
    }


@router.get("/positions/{symbol}")
async def get_portfolio_position(
    symbol: str,
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)

    position = portfolio_service.get_position(symbol)

    if position is None:
        raise HTTPException(
            status_code=404,
            detail="Position not found",
        )

    audit_service.record(
        "PORTFOLIO_POSITION",
        "SUCCESS",
        {
            "symbol": position.symbol,
        },
    )

    return {
        "symbol": position.symbol,
        "side": position.side,
        "quantity": position.quantity,
        "entry_price": position.entry_price,
        "stop_loss": position.stop_loss,
        "take_profit": position.take_profit,
          }
