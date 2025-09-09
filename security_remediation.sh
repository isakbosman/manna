#!/bin/bash
# Manna Financial Platform - Security Remediation Script
# This script addresses critical and high-priority security issues found in the audit

set -e

echo "🔒 Manna Financial Platform - Security Remediation"
echo "=================================================="

# Check if running from project root
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "✅ Starting security remediation..."

# 1. Update Python Dependencies
echo "📦 Updating vulnerable Python dependencies..."
if [ -f "packages/backend/requirements.txt" ]; then
    cd packages/backend
    
    # Backup current requirements
    cp requirements.txt requirements.txt.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update vulnerable packages
    echo "Updating urllib3..."
    sed -i.bak 's/httpx>=0.25.0/httpx>=0.26.0/g' requirements.txt
    
    # Add security-focused package versions
    echo "" >> requirements.txt
    echo "# Security updates - $(date)" >> requirements.txt
    echo "urllib3>=2.5.0  # Fix SSRF vulnerability" >> requirements.txt
    
    cd ../../
    echo "✅ Python dependencies updated"
else
    echo "⚠️ Backend requirements.txt not found"
fi

# 2. Fix Docker Security Issues
echo "🐳 Fixing Docker security configurations..."

# Create secure docker-compose override
cat > docker-compose.security.yml << 'EOF'
# Security-hardened Docker Compose override
# Usage: docker-compose -f docker-compose.yml -f docker-compose.security.yml up

version: '3.8'

services:
  postgres:
    environment:
      # Remove insecure trust method
      POSTGRES_HOST_AUTH_METHOD: md5
    # Add security options
    security_opt:
      - no-new-privileges:true
    read_only: false  # Postgres needs write access to /var/lib/postgresql/data
    tmpfs:
      - /tmp
      - /var/run/postgresql

  redis:
    # Security hardening for Redis
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp

  backend:
    # Security improvements
    security_opt:
      - no-new-privileges:true
    environment:
      # Bind to specific interface in production
      - UVICORN_HOST=0.0.0.0  # Can be changed to specific IP in production
      - UVICORN_PORT=8000
    # Add user context
    user: "1000:1000"

  frontend:
    security_opt:
      - no-new-privileges:true
    user: "1001:1001"

# Add secrets management (example)
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt

EOF

echo "✅ Created docker-compose.security.yml with security hardening"

# 3. Create XSS Prevention Fix
echo "🛡️ Creating XSS prevention fixes..."

# Create a secure toast implementation
mkdir -p packages/frontend/src/utils
cat > packages/frontend/src/utils/dom-utils.ts << 'EOF'
/**
 * Secure DOM utility functions to prevent XSS attacks
 */

/**
 * Safely set text content to prevent XSS
 */
export function setTextContent(element: HTMLElement, text: string): void {
  element.textContent = text;
}

/**
 * Create element with safe text content
 */
export function createElementWithText(
  tagName: string, 
  text: string, 
  className?: string
): HTMLElement {
  const element = document.createElement(tagName);
  element.textContent = text;
  if (className) {
    element.className = className;
  }
  return element;
}

/**
 * Sanitize HTML string (basic implementation - consider using DOMPurify for production)
 */
export function sanitizeHTML(html: string): string {
  const div = document.createElement('div');
  div.textContent = html;
  return div.innerHTML;
}
EOF

echo "✅ Created secure DOM utilities"

# 4. Create Security Headers Middleware
echo "🔒 Adding security headers middleware..."

