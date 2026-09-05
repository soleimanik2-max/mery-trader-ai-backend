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

def get_authenticated_user(
    authorization: str | None,
):
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


@router.post("/api/orders/validate")
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

    order = OrderRequest(
        symbol=request.symbol,
        side=request.side.upper(),
        quantity=request.quantity,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
    )

    result = OrderManagementService.validate_order(order)

    return {
        "approved": result.approved,
        "reason": result.reason,
        "user_id": user.user_id,
        "role": user.role,
    }


@router.post("/api/orders/security-check")
async def order_security_check(
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

    order = OrderRequest(
        symbol=request.symbol,
        side=request.side.upper(),
        quantity=request.quantity,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
    )

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
# ---------------------------------------------------------------------------
# PORTFOLIO
# ---------------------------------------------------------------------------

@router.get("/api/portfolio/summary")
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


@router.get("/api/portfolio/positions")
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


@router.get("/api/portfolio/positions/{symbol}")
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
        "symbol": symbol,
        "side": position.side,
        "quantity": position.quantity,
        "entry_price": position.entry_price,
        "stop_loss": position.stop_loss,
        "take_profit": position.take_profit,
    }
# ---------------------------------------------------------------------------
# PAPER TRADING
# ---------------------------------------------------------------------------

class PaperTradeOpenRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    side: str = Field(..., min_length=1, max_length=10)
    entry_price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    starting_capital: float = Field(..., gt=0)


class PaperTradeCloseRequest(BaseModel):
    trade_id: int = Field(..., gt=0)
    exit_price: float = Field(..., gt=0)


class PaperPriceRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., gt=0)


@router.post("/api/paper-trading/open")
async def open_paper_trade(
    request: PaperTradeOpenRequest,
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)
    auth_result = auth_service.verify_token(token)

    service = PaperTradingService(db)

    trade = service.open_trade(
        user_id=auth_result.user_id,
        symbol=request.symbol.upper(),
        side=request.side.upper(),
        entry_price=request.entry_price,
        quantity=request.quantity,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
        starting_capital=request.starting_capital,
    )

    audit_service.record(
        "PAPER_TRADE_OPEN",
        "SUCCESS",
        {
            "user_id": auth_result.user_id,
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
        },
    )

    return {
        "success": True,
        "trade": {
            "id": trade.id,
            "user_id": trade.user_id,
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit,
            "quantity": trade.quantity,
            "status": trade.status,
            "realized_pnl": trade.realized_pnl,
            "fee": trade.fee,
            "slippage": trade.slippage,
        },
    }
@router.post("/api/paper-trading/close")
async def close_paper_trade(
    request: PaperTradeCloseRequest,
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)
    auth_result = auth_service.verify_token(token)

    service = PaperTradingService(db)

    trade = service.close_trade(
        user_id=auth_result.user_id,
        trade_id=request.trade_id,
        exit_price=request.exit_price,
    )

    audit_service.record(
        "PAPER_TRADE_CLOSE",
        "SUCCESS",
        {
            "user_id": auth_result.user_id,
            "trade_id": trade.id,
            "symbol": trade.symbol,
        },
    )

    return {
        "success": True,
        "trade": {
            "id": trade.id,
            "user_id": trade.user_id,
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit,
            "quantity": trade.quantity,
            "status": trade.status,
            "realized_pnl": trade.realized_pnl,
            "fee": trade.fee,
            "slippage": trade.slippage,
            "closed_at": trade.closed_at,
        },
    }


@router.get("/api/paper-trading/account")
async def get_paper_account(
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)
    auth_result = auth_service.verify_token(token)

    service = PaperTradingService(db)

    account = service.get_account(
        user_id=auth_result.user_id,
    )

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Paper trading account not found",
        )

    return {
        "user_id": account.user_id,
        "starting_capital": account.starting_capital,
        "cash": account.cash,
        "realized_pnl": account.realized_pnl,
        "total_fees": account.total_fees,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }
@router.get("/api/paper-trading/open-trades")
async def get_paper_open_trades(
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)
    auth_result = auth_service.verify_token(token)

    service = PaperTradingService(db)

    trades = service.get_open_trades(
        user_id=auth_result.user_id,
    )

    return {
        "user_id": auth_result.user_id,
        "trades": [
            {
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "entry_price": trade.entry_price,
                "stop_loss": trade.stop_loss,
                "take_profit": trade.take_profit,
                "quantity": trade.quantity,
                "status": trade.status,
                "realized_pnl": trade.realized_pnl,
                "fee": trade.fee,
                "slippage": trade.slippage,
                "created_at": trade.created_at,
            }
            for trade in trades
        ],
    }


@router.get("/api/paper-trading/history")
async def get_paper_trade_history(
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)
    auth_result = auth_service.verify_token(token)

    service = PaperTradingService(db)

    trades = service.get_trade_history(
        user_id=auth_result.user_id,
    )

    return {
        "user_id": auth_result.user_id,
        "trades": [
            {
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "stop_loss": trade.stop_loss,
                "take_profit": trade.take_profit,
                "quantity": trade.quantity,
                "status": trade.status,
                "realized_pnl": trade.realized_pnl,
                "fee": trade.fee,
                "slippage": trade.slippage,
                "created_at": trade.created_at,
                "closed_at": trade.closed_at,
            }
            for trade in trades
        ],
    }


@router.post("/api/paper-trading/process-price")
async def process_paper_market_price(
    request: PaperPriceRequest,
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    token = require_auth(authorization)
    auth_result = auth_service.verify_token(token)

    service = PaperTradingService(db)

    result = service.process_market_price(
        user_id=auth_result.user_id,
        symbol=request.symbol.upper(),
        price=request.price,
    )

    return {
        "success": True,
        "user_id": auth_result.user_id,
        "symbol": request.symbol.upper(),
        "price": request.price,
        "result": result,
    }
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