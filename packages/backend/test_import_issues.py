"""
Test script to identify import path issues in the implementation.
"""

import sys
import os
sys.path.insert(0, '.')

def test_plaid_item_imports():
    """Test PlaidItem model imports."""
    print("=== Testing PlaidItem Model Imports ===")

    try:
        from models.plaid_item import PlaidItem
        print("✓ PlaidItem imported successfully")

        # Test if encryption and locking mixins are available
        item = PlaidItem()

        if hasattr(item, 'plaid_access_token'):
            print("✓ plaid_access_token field available")
        else:
            print("✗ plaid_access_token field missing")

        if hasattr(item, 'version'):
            print("✓ version field available (optimistic locking)")
        else:
            print("✗ version field missing (optimistic locking not working)")

        if hasattr(item, 'update_with_lock'):
            print("✓ update_with_lock method available")
        else:
            print("✗ update_with_lock method missing")

    except ImportError as e:
        print(f"✗ Failed to import PlaidItem: {e}")

def test_core_imports():
    """Test core module imports."""
    print("\n=== Testing Core Module Imports ===")

    # Test encryption imports
    try:
        from src.core.encryption import EncryptedString
        print("✓ EncryptedString from src.core.encryption imported")
    except ImportError as e:
        print(f"✗ src.core.encryption import failed: {e}")

    try:
        from src.core.locking import OptimisticLockMixin
        print("✓ OptimisticLockMixin from src.core.locking imported")
    except ImportError as e:
        print(f"✗ src.core.locking import failed: {e}")

    # Test the fallback imports that PlaidItem tries
    print("\n--- Testing PlaidItem fallback imports ---")

    try:
        from ..src.core.encryption import EncryptedString
        print("✓ Relative import ..src.core.encryption works")
    except (ImportError, ValueError) as e:
        print(f"✗ Relative import ..src.core.encryption failed: {e}")

    try:
        from src.core.encryption import EncryptedString
        print("✓ Direct import src.core.encryption works")
    except ImportError as e:
        print(f"✗ Direct import src.core.encryption failed: {e}")

def test_stale_data_error():
    """Test StaleDataError import fix."""
    print("\n=== Testing StaleDataError Import ===")

    # Test the broken import (what's currently in the code)
    try:
        from sqlalchemy.exc import StaleDataError
        print("✓ StaleDataError from sqlalchemy.exc imported (unexpected)")
    except ImportError as e:
        print(f"✗ sqlalchemy.exc.StaleDataError failed (as expected): {e}")

    # Test the correct import
    try:
        from sqlalchemy.orm.exc import StaleDataError
        print("✓ StaleDataError from sqlalchemy.orm.exc imported (correct)")
    except ImportError as e:
        print(f"✗ sqlalchemy.orm.exc.StaleDataError failed: {e}")

def test_actual_usage():
    """Test actual usage patterns."""
    print("\n=== Testing Actual Usage ===")

    try:
        # Import what the models actually need
        from models.base import Base, UUIDMixin, TimestampMixin
        print("✓ Base model imports work")

        # Try to import with the actual fallback pattern
        try:
            from src.core.encryption import EncryptedString
            from src.core.locking import OptimisticLockMixin
            print("✓ Core modules imported via fallback pattern")
            encryption_available = True
            locking_available = True
        except ImportError:
            print("✗ Core modules not available, using fallbacks")
            EncryptedString = str  # Fallback
            class OptimisticLockMixin:
                pass
            encryption_available = False
            locking_available = False

        print(f"  Encryption available: {encryption_available}")
        print(f"  Optimistic locking available: {locking_available}")

    except ImportError as e:
        print(f"✗ Base model import failed: {e}")

if __name__ == "__main__":
    test_plaid_item_imports()
    test_core_imports()
    test_stale_data_error()
    test_actual_usage()