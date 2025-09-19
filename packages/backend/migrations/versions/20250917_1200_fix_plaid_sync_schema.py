"""Fix Plaid sync schema and add enhanced error tracking

Revision ID: 20250917_1200_fix_plaid_sync_schema
Revises: 20240908_1202_003_reporting_tables
Create Date: 2025-09-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_plaid_sync_20250917'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema to fix Plaid sync issues."""

    # Note: The following columns already exist in migration 001:
    # - last_sync_attempt
    # - status
    # - error_code
    # - error_message
    # - requires_reauth
    # So we skip adding them here

    # Migrate existing error data from 'error' column to new structure (if it exists)
    connection = op.get_bind()

    # Check if 'error' column exists and migrate data
    result = connection.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='plaid_items' AND column_name='error'
    """))

    if result.fetchone():
        # Update items with existing errors
        connection.execute(sa.text("""
            UPDATE plaid_items
            SET status = 'error', error_message = error
            WHERE error IS NOT NULL AND error != ''
        """))

        # Drop old error column
        op.drop_column('plaid_items', 'error')

    # Note: Indexes already exist in migration 001:
    # - idx_plaid_items_user_active -> idx_plaid_items_user
    # - idx_plaid_items_status
    # - idx_plaid_items_reauth

    # Note: Check constraint ck_plaid_item_status already exists in migration 001


def downgrade():
    """Downgrade database schema."""

    # Add back old error column if we had removed it
    connection = op.get_bind()

    # Check if we need to add the error column back
    result = connection.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='plaid_items' AND column_name='error'
    """))

    if not result.fetchone():
        # Add back old error column
        op.add_column('plaid_items', sa.Column('error', sa.Text(), nullable=True))

        # Migrate error data back
        connection.execute(sa.text("""
            UPDATE plaid_items
            SET error = error_message
            WHERE error_message IS NOT NULL
        """))