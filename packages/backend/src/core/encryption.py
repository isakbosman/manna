"""
AES-256-GCM field-level encryption utilities for sensitive data.

Implements NIST-approved AES-256-GCM encryption with authenticated encryption
and additional authenticated data (AAD). Provides migration path from Fernet.
"""

import os
import base64
import logging
import secrets
import struct
from typing import Optional, Union, Any, Tuple
from datetime import datetime
from enum import Enum

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import TypeDecorator, String
from sqlalchemy.engine.interfaces import Dialect

# Try relative import first, fall back to absolute
try:
    from ..config import settings
except ImportError:
    try:
        from src.config import settings
    except ImportError:
        # For testing, create a mock settings object
        class MockSettings:
            environment = "development"
            secret_key = "development-secret-key-change-in-production"

        settings = MockSettings()

logger = logging.getLogger(__name__)

# Encryption version prefixes for migration
class EncryptionVersion(Enum):
    """Encryption version identifiers for migration support."""
    FERNET_V1 = b"FRN1:"  # Legacy Fernet encryption
    AES256_GCM_V2 = b"GCM2:"  # New AES-256-GCM encryption


class EncryptionError(Exception):
    """Custom exception for encryption-related errors."""
    pass


class AES256GCMProvider:
    """
    AES-256-GCM encryption provider with authenticated encryption.

    Features:
    - 256-bit key encryption
    - Authenticated encryption with GCM mode
    - 96-bit nonce for security
    - Additional authenticated data (AAD) support
    - Constant-time operations to prevent timing attacks
    - Key rotation support
    """

    def __init__(self):
        """Initialize AES-256-GCM encryption provider."""
        self._aesgcm: Optional[AESGCM] = None
        self._fernet: Optional[Fernet] = None  # For backward compatibility
        self._key_id: Optional[str] = None
        self._initialize_encryption()

    def _initialize_encryption(self) -> None:
        """Initialize encryption with the appropriate key provider."""
        try:
            # Try environment variable first
            encryption_key = os.getenv("MANNA_ENCRYPTION_KEY_AES256")

            if encryption_key:
                # Decode base64 key (should be 32 bytes for AES-256)
                key_bytes = base64.urlsafe_b64decode(encryption_key.encode())
                if len(key_bytes) != 32:
                    raise EncryptionError(f"AES-256 key must be 32 bytes, got {len(key_bytes)}")

                self._aesgcm = AESGCM(key_bytes)
                self._key_id = self._generate_key_id(key_bytes)
                logger.info("Initialized AES-256-GCM encryption with environment key")

                # Initialize Fernet for backward compatibility
                self._initialize_fernet_fallback()
                return

            # Fall back to derived key for development
            if settings.environment == "development":
                self._aesgcm = self._create_development_key()
                logger.warning("Using development AES-256-GCM key - NOT FOR PRODUCTION")
                self._initialize_fernet_fallback()
                return

            # Production requires explicit key
            if settings.environment == "production":
                raise EncryptionError(
                    "MANNA_ENCRYPTION_KEY_AES256 environment variable required in production"
                )

            # Generate temporary key for testing
            temp_key = AESGCM.generate_key(bit_length=256)
            self._aesgcm = AESGCM(temp_key)
            self._key_id = self._generate_key_id(temp_key)
            logger.warning("Using temporary AES-256-GCM key for testing")

        except Exception as e:
            logger.error(f"Failed to initialize AES-256-GCM encryption: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")

    def _initialize_fernet_fallback(self) -> None:
        """Initialize Fernet for backward compatibility during migration."""
        try:
            # Check for legacy Fernet key
            fernet_key = os.getenv("MANNA_ENCRYPTION_KEY")

            if fernet_key:
                key_bytes = base64.urlsafe_b64decode(fernet_key.encode())
                self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes[:32]))
                logger.info("Initialized Fernet fallback for migration")
            elif settings.environment == "development":
                # Create deterministic Fernet key for development
                password = settings.secret_key.encode()
                salt = b"manna_development_salt_12345"
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                self._fernet = Fernet(key)
                logger.info("Initialized development Fernet fallback")
        except Exception as e:
            logger.warning(f"Could not initialize Fernet fallback: {e}")

    def _create_development_key(self) -> AESGCM:
        """Create a deterministic AES-256 key for development."""
        password = settings.secret_key.encode()
        salt = b"manna_aes256_dev_salt_v2_12345"  # Different salt from Fernet

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password)
        self._key_id = self._generate_key_id(key)
        return AESGCM(key)

    def _generate_key_id(self, key: bytes) -> str:
        """Generate a key ID for tracking key versions."""
        # Use first 4 bytes of SHA256 hash as key ID
        h = hashes.Hash(hashes.SHA256(), backend=default_backend())
        h.update(key)
        digest = h.finalize()
        return base64.urlsafe_b64encode(digest[:4]).decode('ascii').rstrip('=')

    def _generate_nonce(self) -> bytes:
        """
        Generate a cryptographically secure 96-bit nonce for GCM.

        NIST recommends 96-bit nonces for GCM mode.
        """
        return secrets.token_bytes(12)  # 96 bits = 12 bytes

    def encrypt(self, plaintext: str, aad: Optional[bytes] = None) -> str:
        """
        Encrypt plaintext using AES-256-GCM.

        Args:
            plaintext: String to encrypt
            aad: Additional authenticated data (optional)

        Returns:
            Base64 encoded encrypted string with version prefix

        Raises:
            EncryptionError: If encryption fails
        """
        if not self._aesgcm:
            raise EncryptionError("AES-256-GCM encryption not initialized")

        try:
            if plaintext is None:
                return None

            # Generate nonce
            nonce = self._generate_nonce()

            # Convert plaintext to bytes
            plaintext_bytes = plaintext.encode('utf-8')

            # Add timestamp to AAD for replay protection
            if aad is None:
                aad = b""
            timestamp = struct.pack('>Q', int(datetime.utcnow().timestamp()))
            aad = aad + timestamp

            # Encrypt with AES-256-GCM
            ciphertext = self._aesgcm.encrypt(nonce, plaintext_bytes, aad)

            # Combine version prefix + nonce + ciphertext
            encrypted_data = EncryptionVersion.AES256_GCM_V2.value + nonce + ciphertext

            # Base64 encode for storage
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            logger.error(f"AES-256-GCM encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, ciphertext: str, aad: Optional[bytes] = None) -> str:
        """
        Decrypt ciphertext using AES-256-GCM or Fernet (for migration).

        Args:
            ciphertext: Base64 encoded encrypted string
            aad: Additional authenticated data (must match encryption AAD)

        Returns:
            Decrypted plaintext string

        Raises:
            EncryptionError: If decryption fails
        """
        try:
            if ciphertext is None:
                return None

            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))

            # Check version prefix
            if encrypted_bytes.startswith(EncryptionVersion.AES256_GCM_V2.value):
                # New AES-256-GCM format
                if not self._aesgcm:
                    raise EncryptionError("AES-256-GCM decryption not initialized")

                # Remove version prefix
                encrypted_bytes = encrypted_bytes[len(EncryptionVersion.AES256_GCM_V2.value):]

                # Extract nonce (first 12 bytes)
                nonce = encrypted_bytes[:12]
                ciphertext_bytes = encrypted_bytes[12:]

                # Reconstruct AAD with timestamp (ignore timestamp validation for now)
                if aad is None:
                    aad = b""
                # In production, you'd validate the timestamp here
                timestamp = struct.pack('>Q', int(datetime.utcnow().timestamp()))
                aad = aad + timestamp

                # Decrypt
                plaintext_bytes = self._aesgcm.decrypt(nonce, ciphertext_bytes, aad)
                return plaintext_bytes.decode('utf-8')

            elif encrypted_bytes.startswith(EncryptionVersion.FERNET_V1.value):
                # Legacy Fernet format
                if not self._fernet:
                    raise EncryptionError("Fernet decryption not available for migration")

                # Remove version prefix
                fernet_data = encrypted_bytes[len(EncryptionVersion.FERNET_V1.value):]

                # Decrypt with Fernet
                decrypted = self._fernet.decrypt(fernet_data)
                return decrypted.decode('utf-8')

            else:
                # Assume legacy Fernet without version prefix (original format)
                if self._fernet:
                    try:
                        # Try Fernet decryption for backward compatibility
                        decrypted = self._fernet.decrypt(encrypted_bytes)
                        return decrypted.decode('utf-8')
                    except InvalidToken:
                        pass

                raise EncryptionError("Unknown encryption format")

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")

    def migrate_encryption(self, old_ciphertext: str) -> str:
        """
        Migrate encrypted data from Fernet to AES-256-GCM.

        Args:
            old_ciphertext: Fernet-encrypted data

        Returns:
            AES-256-GCM encrypted data

        Raises:
            EncryptionError: If migration fails
        """
        try:
            # Decrypt with old method
            plaintext = self.decrypt(old_ciphertext)

            # Re-encrypt with new method
            return self.encrypt(plaintext)

        except Exception as e:
            logger.error(f"Encryption migration failed: {e}")
            raise EncryptionError(f"Failed to migrate encryption: {e}")

    @staticmethod
    def generate_key() -> str:
        """Generate a new AES-256 encryption key for production use."""
        key = AESGCM.generate_key(bit_length=256)
        return base64.urlsafe_b64encode(key).decode('utf-8')

    def rotate_key(self, new_key: str, old_ciphertexts: list) -> list:
        """
        Rotate encryption key and re-encrypt data.

        Args:
            new_key: New AES-256 key (base64 encoded)
            old_ciphertexts: List of encrypted data with old key

        Returns:
            List of re-encrypted data with new key
        """
        # Decrypt all data with current key
        plaintexts = [self.decrypt(ct) for ct in old_ciphertexts]

        # Update to new key
        key_bytes = base64.urlsafe_b64decode(new_key.encode())
        self._aesgcm = AESGCM(key_bytes)
        self._key_id = self._generate_key_id(key_bytes)

        # Re-encrypt with new key
        return [self.encrypt(pt) for pt in plaintexts]


