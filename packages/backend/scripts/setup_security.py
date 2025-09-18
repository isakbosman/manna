#!/usr/bin/env python3
"""
Security setup script for Manna Financial Platform.

This script sets up the security infrastructure including:
- Generating encryption keys
- Setting up secrets
- Creating database migrations
- Configuring environment variables
"""

import os
import sys
import secrets
import base64
import logging
from pathlib import Path
from typing import Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SecuritySetup:
    """Handles security infrastructure setup."""

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.backend_root = Path(__file__).parent.parent
        self.env_file = self.project_root / ".env"

    def generate_encryption_key(self) -> str:
        """Generate a secure encryption key."""
        # Generate 256-bit key
        key_bytes = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(key_bytes).decode('utf-8')

    def generate_jwt_key(self) -> str:
        """Generate a JWT signing key."""
        # Generate 256-bit key for HS256
        key_bytes = secrets.token_bytes(32)
        return key_bytes.hex()

    def generate_secret_key(self) -> str:
        """Generate application secret key."""
        return secrets.token_urlsafe(32)

    def generate_database_password(self) -> str:
        """Generate a secure database password."""
        # Generate strong password with mixed case, numbers, and symbols
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(24))

    def create_env_file(self, config: Dict[str, str]) -> None:
        """Create or update .env file with security configuration."""
        logger.info(f"Creating/updating environment file: {self.env_file}")

        # Read existing .env if it exists
        existing_config = {}
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key] = value

        # Merge with new config (don't overwrite existing)
        final_config = existing_config.copy()
        for key, value in config.items():
            if key not in final_config:
                final_config[key] = value
            else:
                logger.info(f"Keeping existing value for {key}")

        # Write the .env file
        with open(self.env_file, 'w') as f:
            f.write("# Manna Financial Platform Environment Configuration\n")
            f.write(f"# Generated on {datetime.now().isoformat()}\n\n")

            # Group related settings
            groups = {
                "Application": ["ENVIRONMENT", "DEBUG", "SECRET_KEY"],
                "Database": ["DATABASE_URL", "DATABASE_PASSWORD", "DATABASE_ECHO"],
                "Security": [
                    "MANNA_ENCRYPTION_KEY", "JWT_SIGNING_KEY", "REQUIRE_HTTPS",
                    "SECURE_COOKIES", "FIELD_ENCRYPTION_ENABLED"
                ],
                "Middleware": [
                    "SECURITY_HEADERS_ENABLED", "RATE_LIMITING_ENABLED",
                    "AUDIT_LOGGING_ENABLED"
                ],
                "Plaid": ["PLAID_CLIENT_ID", "PLAID_SECRET", "PLAID_ENVIRONMENT", "PLAID_WEBHOOK_URL"],
                "Redis": ["REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"]
            }

            for group_name, keys in groups.items():
                f.write(f"# {group_name} Settings\n")
                for key in keys:
                    if key in final_config:
                        f.write(f"{key}={final_config[key]}\n")
                f.write("\n")

            # Write any remaining keys
            written_keys = {key for keys in groups.values() for key in keys}
            remaining_keys = set(final_config.keys()) - written_keys
            if remaining_keys:
                f.write("# Other Settings\n")
                for key in sorted(remaining_keys):
                    f.write(f"{key}={final_config[key]}\n")

        logger.info(f"Environment file created/updated: {self.env_file}")

    def setup_development(self) -> None:
        """Set up security for development environment."""
        logger.info("Setting up security for development environment")

        config = {
            "ENVIRONMENT": "development",
            "DEBUG": "true",
            "SECRET_KEY": self.generate_secret_key(),
            "MANNA_ENCRYPTION_KEY": self.generate_encryption_key(),
            "JWT_SIGNING_KEY": self.generate_jwt_key(),
            "FIELD_ENCRYPTION_ENABLED": "true",
            "SECURITY_HEADERS_ENABLED": "true",
            "RATE_LIMITING_ENABLED": "true",
            "AUDIT_LOGGING_ENABLED": "true",
            "REQUIRE_HTTPS": "false",
            "SECURE_COOKIES": "false",
            "DATABASE_URL": "postgresql://postgres@localhost:5432/manna",
            "REDIS_URL": "redis://localhost:6379/0",
            "CELERY_BROKER_URL": "redis://localhost:6379/1",
            "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        }

        self.create_env_file(config)
        logger.info("Development security setup completed")

    def setup_production(self) -> None:
        """Set up security for production environment."""
        logger.info("Setting up security for production environment")

        # Generate secure passwords and keys
        db_password = self.generate_database_password()

        config = {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "SECRET_KEY": self.generate_secret_key(),
            "MANNA_ENCRYPTION_KEY": self.generate_encryption_key(),
            "JWT_SIGNING_KEY": self.generate_jwt_key(),
            "DATABASE_PASSWORD": db_password,
            "FIELD_ENCRYPTION_ENABLED": "true",
            "SECURITY_HEADERS_ENABLED": "true",
            "RATE_LIMITING_ENABLED": "true",
            "AUDIT_LOGGING_ENABLED": "true",
            "REQUIRE_HTTPS": "true",
            "SECURE_COOKIES": "true",
            # Production database URL template (update host/port as needed)
            "DATABASE_URL": f"postgresql://postgres:{db_password}@localhost:5432/manna?sslmode=require",
            "REDIS_URL": "redis://localhost:6379/0",
            "CELERY_BROKER_URL": "redis://localhost:6379/1",
            "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        }

        self.create_env_file(config)

        # Print important production notes
        print("\n" + "="*60)
        print("PRODUCTION SECURITY SETUP COMPLETED")
        print("="*60)
        print("IMPORTANT: The following secrets have been generated:")
        print(f"  - Database Password: {db_password}")
        print(f"  - Encryption Key: {config['MANNA_ENCRYPTION_KEY'][:20]}...")
        print(f"  - JWT Signing Key: {config['JWT_SIGNING_KEY'][:20]}...")
        print("\nACTION REQUIRED:")
        print("1. Update DATABASE_URL with your actual database host/port")
        print("2. Set PLAID_CLIENT_ID and PLAID_SECRET")
        print("3. Set PLAID_WEBHOOK_URL for your domain")
        print("4. Store these secrets securely (password manager, vault, etc.)")
        print("5. Configure SSL certificates for database connection")
        print("6. Run security validation: python -m src.scripts.validate_security")
        print("="*60)

    def run_migration(self) -> None:
        """Run the encryption migration."""
        logger.info("Running encryption migration...")

        try:
            # Change to backend directory
            os.chdir(self.backend_root)

            # Run Alembic migration
            os.system("alembic upgrade head")
            logger.info("Migration completed successfully")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

    def validate_setup(self) -> bool:
        """Validate the security setup."""
        logger.info("Validating security setup...")

        try:
            # Change to backend directory and run validation
            os.chdir(self.backend_root)
            result = os.system("python -m src.scripts.validate_security")

            if result == 0:
                logger.info("Security validation passed")
                return True
            else:
                logger.warning("Security validation found issues")
                return False

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def setup(self, run_migration: bool = True, validate: bool = True) -> None:
        """Run complete security setup."""
        logger.info(f"Starting security setup for {self.environment} environment")

        try:
            # Setup based on environment
            if self.environment == "production":
                self.setup_production()
            else:
                self.setup_development()

            # Run migration if requested
            if run_migration:
                try:
                    self.run_migration()
                except Exception as e:
                    logger.warning(f"Migration failed: {e}")
                    logger.warning("You may need to run 'alembic upgrade head' manually")

            # Validate setup if requested
            if validate:
                if self.validate_setup():
                    logger.info("✅ Security setup completed successfully")
                else:
                    logger.warning("⚠️ Security setup completed with warnings")

        except Exception as e:
            logger.error(f"Security setup failed: {e}")
            raise


def main():
    """Main setup function."""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Setup security infrastructure for Manna Financial Platform")
    parser.add_argument(
        "--environment",
        choices=["development", "production"],
        default="development",
        help="Environment to setup (default: development)"
    )
    parser.add_argument(
        "--no-migration",
        action="store_true",
        help="Skip running database migration"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip security validation"
    )

    args = parser.parse_args()

    # Create setup instance
    setup = SecuritySetup(args.environment)

    try:
        setup.setup(
            run_migration=not args.no_migration,
            validate=not args.no_validate
        )
        print(f"\n✅ Security setup completed for {args.environment} environment")

    except Exception as e:
        print(f"\n❌ Security setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()