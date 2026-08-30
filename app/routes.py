from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.ai_decision import ai_decision_service
from app.services.audit_service import audit_service
from app.services.auth_service import auth_service
from app.services.market_data import market_data_service
from app.services.risk_management import risk_management_service
from app.services.technical_analysis import technical_analysis_service


router = APIRouter()


class AuthRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="USER", min_length=1, max_length=20)


class AuthorizeRequest(BaseModel):
    permission: str = Field(..., min_length=1, max_length=50)


class MarketDataRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    timeframe: str = Field(..., min_length=1, max_length=20)
    price: float = Field(..., gt=0)
    volume: float | None = Field(default=None, ge=0)


class AnalysisRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    prices: list[float] = Field(..., min_length=15)


class RiskRequest(BaseModel):
    active_capital: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    risk_percent: float = Field(..., ge=1, le=3)


@router.post("/api/auth")
async def authenticate(request: AuthRequest):
    result = auth_service.create_token(
        user_id=request.user_id,
        role=request.role,
    )

    audit_service.record(
        "AUTHENTICATION",
        "SUCCESS" if result.authenticated else "REJECTED",
        {
            "user_id": request.user_id,
            "role": request.role.upper(),
        },
    )

    return {
        "authenticated": result.authenticated,
        "token": result.token,
        "reason": result.reason,
        "user_id": result.user_id,
        "role": result.role,
    }


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
            "AUTHORIZATION",
            "REJECTED",
            {"reason": result.reason},
        )

        raise HTTPException(
            status_code=401,
            detail=result.reason,
        )

    return token


@router.post("/api/authorize")
async def authorize(
    request: AuthorizeRequest,
    authorization: str | None = Header(default=None),
):
    token = require_auth(authorization)

    result = auth_service.authorize(
        token=token,
        permission=request.permission,
    )

    if not result.authenticated:
        audit_service.record(
            "AUTHORIZATION",
            "DENIED",
            {
                "permission": request.permission,
                "user_id": result.user_id,
                "role": result.role,
                "reason": result.reason,
            },
        )

        return JSONResponse(
            status_code=403,
            content={
                "authorized": False,
                "permission": request.permission,
                "user_id": result.user_id,
                "role": result.role,
                "reason": result.reason,
            },
        )

    audit_service.record(
        "AUTHORIZATION",
        "APPROVED",
        {
            "permission": request.permission,
            "user_id": result.user_id,
            "role": result.role,
        },
    )

    return {
        "authorized": True,
        "permission": request.permission,
        "user_id": result.user_id,
        "role": result.role,
        "reason": result.reason,
    }


@router.post("/api/market-data")
async def update_market_data(
    request: MarketDataRequest,
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)

    result = market_data_service.update(
        symbol=request.symbol,
        timeframe=request.timeframe,
        price=request.price,
        volume=request.volume,
    )

    audit_service.record(
        "MARKET_DATA_UPDATE",
        "SUCCESS",
        {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
        },
    )

    return result


@router.post("/api/analyze")
async def analyze_market(
    request: AnalysisRequest,
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)

    ema20 = technical_analysis_service.ema(request.prices, 20)
    ema50 = technical_analysis_service.ema(request.prices, 50)
    rsi14 = technical_analysis_service.rsi(request.prices, 14)

    decision = ai_decision_service.analyze(
        price=request.prices[-1],
        ema20=ema20,
        ema50=ema50,
        rsi14=rsi14,
    )

    result = {
        "symbol": request.symbol,
        "ema20": ema20,
        "ema50": ema50,
        "rsi14": rsi14,
        "decision": decision.decision,
        "confidence": decision.confidence,
        "reason": decision.reason,
    }

    audit_service.record(
        "MARKET_ANALYSIS",
        "SUCCESS",
        {
            "symbol": request.symbol,
            "decision": decision.decision,
            "confidence": decision.confidence,
        },
    )

    return result


@router.post("/api/risk")
async def calculate_risk(
    request: RiskRequest,
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)

    result = risk_management_service.calculate_position_size(
        active_capital=request.active_capital,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        risk_percent=request.risk_percent,
    )

    response = {
        "approved": result.approved,
        "risk_amount": result.risk_amount,
        "position_size": result.position_size,
        "reason": result.reason,
    }

    audit_service.record(
        "RISK_CALCULATION",
        "APPROVED" if result.approved else "REJECTED",
        {
            "risk_percent": request.risk_percent,
            "approved": result.approved,
        },
    )

    return response
