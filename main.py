from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from database import Base, engine
import models
from routers import router

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------

Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MERY TRADER AI",
    version="1.0.0",
    description="MERY TRADER AI Secure Backend",
)

app.include_router(router)


# ---------------------------------------------------------------------------
# OPENAPI / SWAGGER AUTHENTICATION
# ---------------------------------------------------------------------------

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="MERY TRADER AI",
        version="1.0.0",
        description="MERY TRADER AI Secure Backend",
        routes=app.routes,
    )

    openapi_schema.setdefault("components", {})

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Token",
        }
    }

    # Public endpoints that do NOT require authentication.
    public_paths = {
        "/",
        "/health",
        "/api/status",
        "/api/version",
        "/api/auth",
    }

    # Require Bearer authentication for protected endpoints.
    for path, methods in openapi_schema["paths"].items():
        if path in public_paths:
            continue

        for operation in methods.values():
            if isinstance(operation, dict):
                operation["security"] = [
                    {
                        "BearerAuth": []
                    }
                ]

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi


# ---------------------------------------------------------------------------
# ROOT
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "app": "MERY TRADER AI",
        "status": "online",
    }


# ---------------------------------------------------------------------------
# HEALTH
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }