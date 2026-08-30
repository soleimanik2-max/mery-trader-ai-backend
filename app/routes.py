from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.ai_decision import ai_decision_service
from app.services.audit_service import audit_service
from app.services.market_data import market_data_service
from app.services.risk_management import risk_management_service
from app.services.technical_analysis import technical_analysis_service


router = APIRouter()


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


@router.post("/api/market-data")
async def update_market_data(request: MarketDataRequest):
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
async def analyze_market(request: AnalysisRequest):
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
async def calculate_risk(request: RiskRequest):
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
