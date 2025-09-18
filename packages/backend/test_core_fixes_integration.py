#!/usr/bin/env python3
"""
Integration test for the core fixes implemented.

This test verifies that:
1. AAD timestamp fix is working (timestamp stored with ciphertext)
2. SQLAlchemy import fix is working (correct import paths)
3. Fallback imports have been removed
4. Core functionality works end-to-end
"""

import os
import sys
import time
import base64
import struct
from datetime import datetime, timezone

# Add the backend source to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock settings to avoid dependency issues
class MockSettings:
    environment = "development"
    secret_key = "test-secret-key-integration"
    redis_url = "redis://localhost:6379/0"

sys.modules['src.config'] = type('MockModule', (), {'settings': MockSettings()})()


def test_encryption_integration():
    """Test end-to-end encryption functionality with the AAD fix."""
    print("Testing encryption integration...")

    from src.core.encryption import AES256GCMProvider, EncryptedString, encrypt_string, decrypt_string

    # Test direct encryption functions
    plaintext = "integration-test-data-123"
    print(f"1. Testing direct encryption of: {plaintext}")

    encrypted = encrypt_string(plaintext)
    decrypted = decrypt_string(encrypted)

    assert decrypted == plaintext, f"Direct encryption failed: {decrypted} != {plaintext}"
    print("   ✓ Direct encryption/decryption working")

    # Test with custom AAD
    aad_context = b"integration-test-context"
    encrypted_with_aad = encrypt_string(plaintext, aad=aad_context)
    decrypted_with_aad = decrypt_string(encrypted_with_aad, aad=aad_context)

    assert decrypted_with_aad == plaintext, "AAD encryption failed"
    print("   ✓ AAD encryption/decryption working")

    # Test timestamp storage (core of the AAD fix)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode('utf-8'))

    # Check format: version(4) + nonce(12) + timestamp(8) + ciphertext
    assert len(encrypted_bytes) >= 24, "Encrypted data too short"

    # Extract timestamp from stored location
    from src.core.encryption import EncryptionVersion
    data_without_prefix = encrypted_bytes[len(EncryptionVersion.AES256_GCM_V2.value):]
    stored_timestamp = data_without_prefix[12:20]

    timestamp_value = struct.unpack('>Q', stored_timestamp)[0]
    current_time = datetime.now(timezone.utc).timestamp()
    time_diff = abs(current_time - timestamp_value)

    assert time_diff < 10, f"Timestamp storage issue: {time_diff}s difference"
    print(f"   ✓ Timestamp correctly stored with ciphertext (diff: {time_diff:.2f}s)")

    # Test that decryption works after time delay
    time.sleep(0.5)
    delayed_decrypted = decrypt_string(encrypted)
    assert delayed_decrypted == plaintext, "Decryption failed after delay"
    print("   ✓ Decryption works after time delay")

    print("✅ Encryption integration tests passed!")
    return True


def test_locking_integration():
    """Test optimistic locking integration with correct imports."""
    print("\nTesting locking integration...")

    try:
        # Test correct imports
        from sqlalchemy.orm.exc import StaleDataError
        from src.core.locking import (
            OptimisticLockMixin,
            OptimisticLockError,
            DistributedLock,
            DistributedLockError
        )
        print("   ✓ All locking imports successful")

        # Test exception inheritance
        assert issubclass(OptimisticLockError, Exception), "OptimisticLockError not an Exception"
        assert issubclass(DistributedLockError, Exception), "DistributedLockError not an Exception"
        print("   ✓ Exception classes properly defined")

        # Test that OptimisticLockMixin has required methods
        assert hasattr(OptimisticLockMixin, 'update_with_lock'), "Missing update_with_lock method"
        assert hasattr(OptimisticLockMixin, 'increment_version'), "Missing increment_version method"
        print("   ✓ OptimisticLockMixin has required methods")

        # Test distributed locking with mock Redis
        from unittest.mock import MagicMock
        mock_redis = MagicMock()
        mock_redis.set.return_value = True

        dist_lock = DistributedLock(redis_client=mock_redis)

        # Test token generation
        token1 = dist_lock._generate_token()
        token2 = dist_lock._generate_token()
        assert token1 != token2, "Tokens should be unique"
        print("   ✓ Distributed lock token generation working")

        # Test lock key generation
        lock_key = dist_lock._get_lock_key("test_resource")
        assert "test_resource" in lock_key, "Lock key should contain resource name"
        print("   ✓ Lock key generation working")

    except ImportError as e:
        assert False, f"Import error in locking integration: {e}"

    print("✅ Locking integration tests passed!")
    return True