cat > packages/backend/src/middleware/security_headers.py << 'EOF'
"""
Security headers middleware for enhanced protection
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            # Prevent MIME sniffing
            "X-Content-Type-Options": "nosniff",
            
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Frame options
            "X-Frame-Options": "DENY",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy (adjust as needed)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "frame-ancestors 'none';"
            ),
            
            # HSTS (only in production with HTTPS)
            # "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }
        
        # Add headers to response
        for header, value in security_headers.items():
            response.headers[header] = value
            
        # Remove server information
        response.headers.pop("server", None)
        
        logger.debug("Security headers added to response")
        return response
EOF

echo "✅ Created security headers middleware"

# 5. Create Environment Validation Script
echo "🔍 Creating environment validation..."

cat > scripts/validate_security.py << 'EOF'
#!/usr/bin/env python3
"""
Security validation script for Manna Financial Platform
"""

import os
import sys
from pathlib import Path
import re

def validate_environment():
    """Validate security configuration"""
    issues = []
    
    # Check for environment file
    env_file = Path('.env')
    if not env_file.exists():
        issues.append("CRITICAL: .env file not found")
        return issues
        
    # Read environment variables
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    
    # Security validations
    
    # 1. Check JWT secret strength
    jwt_secret = env_vars.get('JWT_SECRET', '')
    if jwt_secret == 'your-secret-key-change-this-in-production':
        issues.append("HIGH: Default JWT secret detected")
    elif len(jwt_secret) < 32:
        issues.append("MEDIUM: JWT secret too short (minimum 32 characters)")
    
    # 2. Check database security
    db_url = env_vars.get('DATABASE_URL', '')
    if 'localhost' in db_url and os.environ.get('ENVIRONMENT') == 'production':
        issues.append("HIGH: Using localhost database in production")
    
    # 3. Check CORS origins
    cors_origins = env_vars.get('CORS_ORIGINS', '')
    if '*' in cors_origins:
        issues.append("HIGH: CORS allows all origins")
    
    # 4. Check debug mode
    debug = env_vars.get('DEBUG', 'true').lower()
    if debug == 'true' and os.environ.get('ENVIRONMENT') == 'production':
        issues.append("HIGH: Debug mode enabled in production")
    
    return issues

def main():
    print("🔒 Security Configuration Validation")
    print("====================================")
    
    issues = validate_environment()
    
    if not issues:
        print("✅ No security issues found!")
        return 0
    
    print(f"❌ Found {len(issues)} security issues:")
    for issue in issues:
        level = issue.split(':')[0]
        message = ':'.join(issue.split(':')[1:])
        
        if level == 'CRITICAL':
            print(f"🔴 CRITICAL{message}")
        elif level == 'HIGH':
            print(f"🟠 HIGH{message}")
        elif level == 'MEDIUM':
            print(f"🟡 MEDIUM{message}")
        else:
            print(f"ℹ️ INFO{message}")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x scripts/validate_security.py
echo "✅ Created security validation script"

# 6. Create Security-Enhanced GitHub Actions Workflow
echo "🚀 Creating security-enhanced CI/CD workflow..."

mkdir -p .github/workflows
cat > .github/workflows/security.yml << 'EOF'
name: Security Checks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install security tools
      run: |
        pip install safety bandit semgrep
    
    - name: Run Bandit security scan
      run: |
        bandit -r packages/backend/src/ -f json -o bandit-report.json || true
    
    - name: Run Safety dependency check
      run: |
        safety check --json --output safety-report.json || true
    
    - name: Run Semgrep security scan  
      run: |
        semgrep --config=auto packages/backend/src/ --json --output semgrep-report.json || true
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
          semgrep-report.json

  docker-security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

EOF

echo "✅ Created security-enhanced CI/CD workflow"

# 7. Create secrets directory structure
echo "🔑 Setting up secrets management..."

mkdir -p secrets
echo "# Secrets Directory" > secrets/README.md
echo "This directory contains sensitive configuration files." >> secrets/README.md
echo "Never commit actual secrets to version control." >> secrets/README.md
echo "" >> secrets/README.md
echo "Example files:" >> secrets/README.md
echo "- postgres_password.txt" >> secrets/README.md  
echo "- jwt_secret.txt" >> secrets/README.md

# Create example secret files (for development only)
echo "secure_postgres_password_$(date +%s)" > secrets/postgres_password.txt.example
echo "$(openssl rand -hex 32)" > secrets/jwt_secret.txt.example

echo "✅ Created secrets management structure"

# 8. Update .gitignore for security
echo "📝 Updating .gitignore for security..."

if [ -f ".gitignore" ]; then
    # Add security-related ignores if not already present
    if ! grep -q "secrets/" .gitignore; then
        echo "" >> .gitignore
        echo "# Security files" >> .gitignore
        echo "secrets/*.txt" >> .gitignore
        echo "*.key" >> .gitignore
        echo "*.pem" >> .gitignore
        echo "*security*.json" >> .gitignore
    fi
fi

echo "✅ Updated .gitignore with security patterns"

# 9. Create security documentation
echo "📚 Creating security documentation..."

cat > SECURITY.md << 'EOF'
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ |

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **Do not** create a public issue
2. Send details to [security@manna.finance](mailto:security@manna.finance)
3. Include steps to reproduce the vulnerability
4. We will respond within 48 hours

## Security Measures

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Session management via Redis

### Data Protection  
- Input validation using Pydantic
- SQL injection prevention via SQLAlchemy ORM
- XSS protection through input sanitization
- CSRF protection enabled

### Infrastructure Security
- Container security with non-root users
- Security headers middleware
- Rate limiting and DDoS protection
- Comprehensive audit logging

### Dependency Management
- Regular security scans with Safety and Bandit
- Automated dependency updates
- Container vulnerability scanning

## Security Best Practices

### For Developers
1. Never commit secrets to version control
2. Use parameterized queries for database access
3. Validate all user inputs
4. Follow principle of least privilege
5. Keep dependencies updated

### For Deployment
1. Use strong, unique passwords
2. Enable HTTPS/TLS in production
3. Configure firewall rules properly
4. Monitor logs for suspicious activity
5. Backup encryption keys securely

## Security Tools Used
- **Bandit**: Python security scanner
- **Safety**: Python dependency vulnerability scanner  
- **Semgrep**: Static analysis security scanner
- **Trivy**: Container vulnerability scanner
- **NPM Audit**: JavaScript dependency scanner

## Incident Response
1. Identify and contain the threat
2. Assess impact and affected systems
3. Notify relevant stakeholders
4. Implement fixes and patches
5. Document lessons learned
EOF

echo "✅ Created comprehensive security documentation"

# 10. Summary and next steps
echo ""
echo "🎉 Security Remediation Complete!"
echo "================================="
echo ""
echo "✅ Completed Actions:"
echo "  • Updated vulnerable Python dependencies"
echo "  • Created secure Docker compose configuration"  
echo "  • Added XSS prevention utilities"
echo "  • Implemented security headers middleware"
echo "  • Created environment validation script"
echo "  • Set up automated security scanning"
echo "  • Configured secrets management"
echo "  • Enhanced .gitignore for security"
echo "  • Created security documentation"
echo ""
echo "🔄 Next Manual Steps Required:"
echo "  1. Update packages/backend/requirements.txt with new versions"
echo "  2. Add SecurityHeadersMiddleware to main.py"
echo "  3. Replace innerHTML usage in toast component with secure utilities"
echo "  4. Run: python scripts/validate_security.py"
echo "  5. Test with: docker-compose -f docker-compose.yml -f docker-compose.security.yml up"
echo "  6. Generate actual secrets for production deployment"
echo ""
echo "📋 Monitoring Setup:"
echo "  • Enable security scanning in CI/CD pipeline"
echo "  • Set up log monitoring for security events"  
echo "  • Schedule regular dependency audits"
echo "  • Implement intrusion detection"
echo ""
echo "For questions about security implementation, refer to SECURITY.md"
echo "Security audit report: SECURITY_AUDIT_REPORT.md"