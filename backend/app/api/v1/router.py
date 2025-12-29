"""Main API Router - combines all v1 endpoints"""
from fastapi import APIRouter

from app.api.v1 import upload, portfolio, analysis, ai_insights

api_router = APIRouter()

# Include all routers
api_router.include_router(upload.router)
api_router.include_router(portfolio.router)
api_router.include_router(analysis.router)
api_router.include_router(ai_insights.router)

# Future routers will be added here:
# api_router.include_router(ml_predictions.router)
# api_router.include_router(export.router)
