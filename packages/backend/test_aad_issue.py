"""
Test script to verify the AAD timestamp issue that prevents decryption.

This test demonstrates the critical issue where encryption uses one timestamp
and decryption uses a different timestamp, causing authentication failures.
"""

import os
import sys
import time
import base64
sys.path.insert(0, '.')

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.core.encryption_aes256 import AES256GCMProvider, EncryptionError

def test_aad_timestamp_issue():
    """Test the AAD timestamp issue that prevents decryption."""

    # Set up encryption provider
    aes256_key = AESGCM.generate_key(bit_length=256)
    aes256_key_b64 = base64.urlsafe_b64encode(aes256_key).decode()
    os.environ['MANNA_ENCRYPTION_KEY_AES256'] = aes256_key_b64

    provider = AES256GCMProvider()

    print("=== Testing AAD Timestamp Issue ===")

    # Test 1: Basic encryption/decryption without delay
    print("\n1. Testing immediate encrypt/decrypt (should work):")
    plaintext = "Test message for immediate encryption"

    try:
        encrypted = provider.encrypt(plaintext)
        decrypted = provider.decrypt(encrypted)
        print(f"  ✓ Immediate decrypt succeeded: '{decrypted}'")
    except Exception as e:
        print(f"  ✗ Immediate decrypt failed: {e}")

    # Test 2: Encryption with delay before decryption
    print("\n2. Testing encrypt/decrypt with delay (demonstrates the issue):")
    plaintext2 = "Test message with delayed decryption"

    try:
        encrypted2 = provider.encrypt(plaintext2)
        print(f"  ✓ Encryption succeeded")

        # Wait to simulate delay between encrypt/decrypt operations
        time.sleep(2)

        # This should fail due to timestamp mismatch in AAD
        decrypted2 = provider.decrypt(encrypted2)
        print(f"  ✓ Delayed decrypt succeeded: '{decrypted2}'")
        print("  ⚠️  WARNING: This should have failed due to AAD timestamp mismatch!")

    except EncryptionError as e:
        print(f"  ✗ Delayed decrypt failed as expected: {e}")
        print("  → This demonstrates the AAD timestamp issue")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")

    # Test 3: Demonstrate the root cause
    print("\n3. Analyzing the root cause:")
    print("   The issue is in encryption_aes256.py lines 193-194 and 247-248:")
    print("   - Encryption: timestamp = struct.pack('>Q', int(datetime.utcnow().timestamp()))")
    print("   - Decryption: timestamp = struct.pack('>Q', int(datetime.utcnow().timestamp()))")
    print("   → Each call generates a different timestamp, breaking AAD authentication")

    # Test 4: Show working encryption without AAD timestamp
    print("\n4. Testing encryption without problematic AAD timestamp:")
    try:
        # Manually test with fixed AAD
        import struct
        from datetime import datetime

        plaintext3 = "Test with fixed AAD timestamp"
        fixed_timestamp = struct.pack('>Q', int(datetime.utcnow().timestamp()))

        # Create provider without global instance to avoid timestamp issues
        # (AESGCM already imported at module level)
        import secrets

        aesgcm = AESGCM(aes256_key)
        nonce = secrets.token_bytes(12)
        plaintext_bytes = plaintext3.encode('utf-8')

        # Encrypt with fixed timestamp
        ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, fixed_timestamp)

        # Decrypt with same timestamp
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, fixed_timestamp)
        decrypted3 = decrypted_bytes.decode('utf-8')

        print(f"  ✓ Fixed AAD encryption/decryption works: '{decrypted3}'")

        # Now try with different timestamp (should fail)
        time.sleep(1)
        different_timestamp = struct.pack('>Q', int(datetime.utcnow().timestamp()))

        try:
            aesgcm.decrypt(nonce, ciphertext, different_timestamp)
            print("  ⚠️  WARNING: Different timestamp should have failed!")
        except Exception as e:
            print(f"  ✓ Different timestamp correctly failed: {type(e).__name__}")

    except Exception as e:
        print(f"  ✗ Fixed AAD test failed: {e}")

    # Cleanup
    if 'MANNA_ENCRYPTION_KEY_AES256' in os.environ:
        del os.environ['MANNA_ENCRYPTION_KEY_AES256']

if __name__ == "__main__":
    test_aad_timestamp_issue()