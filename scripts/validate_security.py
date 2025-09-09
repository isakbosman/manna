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