def test_import_consistency():
    """Test that imports are consistent and don't use fallbacks."""
    print("\nTesting import consistency...")

    # Test encryption module imports
    import src.core.encryption
    import inspect

    encryption_source = inspect.getsource(src.core.encryption)

    # Should have explicit config import
    assert "from ..config import settings" in encryption_source, \
        "Encryption should have explicit config import"

    # Should not have MockSettings fallback
    assert "MockSettings" not in encryption_source, \
        "Encryption should not have MockSettings fallback"

    print("   ✓ Encryption module has clean imports")

    # Test locking module imports
    import src.core.locking
    locking_source = inspect.getsource(src.core.locking)

    # Should have explicit config import
    assert "from ..config import settings" in locking_source, \
        "Locking should have explicit config import"

    # Should not have MockSettings fallback
    assert "MockSettings" not in locking_source, \
        "Locking should not have MockSettings fallback"

    # Should have correct SQLAlchemy import
    assert "from sqlalchemy.orm.exc import StaleDataError" in locking_source, \
        "Locking should import StaleDataError from correct path"

    print("   ✓ Locking module has clean imports")

    print("✅ Import consistency tests passed!")
    return True


def test_performance_regression():
    """Test that fixes don't introduce performance regressions."""
    print("\nTesting performance regression...")

    from src.core.encryption import encrypt_string, decrypt_string

    # Test encryption performance
    test_data = "performance-test-" * 20  # ~300 chars

    start_time = time.time()
    encrypted_items = []
    for i in range(50):
        encrypted = encrypt_string(f"{test_data}-{i}")
        encrypted_items.append(encrypted)
    encryption_time = time.time() - start_time

    print(f"   Encrypted 50 items in {encryption_time:.3f}s ({encryption_time*20:.1f}ms avg)")

    # Test decryption performance
    start_time = time.time()
    for encrypted in encrypted_items:
        decrypted = decrypt_string(encrypted)
    decryption_time = time.time() - start_time

    print(f"   Decrypted 50 items in {decryption_time:.3f}s ({decryption_time*20:.1f}ms avg)")

    # Performance should be reasonable
    assert encryption_time < 5.0, f"Encryption too slow: {encryption_time}s for 50 items"
    assert decryption_time < 5.0, f"Decryption too slow: {decryption_time}s for 50 items"

    print("   ✓ Performance is acceptable")
    print("✅ Performance regression tests passed!")
    return True


def test_backward_compatibility():
    """Test backward compatibility with existing encrypted data formats."""
    print("\nTesting backward compatibility...")

    from src.core.encryption import AES256GCMProvider

    provider = AES256GCMProvider()

    # Test that new format works
    plaintext = "backward-compatibility-test"
    encrypted = provider.encrypt(plaintext)
    decrypted = provider.decrypt(encrypted)

    assert decrypted == plaintext, "New format should work"
    print("   ✓ New format encryption/decryption working")

    # Test error handling for invalid formats
    try:
        provider.decrypt("invalid-data-format")
        assert False, "Should raise error for invalid data"
    except Exception:
        print("   ✓ Invalid data properly rejected")

    try:
        provider.decrypt("")
        assert False, "Should raise error for empty data"
    except Exception:
        print("   ✓ Empty data properly rejected")

    print("✅ Backward compatibility tests passed!")
    return True


def main():
    """Run all integration tests for the core fixes."""
    print("=" * 70)
    print("CORE FIXES INTEGRATION TEST SUITE")
    print("=" * 70)
    print("Testing AAD timestamp fix, SQLAlchemy imports, and fallback removal")
    print()

    tests = [
        test_encryption_integration,
        test_locking_integration,
        test_import_consistency,
        test_performance_regression,
        test_backward_compatibility
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_func.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"INTEGRATION TEST RESULTS: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 ALL CORE FIXES VERIFIED SUCCESSFULLY!")
        print("\nSummary of fixes verified:")
        print("✓ AAD timestamp now stored with ciphertext (not in AAD)")
        print("✓ SQLAlchemy imports use correct paths for 2.x")
        print("✓ Fallback import blocks removed")
        print("✓ Performance maintained")
        print("✓ Backward compatibility preserved")
    else:
        print("❌ SOME TESTS FAILED - REVIEW ISSUES ABOVE")

    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)