#!/usr/bin/env python3
"""
Test only the core functionality without SQLAlchemy events and model creation.
"""

import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_encryption_core():
    """Test core encryption functionality."""
    print("Testing core AES-256-GCM encryption...")

    try:
        from src.core.encryption import (
            encrypt_string, decrypt_string, is_encryption_initialized,
            get_encryption_info, generate_aes256_key, _aes256_provider
        )

        # Test 1: Initialization
        assert is_encryption_initialized(), "Encryption not initialized"
        print("   ✓ Encryption initialized")

        # Test 2: Basic encryption/decryption
        test_data = "plaid-access-token-test-123"
        encrypted = encrypt_string(test_data)
        decrypted = decrypt_string(encrypted)
        assert decrypted == test_data, f"Encryption failed: {decrypted} != {test_data}"
        print("   ✓ Basic encryption/decryption works")

        # Test 3: Verify provider is AES256GCMProvider
        from src.core.encryption import AES256GCMProvider
        assert isinstance(_aes256_provider, AES256GCMProvider), "Wrong provider type"
        print("   ✓ Using AES256GCMProvider")

        # Test 4: Verify encryption format
        import base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode('utf-8'))
        assert encrypted_bytes.startswith(b"GCM2:"), "Missing AES-256-GCM prefix"
        print("   ✓ Correct encryption format (GCM2:)")

        # Test 5: Key generation
        key = generate_aes256_key()
        key_bytes = base64.urlsafe_b64decode(key.encode())
        assert len(key_bytes) == 32, f"Wrong key length: {len(key_bytes)}"
        print("   ✓ Key generation works")

        # Test 6: Encryption info
        info = get_encryption_info()
        assert info['algorithm'] == 'AES-256-GCM', "Wrong algorithm"
        assert info['initialized'], "Not reporting as initialized"
        print("   ✓ Encryption info correct")

        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_locking_core():
    """Test core locking functionality without SQLAlchemy events."""
    print("\nTesting core optimistic locking...")

    try:
        from src.core.locking import (
            OptimisticLockMixin, OptimisticLockError,
            DistributedLock, get_distributed_lock
        )

        # Test 1: Mixin functionality
        class SimpleMixin(OptimisticLockMixin):
            def __init__(self):
                self.id = "test-123"
                self.version = 1

        instance = SimpleMixin()
        assert hasattr(instance, 'version'), "Version attribute missing"
        assert instance.version == 1, "Initial version wrong"
        print("   ✓ OptimisticLockMixin basic functionality")

        # Test 2: Version increment
        instance.increment_version()
        assert instance.version == 2, f"Version increment failed: {instance.version}"
        print("   ✓ Version increment works")

        # Test 3: Method presence
        assert hasattr(instance, 'update_with_lock'), "update_with_lock missing"
        assert hasattr(instance, 'refresh_version'), "refresh_version missing"
        print("   ✓ Required methods present")

        # Test 4: Distributed lock
        dist_lock = get_distributed_lock()
        assert isinstance(dist_lock, DistributedLock), "Wrong distributed lock type"
        print("   ✓ DistributedLock creation works")

        # Test 5: Lock key generation
        lock_key = dist_lock._get_lock_key("test_resource")
        assert lock_key == "manna:lock:test_resource", f"Wrong lock key: {lock_key}"
        print("   ✓ Lock key generation works")

        # Test 6: Token generation
        token = dist_lock._generate_token()
        assert len(token) > 10, "Token too short"
        assert ":" in token, "Token format wrong"
        print("   ✓ Token generation works")

        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_migration_functionality():
    """Test migration-related functionality."""
    print("\nTesting migration functionality...")

    try:
        from src.core.encryption import migrate_to_aes256, encrypt_string, decrypt_string

        # Test 1: Migration function exists
        assert callable(migrate_to_aes256), "migrate_to_aes256 not callable"
        print("   ✓ Migration function available")

        # Test 2: Migrate new format (should be no-op)
        test_data = "migration-test-token-456"
        new_encrypted = encrypt_string(test_data)

        # This should work without errors (migrating new format to new format)
        migrated = migrate_to_aes256(new_encrypted)
        migrated_decrypted = decrypt_string(migrated)
        assert migrated_decrypted == test_data, "Migration of new format failed"
        print("   ✓ New format migration works")

        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sqlalchemy_type():
    """Test SQLAlchemy type decorator without model creation."""
    print("\nTesting SQLAlchemy type decorator...")

    try:
        from src.core.encryption import EncryptedString

        # Test 1: Type creation
        encrypted_type = EncryptedString(100)
        assert encrypted_type.impl.length == 300, "Length calculation wrong"  # 100 * 3
        print("   ✓ EncryptedString type creation")

        # Test 2: Value processing
        test_value = "test-sqlalchemy-value-123"
        bound_value = encrypted_type.process_bind_param(test_value, None)
        result_value = encrypted_type.process_result_value(bound_value, None)
        assert result_value == test_value, "Type decorator failed"
        print("   ✓ Type value processing works")

        # Test 3: None handling
        none_bound = encrypted_type.process_bind_param(None, None)
        none_result = encrypted_type.process_result_value(None, None)
        assert none_bound is None and none_result is None, "None handling failed"
        print("   ✓ None value handling works")

        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all core tests."""
    print("Running core implementation tests (no SQLAlchemy events)...\n")

    tests = [
        ("Encryption Core", test_encryption_core),
        ("Locking Core", test_locking_core),
        ("Migration Functionality", test_migration_functionality),
        ("SQLAlchemy Type", test_sqlalchemy_type),
    ]

    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()

    print(f"\n{'='*60}")
    print("CORE IMPLEMENTATION TEST RESULTS")
    print(f"{'='*60}")

    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    total = len(tests)
    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ ALL CORE IMPLEMENTATIONS WORKING!")
        print("\nImplementation Summary:")
        print("1. ✓ AES-256-GCM encryption working correctly")
        print("2. ✓ Optimistic locking mixin implemented")
        print("3. ✓ Migration functions available")
        print("4. ✓ SQLAlchemy type decorator working")
        print("5. ✓ Distributed locking implemented")
        print("\nNext Steps:")
        print("1. Run migration: alembic upgrade head")
        print("2. Set production encryption key: MANNA_ENCRYPTION_KEY_AES256")
        print("3. Test with real database connections")
        print("4. Update environment configuration")
        return True
    else:
        print(f"\n✗ {total - passed} implementation(s) need fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)