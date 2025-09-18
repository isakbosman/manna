"""
Performance testing for AES-256-GCM encryption and optimistic locking.
"""

import os
import sys
import time
import statistics
import base64
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.')

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.core.encryption_aes256 import AES256GCMProvider, EncryptedStringAES256

def performance_test_encryption():
    """Test encryption/decryption performance."""
    print("=== AES-256-GCM Encryption Performance Test ===")

    # Set up encryption
    aes256_key = AESGCM.generate_key(bit_length=256)
    aes256_key_b64 = base64.urlsafe_b64encode(aes256_key).decode()
    os.environ['MANNA_ENCRYPTION_KEY_AES256'] = aes256_key_b64

    provider = AES256GCMProvider()

    # Test data of different sizes
    test_data = {
        "small": "access_token_123",
        "medium": "plaid_access_token_" + "x" * 100,
        "large": "very_long_access_token_" + "x" * 1000
    }

    for size_name, plaintext in test_data.items():
        print(f"\nTesting {size_name} data ({len(plaintext)} chars):")

        # Encryption performance
        encrypt_times = []
        decrypt_times = []

        for _ in range(1000):
            # Encrypt
            start = time.perf_counter()
            encrypted = provider.encrypt(plaintext)
            encrypt_times.append((time.perf_counter() - start) * 1000)  # ms

            # Decrypt
            start = time.perf_counter()
            decrypted = provider.decrypt(encrypted)
            decrypt_times.append((time.perf_counter() - start) * 1000)  # ms

            assert decrypted == plaintext

        print(f"  Encryption: avg={statistics.mean(encrypt_times):.2f}ms, "
              f"p95={sorted(encrypt_times)[int(0.95 * len(encrypt_times))]:.2f}ms")
        print(f"  Decryption: avg={statistics.mean(decrypt_times):.2f}ms, "
              f"p95={sorted(decrypt_times)[int(0.95 * len(decrypt_times))]:.2f}ms")

    # Cleanup
    del os.environ['MANNA_ENCRYPTION_KEY_AES256']

def performance_test_concurrent_encryption():
    """Test concurrent encryption performance."""
    print("\n=== Concurrent Encryption Performance Test ===")

    # Set up encryption
    aes256_key = AESGCM.generate_key(bit_length=256)
    aes256_key_b64 = base64.urlsafe_b64encode(aes256_key).decode()
    os.environ['MANNA_ENCRYPTION_KEY_AES256'] = aes256_key_b64

    def encrypt_decrypt_task(task_id):
        """Single encryption/decryption task."""
        provider = AES256GCMProvider()
        plaintext = f"plaid_access_token_{task_id}_{'x' * 50}"

        start_time = time.perf_counter()
        encrypted = provider.encrypt(plaintext)
        decrypted = provider.decrypt(encrypted)
        end_time = time.perf_counter()

        assert decrypted == plaintext
        return (end_time - start_time) * 1000  # ms

    # Test with different thread counts
    for thread_count in [1, 5, 10, 20]:
        times = []

        start_time = time.perf_counter()
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(encrypt_decrypt_task, i) for i in range(100)]
            times = [future.result() for future in futures]
        total_time = time.perf_counter() - start_time

        print(f"  {thread_count:2d} threads: avg={statistics.mean(times):.2f}ms/op, "
              f"total={total_time:.2f}s, throughput={100/total_time:.1f} ops/sec")

    # Cleanup
    del os.environ['MANNA_ENCRYPTION_KEY_AES256']

def performance_test_sqlalchemy_type():
    """Test SQLAlchemy type decorator performance."""
    print("\n=== SQLAlchemy Type Decorator Performance Test ===")

    # Set up encryption
    aes256_key = AESGCM.generate_key(bit_length=256)
    aes256_key_b64 = base64.urlsafe_b64encode(aes256_key).decode()
    os.environ['MANNA_ENCRYPTION_KEY_AES256'] = aes256_key_b64

    encrypted_type = EncryptedStringAES256(length=255)

    # Mock dialect
    class MockDialect:
        pass

    dialect = MockDialect()
    plaintext = "plaid_access_token_12345"

    # Test bind performance (encryption)
    bind_times = []
    for _ in range(1000):
        start = time.perf_counter()
        encrypted = encrypted_type.process_bind_param(plaintext, dialect)
        bind_times.append((time.perf_counter() - start) * 1000)

    # Test result performance (decryption)
    result_times = []
    for _ in range(1000):
        start = time.perf_counter()
        decrypted = encrypted_type.process_result_value(encrypted, dialect)
        result_times.append((time.perf_counter() - start) * 1000)
        assert decrypted == plaintext

    print(f"  Bind (encrypt): avg={statistics.mean(bind_times):.2f}ms, "
          f"p95={sorted(bind_times)[int(0.95 * len(bind_times))]:.2f}ms")
    print(f"  Result (decrypt): avg={statistics.mean(result_times):.2f}ms, "
          f"p95={sorted(result_times)[int(0.95 * len(result_times))]:.2f}ms")

    # Cleanup
    del os.environ['MANNA_ENCRYPTION_KEY_AES256']

