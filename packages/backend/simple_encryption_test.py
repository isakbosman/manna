#!/usr/bin/env python3
"""
Simple test for AES-256-GCM encryption functionality.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_encryption():
    """Test basic AES-256-GCM encryption."""
    print("Testing AES-256-GCM encryption...")

    try:
        from src.core.encryption import (
            encrypt_string, decrypt_string, is_encryption_initialized,
            get_encryption_info, generate_aes256_key
        )

        # Test initialization
        print("1. Checking encryption initialization...")
        initialized = is_encryption_initialized()
        print(f"   Encryption initialized: {initialized}")

        if not initialized:
            print("   ERROR: Encryption not initialized")
            return False

        # Get info
        print("2. Getting encryption info...")
        info = get_encryption_info()
        print(f"   Info: {info}")

        # Test encryption/decryption
        print("3. Testing encryption/decryption...")
        test_data = "test_access_token_12345"

        encrypted = encrypt_string(test_data)
        print(f"   Original: {test_data}")
        print(f"   Encrypted: {encrypted[:50]}...")

        decrypted = decrypt_string(encrypted)
        print(f"   Decrypted: {decrypted}")

        if decrypted == test_data:
            print("   ✓ Encryption/decryption successful!")
        else:
            print("   ✗ Encryption/decryption failed!")
            return False

        # Test key generation
        print("4. Testing key generation...")
        key = generate_aes256_key()
        print(f"   Generated key length: {len(key)} chars")

        print("✓ All tests passed!")
        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_optimistic_locking():
    """Test optimistic locking functionality."""
    print("\nTesting optimistic locking...")

    try:
        from src.core.locking import OptimisticLockMixin

        # Create a simple test class
        class TestModel(OptimisticLockMixin):
            def __init__(self):
                self.id = "test-123"
                self.version = 1

        # Test the mixin
        print("1. Creating test model...")
        model = TestModel()
        print(f"   Model version: {model.version}")

        print("2. Testing version increment...")
        model.increment_version()
        print(f"   New version: {model.version}")

        if model.version == 2:
            print("   ✓ Version increment successful!")
        else:
            print("   ✗ Version increment failed!")
            return False

        print("✓ Optimistic locking tests passed!")
        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running simple encryption and locking tests...\n")

    test1 = test_basic_encryption()
    test2 = test_optimistic_locking()

    print(f"\nResults:")
    print(f"Encryption: {'PASS' if test1 else 'FAIL'}")
    print(f"Locking: {'PASS' if test2 else 'FAIL'}")

    if test1 and test2:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)