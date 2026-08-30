from fastapi import FastAPI

from database import Base, engine
from routers import router as legacy_router
from app.routes import router as app_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="MERY TRADER AI",
    version="1.0.0",
)


app.include_router(legacy_router)
app.include_router(app_router)


@app.get("/")
async def root():
    return {
        "app": "MERY TRADER AI",
        "status": "online",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }
