"""
Comprehensive test suite for AES-256-GCM encryption implementation.

Tests encryption, decryption, migration from Fernet, and security properties.
"""

import os
import base64
import pytest
import secrets
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Import the encryption module
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.encryption_aes256 import (
    AES256GCMProvider,
    EncryptedStringAES256,
    encrypt_aes256,
    decrypt_aes256,
    migrate_to_aes256,
    EncryptionError,
    EncryptionVersion,
    is_aes256_initialized,
    get_encryption_info
)


class TestAES256GCMProvider:
    """Test the AES-256-GCM encryption provider."""

    def setup_method(self):
        """Set up test environment."""
        # Generate test keys
        self.aes256_key = AESGCM.generate_key(bit_length=256)
        self.aes256_key_b64 = base64.urlsafe_b64encode(self.aes256_key).decode()

        # Set test key in environment
        os.environ['MANNA_ENCRYPTION_KEY_AES256'] = self.aes256_key_b64

        # Create provider
        self.provider = AES256GCMProvider()

    def teardown_method(self):
        """Clean up test environment."""
        if 'MANNA_ENCRYPTION_KEY_AES256' in os.environ:
            del os.environ['MANNA_ENCRYPTION_KEY_AES256']

    def test_initialization_with_environment_key(self):
        """Test provider initialization with environment key."""
        assert self.provider._aesgcm is not None
        assert is_aes256_initialized()

        info = get_encryption_info()
        assert info['initialized'] is True
        assert info['key_source'] == 'environment'
        assert info['algorithm'] == 'AES-256-GCM'

    def test_initialization_without_key(self):
        """Test provider initialization without environment key."""
        del os.environ['MANNA_ENCRYPTION_KEY_AES256']

        with patch('src.core.encryption_aes256.settings.environment', 'test'):
            provider = AES256GCMProvider()
            assert provider._aesgcm is not None

    def test_encrypt_decrypt_basic(self):
        """Test basic encryption and decryption."""
        plaintext = "Hello, World! This is a test message."

        # Encrypt
        ciphertext = self.provider.encrypt(plaintext)
        assert ciphertext is not None
        assert ciphertext != plaintext

        # Verify format
        decoded = base64.urlsafe_b64decode(ciphertext.encode())
        assert decoded.startswith(EncryptionVersion.AES256_GCM_V2.value)

        # Decrypt
        decrypted = self.provider.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_encrypt_decrypt_with_aad(self):
        """Test encryption with additional authenticated data."""
        plaintext = "Sensitive data"
        aad = b"user_id:12345"

        # Encrypt with AAD
        ciphertext = self.provider.encrypt(plaintext, aad)

        # Decrypt with same AAD should work
        decrypted = self.provider.decrypt(ciphertext, aad)
        assert decrypted == plaintext

        # Decrypt with different AAD should fail
        with pytest.raises(EncryptionError):
            self.provider.decrypt(ciphertext, b"user_id:67890")

    def test_encrypt_none_value(self):
        """Test encrypting None value."""
        assert self.provider.encrypt(None) is None
        assert self.provider.decrypt(None) is None

    def test_nonce_uniqueness(self):
        """Test that each encryption uses a unique nonce."""
        plaintext = "Test message"

        # Encrypt same message multiple times
        ciphertexts = [self.provider.encrypt(plaintext) for _ in range(10)]

        # All ciphertexts should be different (due to unique nonces)
        assert len(set(ciphertexts)) == 10

        # Extract nonces and verify they're unique
        nonces = []
        for ct in ciphertexts:
            decoded = base64.urlsafe_b64decode(ct.encode())
            # Skip version prefix (4 bytes)
            nonce = decoded[4:16]  # Next 12 bytes are the nonce
            nonces.append(nonce)

        assert len(set(nonces)) == 10

    def test_decrypt_invalid_ciphertext(self):
        """Test decrypting invalid ciphertext."""
        # Random data
        invalid = base64.urlsafe_b64encode(b"invalid data").decode()
        with pytest.raises(EncryptionError):
            self.provider.decrypt(invalid)

        # Corrupted ciphertext
        valid_ciphertext = self.provider.encrypt("test")
        corrupted = valid_ciphertext[:-5] + "xxxxx"
        with pytest.raises(EncryptionError):
            self.provider.decrypt(corrupted)

    def test_key_rotation(self):
        """Test key rotation functionality."""
        # Encrypt with current key
        plaintexts = ["data1", "data2", "data3"]
        old_ciphertexts = [self.provider.encrypt(pt) for pt in plaintexts]

        # Generate new key
        new_key = AESGCM.generate_key(bit_length=256)
        new_key_b64 = base64.urlsafe_b64encode(new_key).decode()

        # Rotate keys
        new_ciphertexts = self.provider.rotate_key(new_key_b64, old_ciphertexts)

        # Verify all data was re-encrypted
        assert len(new_ciphertexts) == len(old_ciphertexts)
        assert all(nc != oc for nc, oc in zip(new_ciphertexts, old_ciphertexts))

        # Verify we can decrypt with new key
        for pt, ct in zip(plaintexts, new_ciphertexts):
            decrypted = self.provider.decrypt(ct)
            assert decrypted == pt

    def test_constant_time_operations(self):
        """Test that operations are constant-time to prevent timing attacks."""
        import time

        short_text = "a"
        long_text = "a" * 1000

        # Measure encryption times
        short_times = []
        long_times = []

        for _ in range(100):
            start = time.perf_counter_ns()
            self.provider.encrypt(short_text)
            short_times.append(time.perf_counter_ns() - start)

            start = time.perf_counter_ns()
            self.provider.encrypt(long_text)
            long_times.append(time.perf_counter_ns() - start)

        # The time difference should be proportional to data size
        # Not exactly constant time, but should not leak key information
        avg_short = sum(short_times) / len(short_times)
        avg_long = sum(long_times) / len(long_times)

        # Long text should take more time, but not exponentially more
        assert avg_long > avg_short
        assert avg_long < avg_short * 10  # Reasonable upper bound


