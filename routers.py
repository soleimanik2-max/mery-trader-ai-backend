from fastapi import APIRouter

from app.routes import router as api_router


router = APIRouter()

router.include_router(api_router)


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
