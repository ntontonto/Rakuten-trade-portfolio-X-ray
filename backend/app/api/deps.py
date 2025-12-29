"""API Dependencies"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.base import get_db
from app.db.models import Portfolio


def get_db_session() -> Generator:
    """
    Database session dependency

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db_session)):
            ...
    """
    try:
        db = next(get_db())
        yield db
    finally:
        db.close()


def get_portfolio(
    portfolio_id: UUID,
    db: Session = Depends(get_db_session)
) -> Portfolio:
    """
    Get portfolio by ID or raise 404

    Args:
        portfolio_id: Portfolio UUID
        db: Database session

    Returns:
        Portfolio object

    Raises:
        HTTPException: 404 if portfolio not found
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    return portfolio
