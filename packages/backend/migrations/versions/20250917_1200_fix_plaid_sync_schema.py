"""Fix Plaid sync schema and add enhanced error tracking

Revision ID: 20250917_1200_fix_plaid_sync_schema
Revises: 20240908_1202_003_reporting_tables
Create Date: 2025-09-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250917_1200_fix_plaid_sync_schema'
down_revision = '20240908_1202_003_reporting_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema to fix Plaid sync issues."""

    # Add new columns to plaid_items table
    op.add_column('plaid_items', sa.Column('last_sync_attempt', sa.DateTime(timezone=True), nullable=True))
    op.add_column('plaid_items', sa.Column('status', sa.String(20), nullable=False, server_default='active'))
    op.add_column('plaid_items', sa.Column('error_code', sa.String(50), nullable=True))
    op.add_column('plaid_items', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('plaid_items', sa.Column('requires_reauth', sa.Boolean(), nullable=False, server_default='false'))

    # Rename last_failed_sync to last_sync_attempt if it exists
    try:
        op.alter_column('plaid_items', 'last_failed_sync', new_column_name='last_sync_attempt_old')
        op.drop_column('plaid_items', 'last_sync_attempt_old')
    except:
        # Column might not exist
        pass

    # Migrate existing error data from 'error' column to new structure
    connection = op.get_bind()

    # Update items with existing errors
    connection.execute(sa.text("""
        UPDATE plaid_items
        SET status = 'error', error_message = error
        WHERE error IS NOT NULL AND error != ''
    """))

    # Drop old error column
    try:
        op.drop_column('plaid_items', 'error')
    except:
        # Column might not exist
        pass

    # Add indexes for performance
    op.create_index('idx_plaid_items_user_active', 'plaid_items', ['user_id', 'is_active'])
    op.create_index('idx_plaid_items_status', 'plaid_items', ['status', 'last_sync_attempt'])
    op.create_index('idx_plaid_items_reauth', 'plaid_items', ['requires_reauth', 'is_active'])

    # Add check constraint for status
    op.create_check_constraint(
        'ck_plaid_item_status',
        'plaid_items',
        "status IN ('active', 'error', 'expired', 'revoked', 'pending')"
    )


def downgrade():
    """Downgrade database schema."""

    # Remove check constraint
    op.drop_constraint('ck_plaid_item_status', 'plaid_items')

    # Remove indexes
    op.drop_index('idx_plaid_items_reauth', 'plaid_items')
    op.drop_index('idx_plaid_items_status', 'plaid_items')
    op.drop_index('idx_plaid_items_user_active', 'plaid_items')

    # Add back old error column
    op.add_column('plaid_items', sa.Column('error', sa.Text(), nullable=True))

    # Migrate error data back
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE plaid_items
        SET error = error_message
        WHERE error_message IS NOT NULL
    """))

    # Remove new columns
    op.drop_column('plaid_items', 'requires_reauth')
    op.drop_column('plaid_items', 'error_message')
    op.drop_column('plaid_items', 'error_code')
    op.drop_column('plaid_items', 'status')
    op.drop_column('plaid_items', 'last_sync_attempt')

    # Add back last_failed_sync
    op.add_column('plaid_items', sa.Column('last_failed_sync', sa.DateTime(timezone=True), nullable=True))