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
