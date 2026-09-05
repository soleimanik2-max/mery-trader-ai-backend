from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from database import Base, engine
import models
from routers import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MERY TRADER AI",
    version="1.0.0",
)

app.include_router(router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="MERY TRADER AI",
        version="1.0.0",
        description="MERY TRADER AI Secure Backend",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation["security"] = [
                    {
                        "BearerAuth": []
                    }
                ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


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