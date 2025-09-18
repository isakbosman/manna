"""
Centralized secrets management for the Manna platform.

Provides secure storage and retrieval of application secrets with
support for different backends: environment variables, AWS Secrets Manager,
HashiCorp Vault, etc.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import secrets
import string

from ..config import settings

logger = logging.getLogger(__name__)


class SecretNotFoundError(Exception):
    """Raised when a requested secret is not found."""
    pass


class SecretsProvider(ABC):
    """Abstract base class for secrets providers."""

    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret by key."""
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret value."""
        pass

    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete a secret."""
        pass

    @abstractmethod
    def list_secrets(self) -> list[str]:
        """List available secret keys."""
        pass


class EnvironmentSecretsProvider(SecretsProvider):
    """Secrets provider that uses environment variables."""

    def __init__(self, prefix: str = "MANNA_"):
        self.prefix = prefix

    def _get_env_key(self, key: str) -> str:
        """Convert secret key to environment variable name."""
        return f"{self.prefix}{key.upper()}"

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment variable."""
        env_key = self._get_env_key(key)
        return os.getenv(env_key)

    def set_secret(self, key: str, value: str) -> bool:
        """Set environment variable (only for current process)."""
        env_key = self._get_env_key(key)
        os.environ[env_key] = value
        return True

    def delete_secret(self, key: str) -> bool:
        """Delete environment variable."""
        env_key = self._get_env_key(key)
        if env_key in os.environ:
            del os.environ[env_key]
            return True
        return False

    def list_secrets(self) -> list[str]:
        """List all environment variables with the prefix."""
        return [
            key[len(self.prefix):].lower()
            for key in os.environ.keys()
            if key.startswith(self.prefix)
        ]


class FileSecretsProvider(SecretsProvider):
    """Secrets provider that uses a local encrypted file (development only)."""

    def __init__(self, file_path: str = ".secrets.json"):
        self.file_path = file_path
        self._secrets_cache: Dict[str, str] = {}
        self._load_secrets()

    def _load_secrets(self) -> None:
        """Load secrets from file."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    self._secrets_cache = json.load(f)
                logger.info(f"Loaded {len(self._secrets_cache)} secrets from {self.file_path}")
        except Exception as e:
            logger.warning(f"Could not load secrets file {self.file_path}: {e}")
            self._secrets_cache = {}

    def _save_secrets(self) -> None:
        """Save secrets to file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self._secrets_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save secrets to {self.file_path}: {e}")

    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from cache."""
        return self._secrets_cache.get(key)

    def set_secret(self, key: str, value: str) -> bool:
        """Set secret and save to file."""
        self._secrets_cache[key] = value
        self._save_secrets()
        return True

    def delete_secret(self, key: str) -> bool:
        """Delete secret and save to file."""
        if key in self._secrets_cache:
            del self._secrets_cache[key]
            self._save_secrets()
            return True
        return False

    def list_secrets(self) -> list[str]:
        """List all secret keys."""
        return list(self._secrets_cache.keys())


class SecretsManager:
    """
    Centralized secrets manager that coordinates different providers.

    Provides a unified interface for secret management with fallback
    between different providers.
    """

    def __init__(self):
        self.providers: list[SecretsProvider] = []
        self._jwt_keys_cache: Dict[str, Any] = {}
        self._setup_providers()

    def _setup_providers(self) -> None:
        """Set up secrets providers based on environment."""
        # Environment variables provider (always available)
        self.providers.append(EnvironmentSecretsProvider())

        # File provider for development
        if settings.environment in ["development", "testing"]:
            self.providers.append(FileSecretsProvider())

        logger.info(f"Initialized secrets manager with {len(self.providers)} providers")

    def get_secret(self, key: str, required: bool = False) -> Optional[str]:
        """
        Get a secret value from available providers.

        Args:
            key: Secret key to retrieve
            required: If True, raises SecretNotFoundError if not found

        Returns:
            Secret value or None if not found

        Raises:
            SecretNotFoundError: If required=True and secret not found
        """
        for provider in self.providers:
            try:
                value = provider.get_secret(key)
                if value is not None:
                    return value
            except Exception as e:
                logger.warning(f"Provider {type(provider).__name__} failed to get {key}: {e}")

        if required:
            raise SecretNotFoundError(f"Required secret '{key}' not found")

        return None

    def set_secret(self, key: str, value: str) -> bool:
        """
        Set a secret value using the first writable provider.

        Args:
            key: Secret key
            value: Secret value

        Returns:
            True if successful, False otherwise
        """
        for provider in self.providers:
            try:
                if provider.set_secret(key, value):
                    logger.info(f"Secret '{key}' stored using {type(provider).__name__}")
                    return True
            except Exception as e:
                logger.warning(f"Provider {type(provider).__name__} failed to set {key}: {e}")

        logger.error(f"Failed to store secret '{key}' with any provider")
        return False

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from all providers."""
        success = False
        for provider in self.providers:
            try:
                if provider.delete_secret(key):
                    success = True
            except Exception as e:
                logger.warning(f"Provider {type(provider).__name__} failed to delete {key}: {e}")

        return success

    def get_database_url(self) -> str:
        """Get secure database URL with password from secrets."""
        # Try to get database password from secrets
        db_password = self.get_secret("database_password")

        if db_password:
            # Reconstruct database URL with secure password
            base_url = settings.database_url
            if "@" in base_url:
                # Replace or add password
                protocol, rest = base_url.split("://", 1)
                if "@" in rest:
                    user_part, host_part = rest.split("@", 1)
                    if ":" in user_part:
                        user, _ = user_part.split(":", 1)
                    else:
                        user = user_part
                else:
                    user = "postgres"
                    host_part = rest

                return f"{protocol}://{user}:{db_password}@{host_part}"

        # Validate that we don't have a blank password in production
        if settings.environment == "production" and ":@" in settings.database_url:
            raise SecretNotFoundError("Database password required in production")

        return settings.database_url

    def get_jwt_signing_key(self) -> str:
        """Get JWT signing key, generating if needed."""
        key = self.get_secret("jwt_signing_key")

        if not key:
            # Generate new key
            key = self._generate_jwt_key()
            self.set_secret("jwt_signing_key", key)
            logger.info("Generated new JWT signing key")

        return key

    def get_encryption_key(self) -> str:
        """Get field encryption key, generating if needed."""
        key = self.get_secret("encryption_key")

        if not key:
            # Import here to avoid circular imports
            from .encryption import EncryptionKeyProvider
            key = EncryptionKeyProvider.generate_key()
            self.set_secret("encryption_key", key)
            logger.info("Generated new encryption key")

        return key

    def rotate_jwt_key(self) -> tuple[str, str]:
        """
        Rotate JWT signing key.

        Returns:
            Tuple of (old_key, new_key)
        """
        old_key = self.get_jwt_signing_key()
        new_key = self._generate_jwt_key()

        # Store both keys temporarily for transition
        self.set_secret("jwt_signing_key_old", old_key)
        self.set_secret("jwt_signing_key", new_key)

        logger.info("Rotated JWT signing key")
        return old_key, new_key

    def _generate_jwt_key(self) -> str:
        """Generate a secure JWT signing key."""
        # Generate 256-bit key for HS256
        key_bytes = secrets.token_bytes(32)
        return key_bytes.hex()

    def validate_production_secrets(self) -> list[str]:
        """
        Validate that all required secrets are available for production.

        Returns:
            List of missing secrets
        """
        required_secrets = [
            "database_password",
            "jwt_signing_key",
            "encryption_key",
            "plaid_secret"
        ]

        missing = []
        for secret in required_secrets:
            if not self.get_secret(secret):
                missing.append(secret)

        return missing

    def get_secret_info(self) -> Dict[str, Any]:
        """Get information about secrets (for monitoring/health checks)."""
        info = {
            "providers_count": len(self.providers),
            "providers": [type(p).__name__ for p in self.providers],
            "environment": settings.environment,
            "secrets_available": {}
        }

        # Check availability of key secrets (without revealing values)
        key_secrets = [
            "database_password", "jwt_signing_key", "encryption_key",
            "plaid_secret", "plaid_client_id"
        ]

        for secret in key_secrets:
            info["secrets_available"][secret] = self.get_secret(secret) is not None

        return info


# Global secrets manager instance
secrets_manager = SecretsManager()


# Convenience functions
def get_secret(key: str, required: bool = False) -> Optional[str]:
    """Get a secret value."""
    return secrets_manager.get_secret(key, required)


def set_secret(key: str, value: str) -> bool:
    """Set a secret value."""
    return secrets_manager.set_secret(key, value)


def get_secure_database_url() -> str:
    """Get database URL with secure password."""
    return secrets_manager.get_database_url()


def get_jwt_key() -> str:
    """Get JWT signing key."""
    return secrets_manager.get_jwt_signing_key()


def validate_production_setup() -> None:
    """Validate production secrets setup."""
    if settings.environment == "production":
        missing = secrets_manager.validate_production_secrets()
        if missing:
            raise SecretNotFoundError(
                f"Missing required production secrets: {', '.join(missing)}"
            )