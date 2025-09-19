"""Fix cursor column naming in plaid_items table.

Revision ID: fix_cursor_column_20250118
Revises: 20250918_0600_aes256_upgrade
Create Date: 2025-01-18

This migration ensures the cursor column in plaid_items table is properly named.
It handles both scenarios:
1. If column is named 'sync_cursor', rename it to 'cursor'
2. If column is already 'cursor', do nothing
3. If neither exists, create 'cursor' column
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'fix_cursor_column_20250118'
down_revision = '20250918_0600_aes256_upgrade'
branch_labels = None
depends_on = None


def upgrade():
    """Ensure cursor column exists with correct name."""

    # Get the connection to check existing columns
    conn = op.get_bind()

    # Check what columns exist
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name IN ('cursor', 'sync_cursor')
    """))

    existing_columns = [row[0] for row in result]

    if 'sync_cursor' in existing_columns and 'cursor' not in existing_columns:
        # Rename sync_cursor to cursor
        op.alter_column('plaid_items', 'sync_cursor', new_column_name='cursor')
        print("Renamed column 'sync_cursor' to 'cursor'")

    elif 'cursor' not in existing_columns and 'sync_cursor' not in existing_columns:
        # Neither exists, create cursor column
        op.add_column('plaid_items', sa.Column('cursor', sa.String(255), nullable=True))
        print("Added new column 'cursor'")

    else:
        # cursor already exists, nothing to do
        print("Column 'cursor' already exists")

    # Also ensure error columns exist with correct names
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name IN ('error', 'error_code', 'error_message')
    """))

    existing_error_columns = [row[0] for row in result]

    # If old 'error' column exists but not error_code/error_message, handle migration
    if 'error' in existing_error_columns and 'error_code' not in existing_error_columns:
        # Rename error to error_message
        op.alter_column('plaid_items', 'error', new_column_name='error_message')
        # Add error_code column
        op.add_column('plaid_items', sa.Column('error_code', sa.String(50), nullable=True))
        print("Migrated error columns to error_code and error_message")

    elif 'error_code' not in existing_error_columns:
        # Add missing error columns
        op.add_column('plaid_items', sa.Column('error_code', sa.String(50), nullable=True))
        print("Added error_code column")

    if 'error_message' not in existing_error_columns and 'error' not in existing_error_columns:
        op.add_column('plaid_items', sa.Column('error_message', sa.Text(), nullable=True))
        print("Added error_message column")

    # Ensure other potentially missing columns exist
    missing_columns_check = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'plaid_items'
    """))

    existing = [row[0] for row in missing_columns_check]

    if 'plaid_access_token' not in existing and 'access_token' not in existing:
        op.add_column('plaid_items', sa.Column('access_token', sa.String(255), nullable=True))
        print("Added access_token column")
    elif 'plaid_access_token' in existing and 'access_token' not in existing:
        op.alter_column('plaid_items', 'plaid_access_token', new_column_name='access_token')
        print("Renamed plaid_access_token to access_token")

    if 'last_failed_sync' not in existing and 'last_sync_attempt' not in existing:
        # We use last_sync_attempt in the model
        op.add_column('plaid_items', sa.Column('last_sync_attempt', sa.DateTime(timezone=True), nullable=True))
        print("Added last_sync_attempt column")


def downgrade():
    """Revert cursor column name change."""

    conn = op.get_bind()

    # Check current state
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name IN ('cursor', 'sync_cursor')
    """))

    existing_columns = [row[0] for row in result]

    if 'cursor' in existing_columns and 'sync_cursor' not in existing_columns:
        # Rename back to sync_cursor
        op.alter_column('plaid_items', 'cursor', new_column_name='sync_cursor')

    # Revert error columns
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'plaid_items'
        AND column_name IN ('error_code', 'error_message')
    """))

    existing_error_columns = [row[0] for row in result]

    if 'error_message' in existing_error_columns:
        op.alter_column('plaid_items', 'error_message', new_column_name='error')

    if 'error_code' in existing_error_columns:
        op.drop_column('plaid_items', 'error_code')

    # Revert access_token if needed
    if 'access_token' in existing_columns:
        op.alter_column('plaid_items', 'access_token', new_column_name='plaid_access_token')