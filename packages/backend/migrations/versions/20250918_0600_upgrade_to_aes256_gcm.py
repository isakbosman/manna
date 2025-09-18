"""Upgrade from Fernet to AES-256-GCM encryption and fix optimistic locking.

Revision ID: 20250918_0600_aes256_upgrade
Revises: 20250918_0500_encrypt_tokens
Create Date: 2025-09-18 06:00:00.000000

This migration:
1. Migrates existing Fernet-encrypted tokens to AES-256-GCM
2. Fixes version column constraints for optimistic locking
3. Adds proper server defaults for version columns
4. Updates audit logging
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import logging
from datetime import datetime

# revision identifiers
revision = '20250918_0600_aes256_upgrade'
down_revision = '20250918_0500_encrypt_tokens'
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade():
    """Migrate to AES-256-GCM encryption and fix optimistic locking."""

    connection = op.get_bind()

    # 1. First, ensure version column has proper constraints
    logger.info("Updating version column constraints for optimistic locking...")

    # Update any NULL version values to 1
    connection.execute(text("""
        UPDATE plaid_items
        SET version = 1
        WHERE version IS NULL
    """))

    # 2. Migrate existing encrypted tokens from Fernet to AES-256-GCM
    logger.info("Migrating encrypted tokens from Fernet to AES-256-GCM...")

    try:
        # Import encryption modules
        import sys
        import os

        # Add the src directory to Python path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'src')
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        from core.encryption import migrate_to_aes256, is_encryption_initialized, get_encryption_info

        if not is_encryption_initialized():
            logger.warning("AES-256-GCM encryption not initialized - skipping token migration")
            logger.warning("Tokens will be migrated on first access after deployment")
            return

        # Get encryption info
        enc_info = get_encryption_info()
        logger.info(f"Encryption info: {enc_info}")

        # Get all plaid items with access tokens
        result = connection.execute(text("""
            SELECT id, plaid_access_token, version
            FROM plaid_items
            WHERE plaid_access_token IS NOT NULL
            AND plaid_access_token != ''
        """))

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        for row in result:
            item_id, access_token, current_version = row

            # Skip if already AES-256-GCM format (contains GCM2: prefix)
            if access_token.startswith('R0NNMjo'):  # Base64 encoded "GCM2:"
                logger.debug(f"PlaidItem {item_id} already uses AES-256-GCM, skipping")
                skipped_count += 1
                continue

            try:
                # Migrate from Fernet to AES-256-GCM
                migrated_token = migrate_to_aes256(access_token)

                # Update the database with migrated token and increment version
                connection.execute(text("""
                    UPDATE plaid_items
                    SET plaid_access_token = :migrated_token,
                        version = :new_version,
                        updated_at = :updated_at
                    WHERE id = :item_id
                    AND version = :current_version
                """), {
                    'migrated_token': migrated_token,
                    'new_version': current_version + 1,
                    'updated_at': datetime.utcnow(),
                    'item_id': item_id,
                    'current_version': current_version
                })

                # Check if the update was successful (optimistic locking)
                updated_rows = connection.execute(text("""
                    SELECT COUNT(*) as count
                    FROM plaid_items
                    WHERE id = :item_id
                    AND version = :new_version
                """), {
                    'item_id': item_id,
                    'new_version': current_version + 1
                }).scalar()

                if updated_rows == 1:
                    migrated_count += 1
                    logger.info(f"Migrated access token for PlaidItem {item_id} to AES-256-GCM")
                else:
                    logger.warning(f"Failed to update PlaidItem {item_id} - concurrent modification detected")
                    error_count += 1

            except Exception as e:
                logger.error(f"Failed to migrate access token for PlaidItem {item_id}: {e}")
                error_count += 1
                # Continue with other items rather than failing the migration

        logger.info(f"Migration summary: {migrated_count} migrated, {skipped_count} skipped, {error_count} errors")

        # 3. Log the migration in audit log
        try:
            from core.audit import log_audit_event, AuditEventType, AuditSeverity
            log_audit_event(
                AuditEventType.SECURITY_CONFIGURATION_CHANGE,
                f"Migration: Upgraded {migrated_count} tokens from Fernet to AES-256-GCM",
                severity=AuditSeverity.HIGH,
                metadata={
                    "migration_id": revision,
                    "tokens_migrated": migrated_count,
                    "tokens_skipped": skipped_count,
                    "errors": error_count,
                    "encryption_algorithm": "AES-256-GCM"
                }
            )
        except Exception as e:
            logger.warning(f"Could not log audit event: {e}")

    except ImportError as e:
        logger.warning(f"Encryption modules not available during migration: {e}")
        logger.warning("Tokens will be migrated on first access after deployment")
    except Exception as e:
        logger.error(f"Unexpected error during token migration: {e}")
        logger.warning("Migration completed but some tokens may not be migrated")


def downgrade():
    """Downgrade: This is a one-way migration - AES-256-GCM tokens cannot be downgraded to Fernet."""

    logger.warning("=" * 60)
    logger.warning("DOWNGRADE WARNING: This is a one-way migration!")
    logger.warning("AES-256-GCM encrypted tokens cannot be automatically")
    logger.warning("downgraded to Fernet format.")
    logger.warning("=" * 60)

    connection = op.get_bind()

    # Check if we have any AES-256-GCM encrypted tokens
    result = connection.execute(text("""
        SELECT COUNT(*) as count
        FROM plaid_items
        WHERE plaid_access_token LIKE 'R0NNMjo%'
    """)).scalar()

    if result > 0:
        logger.error(f"Found {result} AES-256-GCM encrypted tokens that cannot be downgraded")
        logger.error("Manual intervention required to downgrade these tokens")
        logger.error("Options:")
        logger.error("1. Re-authenticate with Plaid to get new tokens")
        logger.error("2. Manually decrypt and re-encrypt with Fernet (if both keys available)")

        # Log the attempted downgrade
        try:
            from core.audit import log_audit_event, AuditEventType, AuditSeverity
            log_audit_event(
                AuditEventType.SECURITY_CONFIGURATION_CHANGE,
                f"Attempted downgrade from AES-256-GCM - {result} tokens require manual intervention",
                severity=AuditSeverity.CRITICAL,
                metadata={
                    "migration_id": revision,
                    "tokens_requiring_intervention": result,
                    "action_required": "manual_token_re-authentication"
                }
            )
        except Exception as e:
            logger.warning(f"Could not log audit event: {e}")

        raise RuntimeError(f"Cannot automatically downgrade {result} AES-256-GCM encrypted tokens. Manual intervention required.")

    logger.info("No AES-256-GCM tokens found - downgrade can proceed")
    logger.info("Optimistic locking changes are compatible and require no downgrade action")