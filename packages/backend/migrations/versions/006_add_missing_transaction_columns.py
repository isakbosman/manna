"""Add missing transaction columns for Plaid compatibility

Revision ID: 006
Revises: 005
Create Date: 2025-09-19 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to transactions table for Plaid compatibility."""

    # Get existing columns
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'transactions'
    """))
    existing_columns = {row[0] for row in result}

    # Add missing columns to transactions table
    if 'iso_currency_code' not in existing_columns:
        op.add_column('transactions', sa.Column('iso_currency_code', sa.String(3), server_default='USD'))
    if 'datetime' not in existing_columns:
        op.add_column('transactions', sa.Column('datetime', sa.DateTime(timezone=True)))
    if 'authorized_date' not in existing_columns:
        op.add_column('transactions', sa.Column('authorized_date', sa.Date()))
    if 'authorized_datetime' not in existing_columns:
        op.add_column('transactions', sa.Column('authorized_datetime', sa.DateTime(timezone=True)))
    if 'original_description' not in existing_columns:
        op.add_column('transactions', sa.Column('original_description', sa.Text()))
    if 'plaid_category' not in existing_columns:
        op.add_column('transactions', sa.Column('plaid_category', postgresql.JSONB()))
    if 'plaid_category_id' not in existing_columns:
        op.add_column('transactions', sa.Column('plaid_category_id', sa.String(50)))
    if 'pending' not in existing_columns:
        op.add_column('transactions', sa.Column('pending', sa.Boolean(), server_default='false'))
    if 'pending_transaction_id' not in existing_columns:
        op.add_column('transactions', sa.Column('pending_transaction_id', sa.String(255)))
    if 'transaction_code' not in existing_columns:
        op.add_column('transactions', sa.Column('transaction_code', sa.String(50)))
    if 'location' not in existing_columns:
        op.add_column('transactions', sa.Column('location', postgresql.JSONB()))
    if 'account_owner' not in existing_columns:
        op.add_column('transactions', sa.Column('account_owner', sa.String(255)))
    if 'logo_url' not in existing_columns:
        op.add_column('transactions', sa.Column('logo_url', sa.Text()))
    if 'website' not in existing_columns:
        op.add_column('transactions', sa.Column('website', sa.String(500)))
    if 'payment_meta' not in existing_columns:
        op.add_column('transactions', sa.Column('payment_meta', postgresql.JSONB()))

    # Check for existing indexes before creating
    result = conn.execute(sa.text("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'transactions'
    """))
    existing_indexes = {row[0] for row in result}

    # Create indexes for new columns if they don't exist
    if 'idx_transactions_pending' not in existing_indexes and 'pending' not in existing_columns:
        op.create_index('idx_transactions_pending', 'transactions', ['pending'])
    if 'idx_transactions_authorized_date' not in existing_indexes and 'authorized_date' not in existing_columns:
        op.create_index('idx_transactions_authorized_date', 'transactions', ['authorized_date'])


def downgrade() -> None:
    """Remove added columns."""

    # Drop indexes first
    op.drop_index('idx_transactions_pending', 'transactions')
    op.drop_index('idx_transactions_authorized_date', 'transactions')

    # Drop columns
    op.drop_column('transactions', 'iso_currency_code')
    op.drop_column('transactions', 'datetime')
    op.drop_column('transactions', 'authorized_date')
    op.drop_column('transactions', 'authorized_datetime')
    op.drop_column('transactions', 'original_description')
    op.drop_column('transactions', 'plaid_category')
    op.drop_column('transactions', 'plaid_category_id')
    op.drop_column('transactions', 'pending')
    op.drop_column('transactions', 'pending_transaction_id')
    op.drop_column('transactions', 'transaction_code')
    op.drop_column('transactions', 'location')
    op.drop_column('transactions', 'account_owner')
    op.drop_column('transactions', 'logo_url')
    op.drop_column('transactions', 'website')
    op.drop_column('transactions', 'payment_meta')