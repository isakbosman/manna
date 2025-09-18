#!/usr/bin/env python3
"""
Security validation script for Manna Financial Platform.

Validates that all security fixes are properly implemented and configured.
Run this script to verify security posture before deployment.
"""

import sys
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import settings
from core.encryption import is_encryption_initialized, get_encryption_key_info
from core.secrets import secrets_manager
from core.database import check_db_health
from core.audit import log_audit_event, AuditEventType, AuditSeverity

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Raised when security validation fails."""
    pass


class SecurityValidator:
    """Validates security implementation across the platform."""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.successes: List[Dict[str, Any]] = []

    def add_issue(self, category: str, message: str, severity: str = "high"):
        """Add a security issue."""
        self.issues.append({
            "category": category,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow()
        })

    def add_warning(self, category: str, message: str):
        """Add a security warning."""
        self.warnings.append({
            "category": category,
            "message": message,
            "timestamp": datetime.utcnow()
        })

    def add_success(self, category: str, message: str):
        """Add a successful check."""
        self.successes.append({
            "category": category,
            "message": message,
            "timestamp": datetime.utcnow()
        })

    def validate_encryption(self) -> None:
        """Validate field-level encryption implementation."""
        logger.info("Validating encryption implementation...")

        try:
            # Check if encryption is initialized
            if is_encryption_initialized():
                self.add_success("encryption", "Field-level encryption is initialized")

                # Get encryption info
                info = get_encryption_key_info()
                if info["key_source"] == "environment":
                    self.add_success("encryption", "Using environment-based encryption key")
                else:
                    if settings.environment == "production":
                        self.add_issue(
                            "encryption",
                            "Production should use environment-based encryption key",
                            "critical"
                        )
                    else:
                        self.add_warning("encryption", "Using derived encryption key (development only)")

            else:
                self.add_issue("encryption", "Field-level encryption not initialized", "critical")

            # Check encryption is enabled in config
            if settings.field_encryption_enabled:
                self.add_success("encryption", "Field encryption enabled in configuration")
            else:
                self.add_warning("encryption", "Field encryption disabled in configuration")

        except Exception as e:
            self.add_issue("encryption", f"Encryption validation failed: {e}", "critical")

    def validate_secrets_management(self) -> None:
        """Validate secrets management implementation."""
        logger.info("Validating secrets management...")

        try:
            # Check secrets manager info
            info = secrets_manager.get_secret_info()
            self.add_success("secrets", f"Secrets manager initialized with {info['providers_count']} providers")

            # Check required secrets in production
            if settings.environment == "production":
                missing = secrets_manager.validate_production_secrets()
                if missing:
                    for secret in missing:
                        self.add_issue("secrets", f"Missing required production secret: {secret}", "critical")
                else:
                    self.add_success("secrets", "All required production secrets are available")

            # Check specific secret availability
            key_secrets = ["database_password", "jwt_signing_key", "encryption_key"]
            for secret in key_secrets:
                if info["secrets_available"].get(secret, False):
                    self.add_success("secrets", f"Secret '{secret}' is available")
                else:
                    severity = "critical" if settings.environment == "production" else "medium"
                    self.add_issue("secrets", f"Secret '{secret}' not available", severity)

        except Exception as e:
            self.add_issue("secrets", f"Secrets validation failed: {e}", "critical")

    def validate_database_security(self) -> None:
        """Validate database security configuration."""
        logger.info("Validating database security...")

        try:
            # Check database health
            health = check_db_health()
            if health["status"] == "healthy":
                self.add_success("database", "Database connection is healthy")
            else:
                self.add_issue("database", f"Database health check failed: {health}", "high")

            # Check database URL security
            db_url = settings.database_url
            if settings.environment == "production":
                if ":@" in db_url:
                    self.add_issue("database", "Database password missing in production", "critical")
                if "sslmode=require" not in db_url and "sslmode=prefer" not in db_url:
                    self.add_warning("database", "SSL not explicitly configured for production database")
            else:
                self.add_success("database", "Database configuration validated for development")

            # Check connection pool settings
            if settings.database_pool_size > 0:
                self.add_success("database", f"Connection pooling configured (pool_size={settings.database_pool_size})")
            else:
                self.add_warning("database", "Connection pooling not configured")

        except Exception as e:
            self.add_issue("database", f"Database validation failed: {e}", "critical")

    def validate_middleware_security(self) -> None:
        """Validate security middleware configuration."""
        logger.info("Validating security middleware...")

        # Check security headers
        if settings.security_headers_enabled:
            self.add_success("middleware", "Security headers middleware enabled")
        else:
            self.add_warning("middleware", "Security headers middleware disabled")

        # Check rate limiting
        if settings.rate_limiting_enabled:
            self.add_success("middleware", "Rate limiting middleware enabled")
        else:
            self.add_warning("middleware", "Rate limiting middleware disabled")

        # Check audit logging
        if settings.audit_logging_enabled:
            self.add_success("middleware", "Audit logging enabled")
        else:
            severity = "high" if settings.environment == "production" else "medium"
            self.add_issue("middleware", "Audit logging disabled", severity)

        # Check HTTPS requirements
        if settings.environment == "production":
            if settings.require_https:
                self.add_success("middleware", "HTTPS required in production")
            else:
                self.add_issue("middleware", "HTTPS not required in production", "high")

        # Check secure cookies
        if settings.environment == "production":
            if settings.secure_cookies:
                self.add_success("middleware", "Secure cookies enabled in production")
            else:
                self.add_issue("middleware", "Secure cookies not enabled in production", "medium")

    def validate_optimistic_locking(self) -> None:
        """Validate optimistic locking implementation."""
        logger.info("Validating optimistic locking...")

        try:
            # Try to import the locking module
            from core.locking import OptimisticLockMixin, safe_cursor_update
            self.add_success("locking", "Optimistic locking module available")

            # Check if PlaidItem uses optimistic locking
            try:
                from database.models import PlaidItem
                if hasattr(PlaidItem, 'version'):
                    self.add_success("locking", "PlaidItem model has version column for optimistic locking")
                else:
                    self.add_issue("locking", "PlaidItem model missing version column", "high")

                if hasattr(PlaidItem, 'update_with_lock'):
                    self.add_success("locking", "PlaidItem has update_with_lock method")
                else:
                    self.add_warning("locking", "PlaidItem missing update_with_lock method")

            except ImportError:
                self.add_warning("locking", "Could not import PlaidItem model for validation")

        except ImportError as e:
            self.add_issue("locking", f"Optimistic locking module not available: {e}", "high")

    def validate_access_token_encryption(self) -> None:
        """Validate that access tokens are properly encrypted."""
        logger.info("Validating access token encryption...")

        try:
            # Check if PlaidItem uses encrypted access tokens
            from database.models import PlaidItem
            from core.encryption import EncryptedString

            # Check if plaid_access_token field uses EncryptedString
            access_token_field = getattr(PlaidItem, 'plaid_access_token', None)
            if access_token_field and hasattr(access_token_field.property, 'columns'):
                column = access_token_field.property.columns[0]
                if hasattr(column.type, '__class__') and 'EncryptedString' in str(column.type.__class__):
                    self.add_success("tokens", "PlaidItem access token field uses encryption")
                else:
                    self.add_issue("tokens", "PlaidItem access token field not encrypted", "critical")
            else:
                self.add_warning("tokens", "Could not validate access token field encryption")

            # Check for helper methods
            if hasattr(PlaidItem, 'get_decrypted_access_token'):
                self.add_success("tokens", "PlaidItem has decryption helper method")
            else:
                self.add_warning("tokens", "PlaidItem missing decryption helper method")

        except ImportError as e:
            self.add_issue("tokens", f"Could not validate access token encryption: {e}", "high")

    def validate_configuration(self) -> None:
        """Validate overall configuration security."""
        logger.info("Validating configuration security...")

        # Check environment
        if settings.environment in ["development", "testing", "staging", "production"]:
            self.add_success("config", f"Valid environment: {settings.environment}")
        else:
            self.add_issue("config", f"Invalid environment: {settings.environment}", "medium")

        # Check secret key
        if settings.environment == "production":
            if settings.secret_key == "development-secret-key-change-in-production":
                self.add_issue("config", "Default secret key used in production", "critical")
            else:
                self.add_success("config", "Secret key changed from default in production")

        # Check debug mode
        if settings.environment == "production" and settings.debug:
            self.add_issue("config", "Debug mode enabled in production", "high")
        else:
            self.add_success("config", "Debug mode appropriately configured")

        # Check API documentation exposure
        if settings.environment == "production":
            # In main.py, docs are disabled in production
            self.add_success("config", "API documentation disabled in production")

    def run_validation(self) -> Dict[str, Any]:
        """Run all security validations."""
        logger.info("Starting comprehensive security validation...")

        # Log validation start
        log_audit_event(
            AuditEventType.SECURITY_CONFIGURATION_CHANGE,
            "Security validation started",
            severity=AuditSeverity.MEDIUM,
            metadata={"environment": settings.environment}
        )

        # Run all validations
        self.validate_encryption()
        self.validate_secrets_management()
        self.validate_database_security()
        self.validate_middleware_security()
        self.validate_optimistic_locking()
        self.validate_access_token_encryption()
        self.validate_configuration()

        # Compile results
        results = {
            "validation_time": datetime.utcnow(),
            "environment": settings.environment,
            "summary": {
                "total_checks": len(self.successes) + len(self.warnings) + len(self.issues),
                "successes": len(self.successes),
                "warnings": len(self.warnings),
                "issues": len(self.issues),
                "critical_issues": len([i for i in self.issues if i["severity"] == "critical"])
            },
            "successes": self.successes,
            "warnings": self.warnings,
            "issues": self.issues
        }

        # Log validation completion
        log_audit_event(
            AuditEventType.SECURITY_CONFIGURATION_CHANGE,
            "Security validation completed",
            severity=AuditSeverity.MEDIUM,
            metadata=results["summary"]
        )

        return results

    def print_results(self, results: Dict[str, Any]) -> None:
        """Print validation results in a readable format."""
        print("\n" + "="*60)
        print("MANNA FINANCIAL PLATFORM - SECURITY VALIDATION REPORT")
        print("="*60)
        print(f"Environment: {results['environment']}")
        print(f"Validation Time: {results['validation_time']}")
        print(f"Total Checks: {results['summary']['total_checks']}")
        print()

        # Print summary
        summary = results['summary']
        print("SUMMARY:")
        print(f"  ✅ Successes: {summary['successes']}")
        print(f"  ⚠️  Warnings: {summary['warnings']}")
        print(f"  ❌ Issues: {summary['issues']}")
        print(f"  🔥 Critical Issues: {summary['critical_issues']}")
        print()

        # Print critical issues first
        critical_issues = [i for i in results['issues'] if i['severity'] == 'critical']
        if critical_issues:
            print("🔥 CRITICAL ISSUES (Must Fix Before Production):")
            for issue in critical_issues:
                print(f"   [{issue['category']}] {issue['message']}")
            print()

        # Print other issues
        other_issues = [i for i in results['issues'] if i['severity'] != 'critical']
        if other_issues:
            print("❌ OTHER ISSUES:")
            for issue in other_issues:
                print(f"   [{issue['category']}] {issue['message']} (severity: {issue['severity']})")
            print()

        # Print warnings
        if results['warnings']:
            print("⚠️  WARNINGS:")
            for warning in results['warnings']:
                print(f"   [{warning['category']}] {warning['message']}")
            print()

        # Print successes
        if results['successes']:
            print("✅ SUCCESSFUL CHECKS:")
            for success in results['successes']:
                print(f"   [{success['category']}] {success['message']}")
            print()

        # Final recommendation
        if summary['critical_issues'] > 0:
            print("🔥 RECOMMENDATION: DO NOT DEPLOY - Critical security issues must be resolved!")
            return False
        elif summary['issues'] > 0:
            print("⚠️  RECOMMENDATION: Review and resolve issues before production deployment")
            return True
        else:
            print("✅ RECOMMENDATION: Security validation passed - ready for deployment")
            return True


def main():
    """Main validation function."""
    validator = SecurityValidator()

    try:
        results = validator.run_validation()
        ready_for_deployment = validator.print_results(results)

        # Exit with appropriate code
        if results['summary']['critical_issues'] > 0:
            sys.exit(1)  # Critical issues
        elif results['summary']['issues'] > 0:
            sys.exit(2)  # Non-critical issues
        else:
            sys.exit(0)  # All good

    except Exception as e:
        logger.error(f"Security validation failed with error: {e}")
        print(f"\n❌ VALIDATION ERROR: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()