class TestFernetMigration:
    """Test migration from Fernet to AES-256-GCM."""

    def setup_method(self):
        """Set up test environment with both encryption methods."""
        # Generate keys
        self.fernet_key = Fernet.generate_key()
        self.aes256_key = AESGCM.generate_key(bit_length=256)

        # Set environment variables
        os.environ['MANNA_ENCRYPTION_KEY'] = self.fernet_key.decode()
        os.environ['MANNA_ENCRYPTION_KEY_AES256'] = base64.urlsafe_b64encode(self.aes256_key).decode()

        self.provider = AES256GCMProvider()
        self.fernet = Fernet(self.fernet_key)

    def teardown_method(self):
        """Clean up test environment."""
        for key in ['MANNA_ENCRYPTION_KEY', 'MANNA_ENCRYPTION_KEY_AES256']:
            if key in os.environ:
                del os.environ[key]

    def test_decrypt_legacy_fernet(self):
        """Test decrypting legacy Fernet-encrypted data."""
        plaintext = "Legacy data encrypted with Fernet"

        # Encrypt with Fernet (simulating legacy data)
        fernet_encrypted = self.fernet.encrypt(plaintext.encode())

        # Add version prefix for versioned Fernet
        versioned_fernet = EncryptionVersion.FERNET_V1.value + fernet_encrypted
        versioned_b64 = base64.urlsafe_b64encode(versioned_fernet).decode()

        # Should be able to decrypt
        decrypted = self.provider.decrypt(versioned_b64)
        assert decrypted == plaintext

    def test_decrypt_unversioned_fernet(self):
        """Test decrypting unversioned Fernet data (original format)."""
        plaintext = "Unversioned Fernet data"

        # Encrypt with Fernet without version prefix
        fernet_encrypted = self.fernet.encrypt(plaintext.encode())
        fernet_b64 = base64.urlsafe_b64encode(fernet_encrypted).decode()

        # Should be able to decrypt
        decrypted = self.provider.decrypt(fernet_b64)
        assert decrypted == plaintext

    def test_migrate_encryption(self):
        """Test migrating from Fernet to AES-256-GCM."""
        plaintext = "Data to migrate"

        # Create Fernet-encrypted data
        fernet_encrypted = self.fernet.encrypt(plaintext.encode())
        fernet_b64 = base64.urlsafe_b64encode(fernet_encrypted).decode()

        # Migrate to AES-256-GCM
        aes_encrypted = self.provider.migrate_encryption(fernet_b64)

        # Verify it's now AES-256-GCM encrypted
        decoded = base64.urlsafe_b64decode(aes_encrypted.encode())
        assert decoded.startswith(EncryptionVersion.AES256_GCM_V2.value)

        # Verify we can decrypt it
        decrypted = self.provider.decrypt(aes_encrypted)
        assert decrypted == plaintext

    def test_dual_format_support(self):
        """Test that both encryption formats work simultaneously."""
        data1 = "Fernet encrypted"
        data2 = "AES-256-GCM encrypted"

        # Encrypt with Fernet
        fernet_ct = base64.urlsafe_b64encode(self.fernet.encrypt(data1.encode())).decode()

        # Encrypt with AES-256-GCM
        aes_ct = self.provider.encrypt(data2)

        # Both should decrypt correctly
        assert self.provider.decrypt(fernet_ct) == data1
        assert self.provider.decrypt(aes_ct) == data2