def performance_comparison_fernet():
    """Compare AES-256-GCM vs Fernet performance."""
    print("\n=== Performance Comparison: AES-256-GCM vs Fernet ===")

    # Set up both encryption methods
    from cryptography.fernet import Fernet

    # AES-256-GCM setup
    aes256_key = AESGCM.generate_key(bit_length=256)
    aes256_key_b64 = base64.urlsafe_b64encode(aes256_key).decode()
    os.environ['MANNA_ENCRYPTION_KEY_AES256'] = aes256_key_b64
    aes_provider = AES256GCMProvider()

    # Fernet setup
    fernet_key = Fernet.generate_key()
    fernet = Fernet(fernet_key)

    plaintext = "plaid_access_token_12345_" + "x" * 50

    # Test AES-256-GCM
    aes_encrypt_times = []
    aes_decrypt_times = []

    for _ in range(1000):
        start = time.perf_counter()
        aes_encrypted = aes_provider.encrypt(plaintext)
        aes_encrypt_times.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        aes_decrypted = aes_provider.decrypt(aes_encrypted)
        aes_decrypt_times.append((time.perf_counter() - start) * 1000)
        assert aes_decrypted == plaintext

    # Test Fernet
    fernet_encrypt_times = []
    fernet_decrypt_times = []

    for _ in range(1000):
        start = time.perf_counter()
        fernet_encrypted = fernet.encrypt(plaintext.encode())
        fernet_encrypt_times.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        fernet_decrypted = fernet.decrypt(fernet_encrypted).decode()
        fernet_decrypt_times.append((time.perf_counter() - start) * 1000)
        assert fernet_decrypted == plaintext

    print(f"  AES-256-GCM encrypt: avg={statistics.mean(aes_encrypt_times):.2f}ms")
    print(f"  Fernet encrypt:      avg={statistics.mean(fernet_encrypt_times):.2f}ms")
    print(f"  AES-256-GCM decrypt: avg={statistics.mean(aes_decrypt_times):.2f}ms")
    print(f"  Fernet decrypt:      avg={statistics.mean(fernet_decrypt_times):.2f}ms")

    aes_total = statistics.mean(aes_encrypt_times) + statistics.mean(aes_decrypt_times)
    fernet_total = statistics.mean(fernet_encrypt_times) + statistics.mean(fernet_decrypt_times)

    print(f"\n  Total time (encrypt + decrypt):")
    print(f"  AES-256-GCM: {aes_total:.2f}ms")
    print(f"  Fernet:      {fernet_total:.2f}ms")
    print(f"  Performance ratio: {fernet_total/aes_total:.2f}x (Fernet/AES)")

    # Cleanup
    del os.environ['MANNA_ENCRYPTION_KEY_AES256']

def test_memory_usage():
    """Test memory usage of encryption operations."""
    print("\n=== Memory Usage Test ===")

    import psutil
    import gc

    process = psutil.Process()

    # Set up encryption
    aes256_key = AESGCM.generate_key(bit_length=256)
    aes256_key_b64 = base64.urlsafe_b64encode(aes256_key).decode()
    os.environ['MANNA_ENCRYPTION_KEY_AES256'] = aes256_key_b64

    provider = AES256GCMProvider()

    # Measure baseline memory
    gc.collect()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Generate and encrypt many tokens
    encrypted_tokens = []
    for i in range(10000):
        plaintext = f"plaid_access_token_{i}_{'x' * 50}"
        encrypted = provider.encrypt(plaintext)
        encrypted_tokens.append(encrypted)

        if i % 1000 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"  After {i:5d} encryptions: {current_memory:.1f} MB "
                  f"(+{current_memory - initial_memory:.1f} MB)")

    # Decrypt all tokens
    decrypted_tokens = []
    for i, encrypted in enumerate(encrypted_tokens):
        decrypted = provider.decrypt(encrypted)
        decrypted_tokens.append(decrypted)

        if i % 1000 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"  After {i:5d} decryptions: {current_memory:.1f} MB "
                  f"(+{current_memory - initial_memory:.1f} MB)")

    # Final memory check
    final_memory = process.memory_info().rss / 1024 / 1024
    print(f"\n  Final memory usage: {final_memory:.1f} MB "
          f"(+{final_memory - initial_memory:.1f} MB)")

    # Clean up and check memory after GC
    del encrypted_tokens, decrypted_tokens
    gc.collect()
    gc_memory = process.memory_info().rss / 1024 / 1024
    print(f"  After cleanup:      {gc_memory:.1f} MB "
          f"(+{gc_memory - initial_memory:.1f} MB)")

    # Cleanup
    del os.environ['MANNA_ENCRYPTION_KEY_AES256']

if __name__ == "__main__":
    print("Starting Core Performance Tests...")

    performance_test_encryption()
    performance_test_concurrent_encryption()
    performance_test_sqlalchemy_type()
    performance_comparison_fernet()
    test_memory_usage()

    print("\n✓ All performance tests completed!")