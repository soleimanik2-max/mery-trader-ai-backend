from database import Base, engine
from models import MarketData, Trade


def test_database_models_are_registered():
    assert MarketData.__tablename__ == "market_data"
    assert Trade.__tablename__ == "trades"

    assert MarketData in Base.registry.mappers.keys() or any(
        mapper.class_ is MarketData
        for mapper in Base.registry.mappers
    )

    assert Trade in Base.registry.mappers.keys() or any(
        mapper.class_ is Trade
        for mapper in Base.registry.mappers
    )


def test_database_engine_exists():
    assert engine is not None
