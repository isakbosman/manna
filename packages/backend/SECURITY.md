# Security Implementation Guide

This document describes the comprehensive security fixes implemented for the Manna Financial Platform backend.

## Overview

The security implementation addresses four critical vulnerabilities:

1. **Access tokens stored in plaintext** - Fixed with AES-256-GCM field-level encryption
2. **Weak/missing database passwords** - Fixed with centralized secrets management
3. **Default secret keys** - Fixed with secure key generation and rotation
4. **Race conditions in cursor updates** - Fixed with optimistic locking and distributed locks

## 🔐 Security Components

### 1. Field-Level Encryption (`src/core/encryption.py`)

**Purpose**: Encrypt sensitive data like Plaid access tokens at the database field level.

**Features**:
- AES-256-GCM encryption with authenticated encryption
- Transparent encryption/decryption via SQLAlchemy custom types
- Environment-based key management
- Automatic key generation for development

**Usage**:
```python
from core.encryption import EncryptedString

class PlaidItem(Base):
    plaid_access_token = Column(EncryptedString(255), nullable=False)
```

**Key Management**:
- Production: Set `MANNA_ENCRYPTION_KEY` environment variable
- Development: Automatically derived from application secret
- Key rotation: Generate new key with `EncryptionKeyProvider.generate_key()`

### 2. Secrets Management (`src/core/secrets.py`)

**Purpose**: Centralized management of application secrets with multiple provider support.

**Providers**:
- Environment variables (production)
- Local file storage (development)
- Future: AWS Secrets Manager, HashiCorp Vault

**Critical Secrets**:
- `database_password`: Database authentication
- `jwt_signing_key`: JWT token signing
- `encryption_key`: Field-level encryption
- `plaid_secret`: Plaid API authentication

**Usage**:
```python
from core.secrets import get_secret, secrets_manager

# Get individual secret
db_password = get_secret("database_password", required=True)

# Get secure database URL
secure_url = secrets_manager.get_database_url()
```

### 3. Secure Database Connections (`src/core/database.py`)

**Purpose**: Secure database connections with proper authentication and monitoring.

**Features**:
- Automatic SSL configuration for production
- Connection pooling with security settings
- Health monitoring and connection validation
- Automatic password injection from secrets
- Connection timeout and retry logic

**Security Settings**:
- Statement timeout: 30 seconds
- SSL mode: Required in production
- Connection validation before use
- Automatic cleanup and monitoring

### 4. Optimistic Locking (`src/core/locking.py`)

**Purpose**: Prevent race conditions in critical operations like Plaid cursor updates.

**Components**:
- `OptimisticLockMixin`: Adds version-based locking to models
- `DistributedLock`: Redis-based distributed locking
- `safe_cursor_update()`: Atomic cursor updates with locking

**Usage**:
```python
from core.locking import OptimisticLockMixin, safe_cursor_update

class PlaidItem(Base, OptimisticLockMixin):
    # Automatically adds version column
    pass

# Safe cursor update
success = safe_cursor_update(session, plaid_item, new_cursor)
```

### 5. Audit Logging (`src/core/audit.py`)

**Purpose**: Comprehensive security event logging for compliance and monitoring.

**Event Types**:
- Authentication (login, logout, failures)
- Authorization (access granted/denied)
- Data access (CRUD operations)
- Security events (key rotation, config changes)
- Plaid operations (connect, sync, errors)

**Usage**:
```python
from core.audit import log_audit_event, AuditEventType

log_audit_event(
    AuditEventType.LOGIN_SUCCESS,
    f"User {user_id} logged in successfully",
    context=audit_context
)
```

### 6. Security Middleware

**Enhanced Security Headers** (`src/middleware/security_headers.py`):
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options, X-Content-Type-Options
- Permissions Policy
- Environment-specific configurations

**Rate Limiting** (`src/middleware/rate_limit.py`):
- Configurable rate limits per endpoint
- Redis-based distributed rate limiting
- IP-based and user-based limiting

## 🚀 Deployment Guide

### Development Setup

1. **Install Dependencies**:
   ```bash
   pip install cryptography redis python-jose passlib
   ```

2. **Run Security Setup**:
   ```bash
   python packages/backend/scripts/setup_security.py --environment development
   ```

3. **Run Migration**:
   ```bash
   cd packages/backend
   alembic upgrade head
   ```

4. **Validate Setup**:
   ```bash
   python -m src.scripts.validate_security
   ```

### Production Setup

1. **Generate Production Keys**:
   ```bash
   python packages/backend/scripts/setup_security.py --environment production
   ```

