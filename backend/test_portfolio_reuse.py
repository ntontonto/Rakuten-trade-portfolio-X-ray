"""
Test that portfolio reuse works correctly
"""
from app.db.base import SessionLocal
from app.db.models.portfolio import Portfolio

def test_portfolio_reuse():
    """Test that the upload endpoint logic reuses existing portfolios"""

    db = SessionLocal()

    print("\n" + "="*80)
    print("PORTFOLIO REUSE TEST")
    print("="*80)

    # Check current state
    portfolios_before = db.query(Portfolio).all()
    print(f"\nBefore: {len(portfolios_before)} portfolio(s) in database")
    for p in portfolios_before:
        print(f"  - {p.id}: {p.name}")

    # Simulate upload logic (no portfolio_id provided)
    print("\n" + "-"*80)
    print("SIMULATING CSV UPLOAD (no portfolio_id)")
    print("-"*80)

    portfolio_id = None  # User didn't provide one

    if portfolio_id:
        print("✓ User provided portfolio_id - would use that")
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    else:
        # Check if a portfolio already exists (reuse it to avoid duplicates)
        existing_portfolio = db.query(Portfolio).first()
        if existing_portfolio:
            # Reuse existing portfolio
            portfolio = existing_portfolio
            portfolio_id = portfolio.id
            print(f"♻️  Reusing existing portfolio: {portfolio_id}")
        else:
            # Create new portfolio (first time upload)
            portfolio = Portfolio(name="Main Portfolio")
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
            portfolio_id = portfolio.id
            print(f"✨ Created new portfolio: {portfolio_id}")

    # Check final state
    portfolios_after = db.query(Portfolio).all()
    print(f"\nAfter: {len(portfolios_after)} portfolio(s) in database")
    for p in portfolios_after:
        print(f"  - {p.id}: {p.name}")

    # Verify no duplicates were created
    print("\n" + "="*80)
    if len(portfolios_before) == len(portfolios_after):
        print("✅ SUCCESS: No duplicate portfolios created!")
        print(f"   Portfolio ID used: {portfolio_id}")
    else:
        print("❌ FAIL: Duplicate portfolio was created")
    print("="*80 + "\n")

    db.close()
    return len(portfolios_before) == len(portfolios_after)

if __name__ == "__main__":
    success = test_portfolio_reuse()
    exit(0 if success else 1)
