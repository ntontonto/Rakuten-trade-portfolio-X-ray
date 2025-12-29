"""CSV Upload Endpoint"""
from decimal import Decimal
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID, uuid4

from app.api.deps import get_db_session
from app.services.csv_parser import CSVParser
from app.services.portfolio_aggregator import PortfolioAggregator
from app.services.balance_merger import BalanceMerger
from app.services.asset_classifier import classify_asset
from app.db.models import Portfolio, Transaction
from app.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/csv")
async def upload_csv_files(
    files: List[UploadFile] = File(...),
    portfolio_id: UUID = None,
    db: Session = Depends(get_db_session)
):
    """
    Upload and process CSV files from Rakuten Securities

    Accepts:
    - Transaction history files (US stocks, JP stocks, Investment trusts)
    - Asset balance files

    Args:
        files: List of CSV files (multipart/form-data)
        portfolio_id: Optional portfolio ID (creates new if not provided)
        db: Database session

    Returns:
        Processing summary with created portfolio ID

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/upload/csv" \\
             -H "accept: application/json" \\
             -F "files=@transaction_history.csv" \\
             -F "files=@asset_balance.csv"
        ```
    """
    # Validate file count
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )

    # Validate file sizes and extensions
    for file in files:
        # Check file extension
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.filename}. Only CSV files are allowed."
            )

        # Check file size (read to check, then reset)
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large: {file.filename}. Max size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )
        await file.seek(0)  # Reset file pointer

    # Get or create portfolio
    if portfolio_id:
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
    else:
        # Create new portfolio
        portfolio = Portfolio(name="Main Portfolio")
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        portfolio_id = portfolio.id

    # Initialize services
    parser = CSVParser()
    aggregator = PortfolioAggregator(db)
    merger = BalanceMerger(db)

    # Process files
    parsed_files = []
    all_transactions = []
    balance_data = []
    exchange_rates = {}

    for file in files:
        try:
            content = await file.read()
            parsed = parser.parse_file(content, file.filename)
            parsed_files.append({
                'filename': file.filename,
                'type': parsed['type']
            })

            if parsed['type'] == 'transactions':
                # Store transactions
                for tx_data in parsed['data']:
                    # Normalize date for DB and JSON storage
                    tx_date = tx_data['date']
                    if hasattr(tx_date, "date"):
                        tx_date = tx_date.date()

                    # Ensure raw_data is JSON-serializable
                    def _serialize(value):
                        if isinstance(value, Decimal):
                            return float(value)
                        if hasattr(value, "isoformat"):
                            return value.isoformat()
                        return value

                    raw_data = {k: _serialize(v) for k, v in tx_data.items()}

                    # Classify asset if not already classified
                    if not tx_data.get('asset_class'):
                        tx_data['asset_class'] = classify_asset(
                            tx_data['name'],
                            tx_data.get('symbol')
                        )

                    transaction = Transaction(
                        portfolio_id=portfolio_id,
                        transaction_date=tx_date,
                        symbol=tx_data['symbol'],
                        name=tx_data['name'],
                        side=tx_data['side'],
                        transaction_type=tx_data.get('type'),
                        quantity=tx_data['qty'],
                        amount_jpy=tx_data['amount_jpy'],
                        market=tx_data['market'],
                        asset_class=tx_data['asset_class'],
                        raw_data=raw_data
                    )
                    db.add(transaction)
                    all_transactions.append(tx_data)

            elif parsed['type'] == 'balance':
                # Store balance data for later merging
                balance_data.extend(parsed['data'])
                if 'exchange_rates' in parsed:
                    exchange_rates.update(parsed['exchange_rates'])

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing {file.filename}: {str(e)}"
            )

    # Commit transactions
    db.commit()

    # Aggregate transactions into holdings
    holdings = aggregator.process_portfolio(portfolio_id)

    # Merge balance data if available
    merge_stats = None
    if balance_data:
        merge_stats = merger.merge_balance_data(
            portfolio_id,
            balance_data,
            exchange_rates
        )

        # Recalculate metrics after price updates
        aggregator._calculate_performance_metrics(holdings)

    # Get portfolio summary
    summary = aggregator.get_portfolio_summary(portfolio_id)

    return {
        "success": True,
        "message": f"Processed {len(files)} file(s) successfully",
        "portfolio_id": str(portfolio_id),
        "files_processed": parsed_files,
        "transactions_imported": len(all_transactions),
        "holdings_created": len(holdings),
        "balance_merge": merge_stats,
        "summary": summary
    }
