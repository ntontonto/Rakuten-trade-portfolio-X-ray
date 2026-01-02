"""add_price_history_table

Revision ID: 72e26b080b98
Revises: 47b64f9d305c
Create Date: 2025-12-31 00:57:40.231927+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72e26b080b98'
down_revision = '47b64f9d305c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create price_history table
    op.create_table(
        'price_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(length=100), nullable=False),
        sa.Column('ticker', sa.String(length=100), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('nav', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('diff', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('aum_million', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='JPY', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'ticker', 'date', 'source', name='uq_price_history_symbol_ticker_date_source')
    )

    # Create indexes for fast queries
    op.create_index('idx_price_history_symbol_date', 'price_history', ['symbol', 'date'])
    op.create_index('idx_price_history_ticker_date', 'price_history', ['ticker', 'date'])
    op.create_index('idx_price_history_source', 'price_history', ['source'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_price_history_source', table_name='price_history')
    op.drop_index('idx_price_history_ticker_date', table_name='price_history')
    op.drop_index('idx_price_history_symbol_date', table_name='price_history')

    # Drop table
    op.drop_table('price_history')
