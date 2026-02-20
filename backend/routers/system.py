"""System health and status routes."""

from fastapi import APIRouter
from backend.core.config import settings
from backend.db.schemas import SystemStatusResponse, HealthResponse

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    return SystemStatusResponse(
        status="maintenance" if settings.MAINTENANCE_MODE else "running",
        version=settings.APP_VERSION,
        maintenance=settings.MAINTENANCE_MODE,
        maintenance_message=settings.MAINTENANCE_MESSAGE if settings.MAINTENANCE_MODE else None,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", database="connected")
