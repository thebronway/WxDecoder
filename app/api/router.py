from fastapi import APIRouter
from app.api.endpoints import analysis, admin

router = APIRouter()

# Mount the endpoints
# /api/analyze
router.include_router(analysis.router, prefix="/api", tags=["analysis"])

# /api/admin/*
router.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# /api/logs, /api/stats (Legacy paths used by frontend)
router.include_router(admin.router, prefix="/api", tags=["stats"])