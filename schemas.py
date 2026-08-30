from typing import Optional

from pydantic import BaseModel, Field


class MarketDataCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    timeframe: str = Field(..., min_length=1, max_length=20)
    price: float = Field(..., gt=0)
    volume: Optional[float] = Field(default=None, ge=0)


class MarketDataResponse(MarketDataCreate):
    id: int


class TradeCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    side: str = Field(..., pattern="^(BUY|SELL)$")
    entry_price: float = Field(..., gt=0)
    stop_loss: Optional[float] = Field(default=None, gt=0)
    take_profit: Optional[float] = Field(default=None, gt=0)
    quantity: float = Field(..., gt=0)


class TradeResponse(TradeCreate):
    id: int
    status: str
