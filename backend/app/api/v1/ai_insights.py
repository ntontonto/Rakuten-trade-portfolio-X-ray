"""AI Insights Endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db_session, get_portfolio
from app.db.models import Portfolio, Holding
from app.services.ai_insights import AIInsightsGenerator
from app.services.portfolio_aggregator import PortfolioAggregator
from collections import defaultdict

router = APIRouter(prefix="/ai", tags=["ai-insights"])


class AIReportResponse(BaseModel):
    """Response schema for AI report"""
    status: str
    report: str
    generated_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "report": "# ポートフォリオ診断レポート\n\n## 1. 健全性診断...",
                "generated_at": "2025-12-27T10:00:00Z"
            }
        }


@router.post("/insights", response_model=AIReportResponse)
def generate_portfolio_insights(
    portfolio_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Generate AI-powered portfolio insights

    Uses Google Gemini to analyze portfolio and provide recommendations

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/ai/insights" \\
             -H "Content-Type: application/json" \\
             -d '{"portfolio_id": "123e4567-e89b-12d3-a456-426614174000"}'
        ```
    """
    # Get portfolio summary
    aggregator = PortfolioAggregator(db)
    summary = aggregator.get_portfolio_summary(portfolio_id)

    # Get holdings for additional analysis
    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio_id)
        .all()
    )

    # Calculate core ratio
    total_value = summary['total_current_value']
    core_value = sum(
        float(h.current_value or 0)
        for h in holdings
        if h.strategy == 'Core'
    )
    core_ratio = (core_value / total_value * 100) if total_value > 0 else 0

    # Get top asset class
    class_allocation = defaultdict(float)
    for h in holdings:
        class_allocation[h.asset_class or 'Other'] += float(h.current_value or 0)

    top_asset_class = max(class_allocation.items(), key=lambda x: x[1])[0] if class_allocation else "未分類"

    # Generate insights
    ai_generator = AIInsightsGenerator()
    result = ai_generator.generate_portfolio_report(
        total_value=total_value,
        total_xirr=summary['total_xirr'],
        core_ratio=core_ratio,
        top_asset_class=top_asset_class,
        holdings_count=summary['holdings_count']
    )

    from datetime import datetime
    return AIReportResponse(
        status=result['status'],
        report=result['report'],
        generated_at=datetime.now().isoformat()
    )


@router.get("/portfolios/{portfolio_id}/ai/latest-insight")
def get_latest_insight(
    portfolio: Portfolio = Depends(get_portfolio),
    db: Session = Depends(get_db_session)
):
    """
    Get cached AI insight (placeholder for future caching)

    For now, redirects to generate new insight
    """
    return {
        "message": "Use POST /api/v1/ai/insights to generate new insights",
        "portfolio_id": str(portfolio.id)
    }
