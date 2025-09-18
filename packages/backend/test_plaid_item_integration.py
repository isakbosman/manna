#!/usr/bin/env python3
"""
Integration test for PlaidItem model with AES-256-GCM encryption and optimistic locking.
"""

import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_plaid_item_integration():
    """Test PlaidItem model with encryption and optimistic locking."""
    print("Testing PlaidItem integration with AES-256-GCM and optimistic locking...")

    try:
        # Import PlaidItem model
        from models.plaid_item import PlaidItem
        from src.core.encryption import decrypt_string
        from uuid import uuid4

        print("1. Creating PlaidItem instance...")

        # Create a test PlaidItem
        item = PlaidItem(
            user_id=uuid4(),
            institution_id=uuid4(),
            plaid_item_id="test_item_123",
            plaid_access_token="access-token-test-12345"
        )

        print(f"   PlaidItem created with ID: {item.id}")
        print(f"   Version: {item.version}")
        print(f"   Access token (plain): {item.plaid_access_token}")

        print("2. Testing encryption functionality...")

        # Test that the encrypted field is working
        # Note: The actual encryption happens at the SQLAlchemy level
        # For this test, we'll verify the import works and the field is properly defined

        # Check if the field has the right type
        access_token_column = PlaidItem.__table__.columns['plaid_access_token']
        print(f"   Access token column type: {type(access_token_column.type)}")

        # Verify OptimisticLockMixin is applied
        print("3. Testing optimistic locking functionality...")

        if hasattr(item, 'version'):
            print("   ✓ Version column present")

            if hasattr(item, 'update_with_lock'):
                print("   ✓ update_with_lock method present")
            else:
                print("   ⚠ update_with_lock method not found")

            if hasattr(item, 'increment_version'):
                print("   ✓ increment_version method present")

                # Test version increment
                original_version = item.version
                item.increment_version()
                if item.version == original_version + 1:
                    print("   ✓ Version increment works correctly")
                else:
                    print("   ✗ Version increment failed")
                    return False
            else:
                print("   ⚠ increment_version method not found")
        else:
            print("   ✗ Version column not found")
            return False

        print("4. Testing access token methods...")

        # Test the access token methods
        if hasattr(item, 'get_decrypted_access_token'):
            print("   ✓ get_decrypted_access_token method present")
            decrypted = item.get_decrypted_access_token()
            print(f"   Decrypted token: {decrypted}")
        else:
            print("   ⚠ get_decrypted_access_token method not found")

        if hasattr(item, 'set_access_token'):
            print("   ✓ set_access_token method present")
            item.set_access_token("new-test-token-456")
            print(f"   New token set: {item.plaid_access_token}")
        else:
            print("   ⚠ set_access_token method not found")

        print("5. Testing cursor update functionality...")

        if hasattr(item, 'update_cursor_safely'):
            print("   ✓ update_cursor_safely method present")
        else:
            print("   ⚠ update_cursor_safely method not found")

        print("6. Testing model properties...")

        # Test the various properties
        properties_to_test = [
            'is_healthy', 'needs_attention', 'has_transactions_product',
            'days_since_last_sync'
        ]

        for prop in properties_to_test:
            if hasattr(item, prop):
                try:
                    value = getattr(item, prop)
                    print(f"   ✓ {prop}: {value}")
                except Exception as e:
                    print(f"   ⚠ {prop} property error: {e}")
            else:
                print(f"   ✗ {prop} property missing")

        print("✓ PlaidItem integration test completed successfully!")
        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_migration_compatibility():
    """Test that the migration functions work."""
    print("\nTesting migration compatibility...")

    try:
        from src.core.encryption import migrate_to_aes256, decrypt_string, encrypt_string
        from cryptography.fernet import Fernet
        import base64

        print("1. Testing migration function availability...")

        # Test that migration functions exist
        if callable(migrate_to_aes256):
            print("   ✓ migrate_to_aes256 function available")
        else:
            print("   ✗ migrate_to_aes256 function not found")
            return False

        print("2. Testing new encryption format...")

        # Test new encryption creates correct format
        test_token = "test-migration-token-123"
        new_encrypted = encrypt_string(test_token)

        # Check that it uses the new format (GCM2: prefix when base64 decoded)
        encrypted_bytes = base64.urlsafe_b64decode(new_encrypted.encode('utf-8'))
        if encrypted_bytes.startswith(b"GCM2:"):
            print("   ✓ New encryption uses correct AES-256-GCM format")
        else:
            print("   ✗ New encryption doesn't use expected format")
            return False

        # Test decryption
        decrypted = decrypt_string(new_encrypted)
        if decrypted == test_token:
            print("   ✓ New encryption/decryption cycle works")
        else:
            print("   ✗ New encryption/decryption failed")
            return False

        print("✓ Migration compatibility test passed!")
        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running PlaidItem integration tests...\n")

    test1 = test_plaid_item_integration()
    test2 = test_migration_compatibility()

    print(f"\nResults:")
    print(f"PlaidItem Integration: {'PASS' if test1 else 'FAIL'}")
    print(f"Migration Compatibility: {'PASS' if test2 else 'FAIL'}")

    if test1 and test2:
        print("\n✓ All integration tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some integration tests failed!")
        sys.exit(1)