from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String

from database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(
        String(50),
        index=True,
        nullable=False,
    )

    timeframe = Column(
        String(20),
        nullable=False,
    )

    price = Column(
        Float,
        nullable=False,
    )

    volume = Column(
        Float,
        nullable=True,
    )

    timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Trade(Base):
    __tablename__ = "trades"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        String(100),
        index=True,
        nullable=False,
    )

    symbol = Column(
        String(50),
        index=True,
        nullable=False,
    )

    side = Column(
        String(10),
        nullable=False,
    )

    entry_price = Column(
        Float,
        nullable=False,
    )

    exit_price = Column(
        Float,
        nullable=True,
    )

    stop_loss = Column(
        Float,
        nullable=True,
    )

    take_profit = Column(
        Float,
        nullable=True,
    )

    quantity = Column(
        Float,
        nullable=False,
    )

    status = Column(
        String(20),
        default="OPEN",
        nullable=False,
    )

    realized_pnl = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    fee = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    slippage = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    closed_at = Column(
        DateTime,
        nullable=True,
    )


class PaperAccount(Base):
    __tablename__ = "paper_accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        String(100),
        index=True,
        nullable=False,
    )

    starting_capital = Column(
        Float,
        nullable=False,
    )

    cash = Column(
        Float,
        nullable=False,
    )

    realized_pnl = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    total_fees = Column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )