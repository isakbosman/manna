# AES-256-GCM Encryption and Optimistic Locking Implementation

## Overview

This document describes the implementation of AES-256-GCM encryption and optimistic locking fixes for the Manna backend. This replaces the previous Fernet-based encryption and fixes SQLAlchemy 2.x compatibility issues.

## Features Implemented

### 1. AES-256-GCM Encryption (`src/core/encryption.py`)

**Key Features:**
- NIST-approved AES-256-GCM authenticated encryption
- 96-bit nonces for security (NIST recommended)
- Additional Authenticated Data (AAD) support
- Backward compatibility with Fernet encryption
- Migration path from Fernet to AES-256-GCM
- Key rotation support
- Version prefixes for format identification

**Security Improvements:**
- Stronger encryption algorithm (AES-256 vs AES-128)
- Authenticated encryption prevents tampering
- Constant-time operations prevent timing attacks
- Replay protection with timestamps in AAD

### 2. Fixed Optimistic Locking (`src/core/locking.py`)

**Key Features:**
- SQLAlchemy 2.x compatible event handlers
- Automatic version increment on modifications
- Optimistic lock failure detection and handling
- Retry mechanism with exponential backoff
- Distributed locking with Redis
- Lock auto-extension for long operations

**Fixes Applied:**
- Corrected SQLAlchemy event listener syntax
- Proper version column management
- Better error handling for concurrent modifications
- Thread-safe lock token generation

### 3. Migration Support

**Migration Scripts:**
- `20250918_0600_upgrade_to_aes256_gcm.py` - Migrates Fernet to AES-256-GCM
- Backward compatibility during transition
- Zero-downtime migration strategy
- Audit logging for all encryption changes

## Files Modified/Created

### Core Implementation
- `src/core/encryption.py` - Replaced with AES-256-GCM implementation
- `src/core/locking.py` - Fixed SQLAlchemy 2.x compatibility
- `src/config.py` - Added AES-256 key configuration

### Migration Scripts
- `migrations/versions/20250918_0600_upgrade_to_aes256_gcm.py` - New migration

### Test Files
- `test_core_only.py` - Core implementation tests
- `simple_encryption_test.py` - Basic functionality tests
- `test_implementation_only.py` - Comprehensive tests

## Environment Variables

### Required for Production
```bash
# AES-256 encryption key (32 bytes, base64 encoded)
MANNA_ENCRYPTION_KEY_AES256=<base64-encoded-32-byte-key>

# Redis URL for distributed locking
REDIS_URL=redis://localhost:6379/0
```

### Optional (for migration compatibility)
```bash
# Legacy Fernet key (for migration only)
MANNA_ENCRYPTION_KEY=<base64-encoded-fernet-key>
```

## Key Generation

Generate a production AES-256 key:

```python
from src.core.encryption import generate_aes256_key
key = generate_aes256_key()
print(f"MANNA_ENCRYPTION_KEY_AES256={key}")
```

## Usage Examples

### Encrypting Data
```python
from src.core.encryption import encrypt_string, decrypt_string

# Basic encryption
encrypted = encrypt_string("sensitive-data")
decrypted = decrypt_string(encrypted)

# With Additional Authenticated Data
aad = b"plaid_item_context"
encrypted = encrypt_string("access-token", aad=aad)
decrypted = decrypt_string(encrypted, aad=aad)
```

### Optimistic Locking
```python
from src.core.locking import OptimisticLockMixin
from sqlalchemy.orm import Session

class MyModel(Base, OptimisticLockMixin):
    # ... model definition

# Safe update with optimistic locking
try:
    item.update_with_lock(session, field="new_value")
    session.commit()
except OptimisticLockError:
    session.rollback()
    # Handle concurrent modification
```

### Distributed Locking
```python
from src.core.locking import get_distributed_lock

dist_lock = get_distributed_lock()

# Context manager (recommended)
with dist_lock.lock("resource_id", timeout=30.0):
    # Perform exclusive operation
    pass

# Manual locking
token = dist_lock.acquire_lock("resource_id")
try:
    # Perform operation
    pass
finally:
    dist_lock.release_lock("resource_id", token)
```

## Migration Instructions

### 1. Backup Database
```bash
pg_dump manna > backup_before_encryption_upgrade.sql
```

### 2. Run Migration
```bash
# Navigate to backend directory
cd packages/backend

# Activate environment
conda activate mana

# Run migration
alembic upgrade head
```

### 3. Verify Migration
```bash
# Test core implementations
python test_core_only.py

# Check encryption info
python -c "
from src.core.encryption import get_encryption_info
print(get_encryption_info())
"
```

## Testing Results

All core implementations tested and verified:

✓ **Encryption Core**: AES-256-GCM encryption/decryption working
✓ **Locking Core**: Optimistic locking mixin and distributed locking working
✓ **Migration Functionality**: Migration functions available and working
✓ **SQLAlchemy Type**: Encrypted field type decorator working

## Security Considerations

### Encryption
- Uses NIST-approved AES-256-GCM algorithm
- 96-bit nonces prevent replay attacks
- Version prefixes enable format detection
- AAD prevents ciphertext manipulation
- Constant-time operations prevent timing attacks

### Key Management
- Production requires explicit key configuration
- Development uses deterministic key derivation
- Supports key rotation without downtime
- Keys should be stored in secure key management system

### Optimistic Locking
- Prevents lost update anomalies
- Version columns detect concurrent modifications
- Retry mechanism handles temporary conflicts
- Distributed locks coordinate across processes

## Performance Considerations

### Encryption
- AES-256-GCM is hardware accelerated on modern CPUs
- Minimal overhead compared to Fernet
- Larger ciphertext due to nonce and authentication tag
- Database column sizes increased by 3x to accommodate overhead

### Locking
- Redis-based distributed locking for coordination
- Auto-extending locks for long operations
- Exponential backoff for retry attempts
- Lua scripts ensure atomic operations

## Troubleshooting

### Common Issues

1. **Encryption not initialized**
   - Set `MANNA_ENCRYPTION_KEY_AES256` environment variable
   - Verify key is base64-encoded 32-byte value

2. **Migration fails**
   - Check database connectivity
   - Verify backup before running
   - Check logs for specific error messages

3. **Optimistic lock failures**
   - Normal in high-concurrency scenarios
   - Implement retry logic in application code
   - Monitor frequency of conflicts

4. **Distributed lock timeouts**
   - Check Redis connectivity
   - Increase timeout values for long operations
   - Monitor Redis memory usage

### Verification Commands

```bash
# Test encryption
python -c "
from src.core.encryption import encrypt_string, decrypt_string
test = 'test-data-123'
enc = encrypt_string(test)
dec = decrypt_string(enc)
print(f'Success: {test == dec}')
"

# Test optimistic locking
python -c "
from src.core.locking import OptimisticLockMixin
class Test(OptimisticLockMixin):
    def __init__(self): self.version = 1
t = Test()
t.increment_version()
print(f'Version: {t.version}')
"
```

## Next Steps

1. **Production Deployment**
   - Generate and securely store AES-256 key
   - Set environment variables
   - Run migrations during maintenance window

2. **Monitoring**
   - Monitor encryption/decryption performance
   - Track optimistic lock conflict rates
   - Monitor Redis memory usage for distributed locks

3. **Security Audit**
   - Review key storage and rotation procedures
   - Test failover scenarios
   - Validate audit logging

## Support

For issues or questions:
1. Check this documentation
2. Review test files for examples
3. Check application logs for specific errors
4. Verify environment configuration