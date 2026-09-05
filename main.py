from fastapi import FastAPI

from database import Base, engine
import models
from routers import router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="MERY TRADER AI",
    version="1.0.0",
)

app.include_router(router)


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