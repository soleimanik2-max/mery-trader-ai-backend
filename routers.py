from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database import get_db
from app.services.ai_decision import ai_decision_service
from app.services.audit_service import audit_service
from app.services.auth_service import auth_service
from app.services.market_data import market_data_service
from app.services.order_management import (
    OrderManagementService,
    OrderRequest,
)
from app.services.portfolio_service import portfolio_service
from app.services.risk_management import risk_management_service
from app.services.technical_analysis import technical_analysis_service
from app.services.paper_trading import PaperTradingService

router = APIRouter()

# ---------------------------------------------------------------------------
# API STATUS / VERSION
# ---------------------------------------------------------------------------

@router.get("/api/status")
async def api_status():
    return {
        "service": "MERY TRADER AI Backend",
        "status": "operational",
    }


@router.get("/api/version")
async def api_version():
    return {
        "version": "1.0.0",
    }

# ---------------------------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------------

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

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    result = auth_service.verify_token(token)
    if not result.authenticated:
        audit_service.record(
            "AUTHORIZATION",
            "REJECTED",
            {
                "reason": result.reason,
            },
        )

        raise HTTPException(
            status_code=401,
            detail=result.reason,
        )

    return token

# ---------------------------------------------------------------------------
# AUTHORIZATION
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# MARKET DATA
# ---------------------------------------------------------------------------

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
# ---------------------------------------------------------------------------
# AI MARKET ANALYSIS
# ---------------------------------------------------------------------------

@router.post("/api/analyze")
async def analyze_market(
    request: AnalysisRequest,
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)

    ema20 = technical_analysis_service.ema(
        request.prices,
        20,
    )

    ema50 = technical_analysis_service.ema(
        request.prices,
        50,
    )

    rsi14 = technical_analysis_service.rsi(
        request.prices,
        14,
    )

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


# ---------------------------------------------------------------------------
# RISK MANAGEMENT
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# ORDER MANAGEMENT
# ---------------------------------------------------------------------------

@router.post("/api/orders/validate")
async def validate_order(
    request: OrderAPIRequest,
    authorization: str | None = Header(default=None),
):
    require_auth(authorization)

    order = OrderRequest(
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
    )

    service = OrderManagementService()

    result = service.validate_order(order)

    audit_service.record(
        "ORDER_VALIDATION",
        "APPROVED" if result.valid else "REJECTED",
        {
            "symbol": request.symbol,
            "side": request.side,
            "quantity": request.quantity,
        },
    )

    return {
        "valid": result.valid,
        "reason": result.reason,
        "symbol": request.symbol,
        "side": request.side,
        "quantity": request.quantity,
        "entry_price": request.entry_price,
        "stop_loss": request.stop_loss,
        "take_profit": request.take_profit,
    }


@router.post("/api/orders")
async def create_order(
    request: OrderSecurityRequest,
    authorization: str | None = Header(default=None),
):
    token = require_auth(authorization)

    auth_result = auth_service.verify_token(token)

    if not auth_result.authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    order = OrderRequest(
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
    )

    service = OrderManagementService()

    validation = service.validate_order(order)

    if not validation.valid:
        audit_service.record(
            "ORDER",
            "REJECTED",
            {
                "user_id": auth_result.user_id,
                "symbol": request.symbol,
                "reason": validation.reason,
            },
        )

        return {
            "accepted": False,
            "executed": False,
            "status": "REJECTED",
            "reason": validation.reason,
        }

    if not request.system_enabled:
        audit_service.record(
            "ORDER",
            "REJECTED",
            {
                "user_id": auth_result.user_id,
                "symbol": request.symbol,
                "reason": "Trading system is disabled",
            },
        )

        return {
            "accepted": False,
            "executed": False,
            "status": "REJECTED",
            "reason": "Trading system is disabled",
        }

    if not request.risk_approved:
        audit_service.record(
            "ORDER",
            "REJECTED",
            {
                "user_id": auth_result.user_id,
                "symbol": request.symbol,
                "reason": "Risk approval required",
            },
        )

        return {
            "accepted": False,
            "executed": False,
            "status": "REJECTED",
            "reason": "Risk approval required",
# ---------------------------------------------------------------------------
# PAPER TRADING - CLOSE TRADE
# ---------------------------------------------------------------------------

@router.post("/api/paper-trading/close")
async def close_paper_trade(
    request: PaperTradeCloseRequest,
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)

    auth_result = auth_service.verify_token(token)

    if not auth_result.authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    service = PaperTradingService(db)

    result = service.close_trade(
        user_id=auth_result.user_id,
        trade_id=request.trade_id,
        exit_price=request.exit_price,
    )

    audit_service.record(
        "PAPER_TRADE_CLOSE",
        "SUCCESS" if result.get("success", False) else "REJECTED",
        {
            "user_id": auth_result.user_id,
            "trade_id": request.trade_id,
        },
    )

    return result


# ---------------------------------------------------------------------------
# PAPER TRADING - ACCOUNT
# ---------------------------------------------------------------------------

@router.get("/api/paper-trading/account")
async def get_paper_account(
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)

    auth_result = auth_service.verify_token(token)

    if not auth_result.authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    service = PaperTradingService(db)

    return service.get_account(
        user_id=auth_result.user_id,
    )


# ---------------------------------------------------------------------------
# PAPER TRADING - OPEN TRADES
# ---------------------------------------------------------------------------

@router.get("/api/paper-trading/open-trades")
async def get_open_paper_trades(
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)

    auth_result = auth_service.verify_token(token)

    if not auth_result.authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    service = PaperTradingService(db)

    return service.get_open_trades(
        user_id=auth_result.user_id,
    )


# ---------------------------------------------------------------------------
# PAPER TRADING - TRADE HISTORY
# ---------------------------------------------------------------------------

@router.get("/api/paper-trading/history")
async def get_paper_trade_history(
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)

    auth_result = auth_service.verify_token(token)

    if not auth_result.authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    service = PaperTradingService(db)

    return service.get_trade_history(
        user_id=auth_result.user_id,
    )


# ---------------------------------------------------------------------------
# PAPER TRADING - EQUITY
# ---------------------------------------------------------------------------

@router.get("/api/paper-trading/equity")
async def get_paper_equity(
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)

    auth_result = auth_service.verify_token(token)

    if not auth_result.authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    service = PaperTradingService(db)

    return service.get_equity(
        user_id=auth_result.user_id,
    )


# ---------------------------------------------------------------------------
# PAPER TRADING - UNREALIZED PNL
# ---------------------------------------------------------------------------

class PaperUnrealizedRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    current_price: float = Field(..., gt=0)


@router.post("/api/paper-trading/unrealized-pnl")
async def calculate_unrealized_pnl(
    request: PaperUnrealizedRequest,
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)

    auth_result = auth_service.verify_token(token)

    if not auth_result.authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    service = PaperTradingService(db)

    return service.calculate_unrealized_pnl(
        user_id=auth_result.user_id,
        symbol=request.symbol,
        current_price=request.current_price,
    )


# ---------------------------------------------------------------------------
# PAPER TRADING - EVALU
# ---------------------------------------------------------------------------
# ROOT / HEALTH
# ---------------------------------------------------------------------------

@router.get("/")
async def root():
    return {
        "app": "MERY TRADER AI",
        "status": "online",
    }


@router.get("/health")
async def health():
    return {
        "status": "healthy",
    }