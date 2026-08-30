from database import Base, engine
from models import MarketData, Trade


def test_database_models_are_registered():
    assert MarketData.__tablename__ == "market_data"
    assert Trade.__tablename__ == "trades"

    registered_models = {
        mapper.class_
        for mapper in Base.registry.mappers
    }

    assert MarketData in registered_models
    assert Trade in registered_models


def test_database_engine_exists():
    assert engine is not None