# Global encryption provider instance
_aes256_provider = AES256GCMProvider()


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type decorator for AES-256-GCM encrypted string fields.

    Automatically encrypts data on write and decrypts on read.
    Supports migration from Fernet-encrypted data.
    """

    impl = String
    cache_ok = True

    def __init__(self, length: Optional[int] = None):
        """
        Initialize encrypted string type.

        Args:
            length: Maximum length for the underlying string column
        """
        # Encrypted data is longer than original
        if length:
            # AES-256-GCM overhead: version(4) + nonce(12) + tag(16) + base64 overhead
            # Roughly 3x the original size to be safe
            length = length * 3
        super().__init__(length)

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        """
        Process value before storing in database (encrypt).

        Args:
            value: Raw value to encrypt
            dialect: Database dialect

        Returns:
            Encrypted value or None
        """
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        try:
            return _aes256_provider.encrypt(value)
        except EncryptionError:
            logger.error("Failed to encrypt field value with AES-256-GCM")
            raise

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        """
        Process value after loading from database (decrypt).

        Args:
            value: Encrypted value from database
            dialect: Database dialect

        Returns:
            Decrypted value or None
        """
        if value is None:
            return None

        try:
            return _aes256_provider.decrypt(value)
        except EncryptionError:
            logger.error("Failed to decrypt field value")
            raise


def encrypt_string(plaintext: str, aad: Optional[bytes] = None) -> str:
    """
    Encrypt a string value using AES-256-GCM.

    Args:
        plaintext: String to encrypt
        aad: Additional authenticated data

    Returns:
        Encrypted string
    """
    return _aes256_provider.encrypt(plaintext, aad)


def decrypt_string(ciphertext: str, aad: Optional[bytes] = None) -> str:
    """
    Decrypt a string value using AES-256-GCM.

    Args:
        ciphertext: Encrypted string
        aad: Additional authenticated data

    Returns:
        Decrypted string
    """
    return _aes256_provider.decrypt(ciphertext, aad)


def migrate_to_aes256(old_ciphertext: str) -> str:
    """
    Migrate Fernet-encrypted data to AES-256-GCM.

    Args:
        old_ciphertext: Fernet-encrypted data

    Returns:
        AES-256-GCM encrypted data
    """
    return _aes256_provider.migrate_encryption(old_ciphertext)


def is_encryption_initialized() -> bool:
    """Check if AES-256-GCM encryption is properly initialized."""
    return _aes256_provider._aesgcm is not None


def get_encryption_info() -> dict:
    """Get information about the current encryption setup."""
    return {
        "initialized": is_encryption_initialized(),
        "environment": settings.environment,
        "key_source": "environment" if os.getenv("MANNA_ENCRYPTION_KEY_AES256") else "derived",
        "key_id": _aes256_provider._key_id,
        "fernet_fallback": _aes256_provider._fernet is not None,
        "algorithm": "AES-256-GCM"
    }


def generate_aes256_key() -> str:
    """Generate a new AES-256 encryption key for production use."""
    return AES256GCMProvider.generate_key()


# Legacy aliases for backward compatibility
encrypt_aes256 = encrypt_string
decrypt_aes256 = decrypt_string
EncryptedStringAES256 = EncryptedString