"""Add iso_currency_code to accounts table

Revision ID: 007
Revises: 006
Create Date: 2025-09-19 20:42:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add iso_currency_code column to accounts table."""

    # Get existing columns
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'accounts'
    """))
    existing_columns = {row[0] for row in result}

    # Add iso_currency_code column if it doesn't exist
    if 'iso_currency_code' not in existing_columns:
        op.add_column('accounts', sa.Column('iso_currency_code', sa.String(3), server_default='USD'))


def downgrade() -> None:
    """Remove iso_currency_code column."""
    op.drop_column('accounts', 'iso_currency_code')