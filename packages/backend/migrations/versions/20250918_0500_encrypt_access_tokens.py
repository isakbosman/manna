"""Encrypt existing Plaid access tokens and add optimistic locking.

Revision ID: 20250918_0500_encrypt_tokens
Revises: 20250918_0430_seed_initial_data
Create Date: 2025-09-18 05:00:00.000000

This migration:
1. Adds version column for optimistic locking to plaid_items table
2. Encrypts existing plaintext access tokens
3. Adds audit logging for the migration
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import logging

# revision identifiers
revision = '20250918_0500_encrypt_tokens'
down_revision = '20250918_0430_seed_initial_data'
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade():
    """Encrypt existing access tokens and add version column."""

    # 1. Add version column for optimistic locking
    op.add_column('plaid_items', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    # 2. Add index on version column for performance
    op.create_index('idx_plaid_items_version', 'plaid_items', ['version'])

    # 3. Encrypt existing access tokens
    connection = op.get_bind()

    # Check if we have encryption available
    try:
        # Try to import encryption - if not available, skip encryption
        import sys
        import os

        # Add the src directory to Python path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'src')
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        from core.encryption import encrypt_string, is_encryption_initialized

        if not is_encryption_initialized():
            logger.warning("Encryption not initialized - skipping token encryption")
            return

        # Get all plaid items with access tokens
        result = connection.execute(text("""
            SELECT id, plaid_access_token
            FROM plaid_items
            WHERE plaid_access_token IS NOT NULL
            AND plaid_access_token != ''
        """))

        encrypted_count = 0

        for row in result:
            item_id, access_token = row

            # Skip if already encrypted (contains encryption indicators)
            if access_token.startswith('gAAAAA') or len(access_token) > 100:
                logger.info(f"PlaidItem {item_id} already appears to be encrypted, skipping")
                continue

            try:
                # Encrypt the access token
                encrypted_token = encrypt_string(access_token)

                # Update the database
                connection.execute(text("""
                    UPDATE plaid_items
                    SET plaid_access_token = :encrypted_token,
                        version = version + 1
                    WHERE id = :item_id
                """), {
                    'encrypted_token': encrypted_token,
                    'item_id': item_id
                })

                encrypted_count += 1
                logger.info(f"Encrypted access token for PlaidItem {item_id}")

            except Exception as e:
                logger.error(f"Failed to encrypt access token for PlaidItem {item_id}: {e}")
                # Continue with other items rather than failing the migration

        logger.info(f"Successfully encrypted {encrypted_count} access tokens")

        # Log the migration in audit log
        try:
            from core.audit import log_audit_event, AuditEventType, AuditSeverity
            log_audit_event(
                AuditEventType.SECURITY_CONFIGURATION_CHANGE,
                f"Migration: Encrypted {encrypted_count} Plaid access tokens",
                severity=AuditSeverity.HIGH,
                metadata={
                    "migration_id": revision,
                    "tokens_encrypted": encrypted_count
                }
            )
        except Exception as e:
            logger.warning(f"Could not log audit event: {e}")

    except ImportError as e:
        logger.warning(f"Encryption modules not available during migration: {e}")
        logger.warning("Tokens will be encrypted on first access after deployment")
    except Exception as e:
        logger.error(f"Unexpected error during token encryption: {e}")
        # Don't fail the migration for encryption issues
        logger.warning("Migration completed but some tokens may not be encrypted")


def downgrade():
    """Downgrade: Remove version column and decrypt tokens if possible."""

    connection = op.get_bind()

    # Try to decrypt tokens back to plaintext
    try:
        import sys
        import os

        # Add the src directory to Python path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'src')
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        from core.encryption import decrypt_string, is_encryption_initialized

        if is_encryption_initialized():
            # Get all plaid items with encrypted access tokens
            result = connection.execute(text("""
                SELECT id, plaid_access_token
                FROM plaid_items
                WHERE plaid_access_token IS NOT NULL
                AND plaid_access_token != ''
            """))

            decrypted_count = 0

            for row in result:
                item_id, access_token = row

                # Only decrypt if it looks encrypted
                if access_token.startswith('gAAAAA') or len(access_token) > 100:
                    try:
                        # Decrypt the access token
                        decrypted_token = decrypt_string(access_token)

                        # Update the database
                        connection.execute(text("""
                            UPDATE plaid_items
                            SET plaid_access_token = :decrypted_token
                            WHERE id = :item_id
                        """), {
                            'decrypted_token': decrypted_token,
                            'item_id': item_id
                        })

                        decrypted_count += 1
                        logger.info(f"Decrypted access token for PlaidItem {item_id}")

                    except Exception as e:
                        logger.error(f"Failed to decrypt access token for PlaidItem {item_id}: {e}")
                        # Continue with other items

            logger.info(f"Successfully decrypted {decrypted_count} access tokens")
        else:
            logger.warning("Encryption not available - cannot decrypt tokens during downgrade")

    except ImportError:
        logger.warning("Encryption modules not available - cannot decrypt tokens")
    except Exception as e:
        logger.error(f"Error during token decryption: {e}")

    # Remove version column and index
    op.drop_index('idx_plaid_items_version', table_name='plaid_items')
    op.drop_column('plaid_items', 'version')

    logger.info("Removed optimistic locking version column")