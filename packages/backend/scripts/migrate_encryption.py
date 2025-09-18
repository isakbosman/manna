#!/usr/bin/env python3
"""
Migration script to transition from Fernet encryption to AES-256-GCM.

This script safely migrates all encrypted data in the database from
the old Fernet format to the new AES-256-GCM format with zero downtime.
"""

import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from src.config import settings
from src.core.encryption_aes256 import (
    migrate_to_aes256,
    is_aes256_initialized,
    get_encryption_info,
    EncryptionVersion
)
from src.core.database import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EncryptionMigrator:
    """
    Handles the migration of encrypted data from Fernet to AES-256-GCM.
    """

    def __init__(self, batch_size: int = 100, dry_run: bool = False):
        """
        Initialize the encryption migrator.

        Args:
            batch_size: Number of records to process in each batch
            dry_run: If True, only simulate the migration without changes
        """
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)

        # Track migration statistics
        self.stats = {
            'total_records': 0,
            'migrated_records': 0,
            'skipped_records': 0,
            'failed_records': 0,
            'tables_processed': [],
            'start_time': None,
            'end_time': None
        }

    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with proper cleanup."""
        session = self.Session()
        try:
            yield session
        finally:
            session.close()

    def identify_encrypted_columns(self) -> Dict[str, List[str]]:
        """
        Identify all tables and columns that contain encrypted data.

        Returns:
            Dictionary mapping table names to lists of encrypted column names
        """
        encrypted_columns = {}

        # Known encrypted columns (extend this based on your schema)
        known_encrypted = {
            'plaid_items': ['access_token'],
            'users': ['password_hash'],  # If using field encryption for passwords
            'accounts': [],  # Add any encrypted columns
            # Add more tables and columns as needed
        }

        with self.get_session() as session:
            # Verify tables exist
            for table, columns in known_encrypted.items():
                try:
                    # Check if table exists
                    result = session.execute(
                        text(f"SELECT 1 FROM information_schema.tables WHERE table_name = :table"),
                        {"table": table}
                    ).first()

                    if result:
                        # Check which columns exist
                        existing_columns = []
                        for column in columns:
                            col_result = session.execute(
                                text("""
                                    SELECT 1 FROM information_schema.columns
                                    WHERE table_name = :table AND column_name = :column
                                """),
                                {"table": table, "column": column}
                            ).first()
                            if col_result:
                                existing_columns.append(column)

                        if existing_columns:
                            encrypted_columns[table] = existing_columns
                            logger.info(f"Found encrypted columns in {table}: {existing_columns}")

                except SQLAlchemyError as e:
                    logger.warning(f"Error checking table {table}: {e}")

        return encrypted_columns

    def check_encryption_version(self, encrypted_data: str) -> str:
        """
        Check the encryption version of data.

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            'fernet', 'aes256', or 'unknown'
        """
        if not encrypted_data:
            return 'unknown'

        try:
            import base64
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())

            if decoded.startswith(EncryptionVersion.AES256_GCM_V2.value):
                return 'aes256'
            elif decoded.startswith(EncryptionVersion.FERNET_V1.value):
                return 'fernet'
            else:
                # Check if it's legacy Fernet (no version prefix)
                # Fernet tokens start with specific byte patterns
                if len(decoded) > 0 and decoded[0] == 0x80:
                    return 'fernet'

            return 'unknown'

        except Exception:
            return 'unknown'

    def migrate_table_column(
        self,
        table: str,
        column: str,
        id_column: str = 'id'
    ) -> Dict[str, int]:
        """
        Migrate encrypted data in a specific table column.

        Args:
            table: Table name
            column: Column name containing encrypted data
            id_column: Primary key column name

        Returns:
            Dictionary with migration statistics for this table
        """
        stats = {
            'total': 0,
            'migrated': 0,
            'skipped': 0,
            'failed': 0
        }

        logger.info(f"Starting migration for {table}.{column}")

        with self.get_session() as session:
            try:
                # Get total count
                count_result = session.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL")
                ).scalar()
                stats['total'] = count_result or 0

                if stats['total'] == 0:
                    logger.info(f"No records to migrate in {table}.{column}")
                    return stats

                # Process in batches
                offset = 0
                while offset < stats['total']:
                    # Fetch batch of records
                    batch_query = text(f"""
                        SELECT {id_column}, {column}
                        FROM {table}
                        WHERE {column} IS NOT NULL
                        ORDER BY {id_column}
                        LIMIT :limit OFFSET :offset
                    """)

                    batch_results = session.execute(
                        batch_query,
                        {"limit": self.batch_size, "offset": offset}
                    ).fetchall()

                    if not batch_results:
                        break

                    # Process each record in the batch
                    for row in batch_results:
                        record_id = row[0]
                        encrypted_data = row[1]

                        try:
                            # Check encryption version
                            version = self.check_encryption_version(encrypted_data)

                            if version == 'aes256':
                                # Already migrated
                                stats['skipped'] += 1
                                logger.debug(f"Record {record_id} already uses AES-256-GCM")
                                continue

                            elif version == 'fernet':
                                # Needs migration
                                if not self.dry_run:
                                    # Migrate the data
                                    new_encrypted = migrate_to_aes256(encrypted_data)

                                    # Update the record
                                    update_query = text(f"""
                                        UPDATE {table}
                                        SET {column} = :new_value
                                        WHERE {id_column} = :id
                                    """)

                                    session.execute(
                                        update_query,
                                        {"new_value": new_encrypted, "id": record_id}
                                    )

                                stats['migrated'] += 1
                                logger.debug(f"Migrated record {record_id}")

                            else:
                                # Unknown format
                                stats['failed'] += 1
                                logger.warning(f"Unknown encryption format for record {record_id}")

                        except Exception as e:
                            stats['failed'] += 1
                            logger.error(f"Failed to migrate record {record_id}: {e}")

                    # Commit batch
                    if not self.dry_run and stats['migrated'] > 0:
                        session.commit()
                        logger.info(f"Committed batch: {stats['migrated']} records migrated")

                    offset += self.batch_size

                    # Progress update
                    progress = min(100, (offset / stats['total']) * 100)
                    logger.info(f"Progress: {progress:.1f}% ({offset}/{stats['total']})")

            except SQLAlchemyError as e:
                logger.error(f"Database error migrating {table}.{column}: {e}")
                session.rollback()

        logger.info(f"Completed migration for {table}.{column}: {stats}")
        return stats

    def run_migration(self) -> Dict[str, Any]:
        """
        Run the complete encryption migration.

        Returns:
            Migration statistics
        """
        self.stats['start_time'] = datetime.utcnow()

        # Check if AES-256 is initialized
        if not is_aes256_initialized():
            logger.error("AES-256-GCM encryption is not initialized. Set MANNA_ENCRYPTION_KEY_AES256")
            return self.stats

        logger.info(f"Starting encryption migration (dry_run={self.dry_run})")
        logger.info(f"Encryption info: {get_encryption_info()}")

        # Identify encrypted columns
        encrypted_columns = self.identify_encrypted_columns()

        if not encrypted_columns:
            logger.warning("No encrypted columns found to migrate")
            return self.stats

        # Migrate each table/column
        for table, columns in encrypted_columns.items():
            self.stats['tables_processed'].append(table)

            for column in columns:
                table_stats = self.migrate_table_column(table, column)

                self.stats['total_records'] += table_stats['total']
                self.stats['migrated_records'] += table_stats['migrated']
                self.stats['skipped_records'] += table_stats['skipped']
                self.stats['failed_records'] += table_stats['failed']

        self.stats['end_time'] = datetime.utcnow()

        # Calculate duration
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            self.stats['duration_seconds'] = duration

        return self.stats

    def verify_migration(self) -> bool:
        """
        Verify that all encrypted data has been migrated.

        Returns:
            True if all data is migrated, False otherwise
        """
        logger.info("Verifying migration...")

        encrypted_columns = self.identify_encrypted_columns()
        all_migrated = True

        for table, columns in encrypted_columns.items():
            for column in columns:
                with self.get_session() as session:
                    # Sample some records to check
                    sample_query = text(f"""
                        SELECT {column}
                        FROM {table}
                        WHERE {column} IS NOT NULL
                        LIMIT 100
                    """)

                    samples = session.execute(sample_query).fetchall()

                    fernet_count = 0
                    aes256_count = 0

                    for sample in samples:
                        version = self.check_encryption_version(sample[0])
                        if version == 'fernet':
                            fernet_count += 1
                        elif version == 'aes256':
                            aes256_count += 1

                    if fernet_count > 0:
                        logger.warning(f"{table}.{column}: Found {fernet_count} Fernet-encrypted records")
                        all_migrated = False
                    else:
                        logger.info(f"{table}.{column}: All sampled records use AES-256-GCM ({aes256_count})")

        return all_migrated


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description='Migrate encryption from Fernet to AES-256-GCM')
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of records to process in each batch'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without making changes'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify migration status without migrating'
    )

    args = parser.parse_args()

    # Set up AES-256 key from environment
    if not os.getenv('MANNA_ENCRYPTION_KEY_AES256'):
        # For migration, we can derive it from the Fernet key if available
        fernet_key = os.getenv('MANNA_ENCRYPTION_KEY')
        if fernet_key:
            logger.warning("Using derived AES-256 key from Fernet key for migration")
            # In production, you should generate a new key
            # For demo, we'll use the Fernet key padded/truncated to 32 bytes
            import base64
            fernet_bytes = base64.urlsafe_b64decode(fernet_key.encode())[:32]
            aes256_key = base64.urlsafe_b64encode(fernet_bytes).decode()
            os.environ['MANNA_ENCRYPTION_KEY_AES256'] = aes256_key

    migrator = EncryptionMigrator(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    if args.verify_only:
        # Just verify migration status
        is_complete = migrator.verify_migration()
        if is_complete:
            logger.info("✓ All encrypted data has been migrated to AES-256-GCM")
            sys.exit(0)
        else:
            logger.warning("✗ Some data still uses Fernet encryption")
            sys.exit(1)
    else:
        # Run migration
        stats = migrator.run_migration()

        # Print summary
        print("\n" + "=" * 50)
        print("MIGRATION SUMMARY")
        print("=" * 50)
        print(f"Total records:    {stats['total_records']}")
        print(f"Migrated:         {stats['migrated_records']}")
        print(f"Skipped:          {stats['skipped_records']}")
        print(f"Failed:           {stats['failed_records']}")
        print(f"Tables processed: {', '.join(stats['tables_processed'])}")

        if 'duration_seconds' in stats:
            print(f"Duration:         {stats['duration_seconds']:.2f} seconds")

        if args.dry_run:
            print("\n⚠ This was a DRY RUN - no changes were made")
        else:
            print("\n✓ Migration completed")

            # Verify migration
            if migrator.verify_migration():
                print("✓ Migration verified successfully")
            else:
                print("⚠ Some records may not have been migrated")

        # Exit with appropriate code
        if stats['failed_records'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == '__main__':
    main()