2. **Set Environment Variables**:
   ```bash
   export MANNA_ENCRYPTION_KEY="<generated-key>"
   export DATABASE_PASSWORD="<secure-password>"
   export JWT_SIGNING_KEY="<jwt-key>"
   export PLAID_SECRET="<plaid-secret>"
   ```

3. **Configure Database SSL**:
   - Set up SSL certificates
   - Update DATABASE_URL with `sslmode=require`

4. **Run Migration**:
   ```bash
   alembic upgrade head
   ```

5. **Validate Security**:
   ```bash
   python -m src.scripts.validate_security
   ```

## 🔧 Configuration

### Environment Variables

**Required for Production**:
- `MANNA_ENCRYPTION_KEY`: Field encryption key
- `DATABASE_PASSWORD`: Database password
- `JWT_SIGNING_KEY`: JWT signing key
- `PLAID_SECRET`: Plaid API secret

**Security Flags**:
- `FIELD_ENCRYPTION_ENABLED=true`: Enable field encryption
- `SECURITY_HEADERS_ENABLED=true`: Enable security headers
- `RATE_LIMITING_ENABLED=true`: Enable rate limiting
- `AUDIT_LOGGING_ENABLED=true`: Enable audit logging
- `REQUIRE_HTTPS=true`: Require HTTPS (production)
- `SECURE_COOKIES=true`: Secure cookie settings

### Database Migration

The migration `20250918_0500_encrypt_access_tokens.py` handles:
- Adding version column to PlaidItem for optimistic locking
- Encrypting existing plaintext access tokens
- Audit logging of the migration process

**Manual Encryption Check**:
```sql
-- Check if tokens are encrypted (should show encrypted data)
SELECT id, length(plaid_access_token), left(plaid_access_token, 20)
FROM plaid_items
LIMIT 5;
```

## 🔍 Monitoring and Validation

### Security Validation Script

Run the validation script to check security posture:

```bash
python -m src.scripts.validate_security
```

**Checks Performed**:
- Encryption initialization and configuration
- Secrets availability and management
- Database security settings
- Middleware configuration
- Optimistic locking implementation
- Access token encryption
- Overall configuration security

### Health Check Endpoint

The `/health` endpoint now includes security status:

```json
{
  "status": "healthy",
  "security": {
    "encryption_enabled": true,
    "security_headers": true,
    "rate_limiting": true,
    "audit_logging": true
  }
}
```

### Audit Log Monitoring

Monitor audit logs for security events:
- Failed authentication attempts
- Access denied events
- Suspicious activity
- Configuration changes

## 🛡️ Security Best Practices

### Key Management
- Rotate encryption keys regularly
- Use environment variables for production secrets
- Never commit secrets to version control
- Use secure key generation methods

### Database Security
- Use SSL/TLS for database connections
- Implement least privilege access
- Regular password rotation
- Monitor connection patterns

### Application Security
- Enable all security middleware in production
- Use HTTPS for all external communications
- Implement proper session management
- Regular security validations

### Monitoring and Alerting
- Monitor audit logs for security events
- Set up alerts for failed authentications
- Track encryption key usage
- Monitor database connection security

## 🚨 Incident Response

### Suspected Data Breach
1. Check audit logs for unauthorized access
2. Rotate all encryption keys immediately
3. Reset database passwords
4. Review access patterns
5. Notify relevant stakeholders

### Performance Issues
1. Check database connection pool status
2. Monitor Redis performance for rate limiting
3. Review audit log volume
4. Check for distributed lock contention

### Configuration Issues
1. Run security validation script
2. Check environment variable settings
3. Verify database connectivity
4. Test encryption/decryption functionality

## 📝 Troubleshooting

### Encryption Issues
- **Error**: "Encryption not initialized"
  - **Solution**: Set `MANNA_ENCRYPTION_KEY` environment variable

- **Error**: "Failed to decrypt data"
  - **Solution**: Verify encryption key hasn't changed, check data integrity

### Database Connection Issues
- **Error**: "Database password required in production"
  - **Solution**: Set `DATABASE_PASSWORD` environment variable

- **Error**: "SSL connection required"
  - **Solution**: Add `sslmode=require` to DATABASE_URL

### Lock Contention
- **Error**: "Could not acquire sync lock"
  - **Solution**: Wait for current operation to complete, check Redis connectivity

### Migration Issues
- **Error**: "Migration failed to encrypt tokens"
  - **Solution**: Check encryption key availability, run manual encryption

For additional support, check the audit logs and run the security validation script for detailed diagnostics.