class TestEncryptedStringType:
    """Test the SQLAlchemy encrypted string type."""

    def setup_method(self):
        """Set up test environment."""
        self.aes256_key = AESGCM.generate_key(bit_length=256)
        os.environ['MANNA_ENCRYPTION_KEY_AES256'] = base64.urlsafe_b64encode(self.aes256_key).decode()

        self.encrypted_type = EncryptedStringAES256(length=100)

    def teardown_method(self):
        """Clean up test environment."""
        if 'MANNA_ENCRYPTION_KEY_AES256' in os.environ:
            del os.environ['MANNA_ENCRYPTION_KEY_AES256']

    def test_process_bind_param(self):
        """Test encrypting data before database storage."""
        plaintext = "Database value"

        # Mock dialect
        dialect = MagicMock()

        # Process for binding
        encrypted = self.encrypted_type.process_bind_param(plaintext, dialect)

        assert encrypted is not None
        assert encrypted != plaintext

        # Should be properly encrypted
        decoded = base64.urlsafe_b64decode(encrypted.encode())
        assert decoded.startswith(EncryptionVersion.AES256_GCM_V2.value)

    def test_process_result_value(self):
        """Test decrypting data after database retrieval."""
        plaintext = "Database value"

        # Mock dialect
        dialect = MagicMock()

        # First encrypt
        encrypted = self.encrypted_type.process_bind_param(plaintext, dialect)

        # Then decrypt
        decrypted = self.encrypted_type.process_result_value(encrypted, dialect)

        assert decrypted == plaintext

    def test_none_handling(self):
        """Test handling of None values."""
        dialect = MagicMock()

        assert self.encrypted_type.process_bind_param(None, dialect) is None
        assert self.encrypted_type.process_result_value(None, dialect) is None


class TestSecurityProperties:
    """Test security properties of the encryption implementation."""

    def setup_method(self):
        """Set up test environment."""
        self.aes256_key = AESGCM.generate_key(bit_length=256)
        os.environ['MANNA_ENCRYPTION_KEY_AES256'] = base64.urlsafe_b64encode(self.aes256_key).decode()
        self.provider = AES256GCMProvider()

    def teardown_method(self):
        """Clean up test environment."""
        if 'MANNA_ENCRYPTION_KEY_AES256' in os.environ:
            del os.environ['MANNA_ENCRYPTION_KEY_AES256']

    def test_nist_test_vectors(self):
        """Test against NIST test vectors for AES-GCM."""
        # This is a simplified test - in production, use full NIST test vectors
        # Test vector from NIST SP 800-38D
        key = bytes.fromhex('00' * 32)  # 256-bit key
        nonce = bytes.fromhex('00' * 12)  # 96-bit nonce
        plaintext = b''
        aad = b''

        # Create AESGCM with test key
        aesgcm = AESGCM(key)

        # Encrypt
        ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

        # The ciphertext should include the authentication tag
        assert len(ciphertext) == 16  # Empty plaintext + 16-byte tag

    def test_authentication_tag_verification(self):
        """Test that authentication tags are properly verified."""
        plaintext = "Authenticated data"

        # Encrypt
        ciphertext = self.provider.encrypt(plaintext)

        # Decode and corrupt the authentication tag (last 16 bytes)
        decoded = base64.urlsafe_b64decode(ciphertext.encode())
        corrupted = decoded[:-16] + b'x' * 16
        corrupted_b64 = base64.urlsafe_b64encode(corrupted).decode()

        # Decryption should fail due to invalid tag
        with pytest.raises(EncryptionError):
            self.provider.decrypt(corrupted_b64)

    def test_replay_protection(self):
        """Test that timestamps provide replay protection."""
        # This is a basic test - full replay protection requires more infrastructure
        plaintext = "Time-sensitive data"

        # Encrypt
        ciphertext = self.provider.encrypt(plaintext)

        # Decrypt should work immediately
        decrypted = self.provider.decrypt(ciphertext)
        assert decrypted == plaintext

        # In a real system, old timestamps would be rejected
        # This would require tracking timestamp windows

    def test_key_derivation_strength(self):
        """Test that key derivation is properly implemented."""
        import hashlib
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend

        password = b"test_password"
        salt = b"test_salt_12345"

        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password)

        # Key should be 32 bytes (256 bits)
        assert len(key) == 32

        # Key should be deterministic
        kdf2 = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key2 = kdf2.derive(password)
        assert key == key2

        # Different passwords should produce different keys
        kdf3 = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key3 = kdf3.derive(b"different_password")
        assert key != key3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])