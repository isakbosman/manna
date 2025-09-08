# Manna Financial Management Platform API Specification

## Overview

This directory contains the complete API specification for the Manna Financial Management Platform Phase 1.3. The platform serves as an agentic accounting firm system, providing comprehensive financial management capabilities through a RESTful API and real-time WebSocket connections.

## Architecture

- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL via SQLAlchemy ORM
- **Authentication**: JWT-based with preparation for Clerk integration
- **Real-time**: WebSocket connections for live updates
- **External Integrations**: Plaid API for bank connectivity
- **ML Components**: Transaction categorization and financial insights

## Documentation Structure

### Core Specifications

| File                             | Description                                                                   |
| -------------------------------- | ----------------------------------------------------------------------------- |
| [`openapi.yaml`](./openapi.yaml) | Complete OpenAPI 3.0 specification with all endpoints, schemas, and examples  |
| [`types.ts`](./types.ts)         | TypeScript type definitions for all API entities and request/response schemas |

### Implementation Guides

| File                                             | Description                                                       |
| ------------------------------------------------ | ----------------------------------------------------------------- |
| [`integration-guide.md`](./integration-guide.md) | Comprehensive integration patterns, SDK usage, and best practices |
| [`websocket-events.md`](./websocket-events.md)   | WebSocket event specifications and real-time update patterns      |
| [`error-standards.md`](./error-standards.md)     | Error response formats, codes, and handling strategies            |
| [`rate-limits.md`](./rate-limits.md)             | Rate limiting configuration, thresholds, and client handling      |

## API Endpoints Overview

### Authentication & User Management

- **POST** `/auth/register` - User registration
- **POST** `/auth/login` - User authentication
- **POST** `/auth/refresh` - Token refresh
- **POST** `/auth/logout` - User logout
- **POST** `/auth/reset-password` - Password reset

### Plaid Integration

- **POST** `/plaid/link-token` - Create Plaid Link token
- **POST** `/plaid/exchange-token` - Exchange public token
- **GET** `/plaid/accounts` - Retrieve connected accounts
- **POST** `/plaid/sync` - Trigger manual sync
- **POST** `/plaid/webhooks` - Plaid webhook handler

### Transaction Management

- **GET** `/transactions` - List transactions with filtering/pagination
- **GET** `/transactions/{id}` - Get specific transaction
- **PUT** `/transactions/{id}` - Update transaction
- **POST** `/transactions/bulk-update` - Bulk transaction updates
- **POST** `/transactions/export` - Export transactions (CSV/Excel/QBO)

### Financial Reporting

- **GET** `/reports/pnl` - Profit & Loss statements
- **GET** `/reports/balance-sheet` - Balance sheet reports
- **GET** `/reports/cash-flow` - Cash flow statements
- **GET** `/reports/kpis` - Key performance indicators
- **POST** `/reports/generate` - Custom report generation

### ML Categorization

- **POST** `/ml/categorize` - Categorize transactions
- **POST** `/ml/train` - Retrain categorization model
- **GET** `/ml/suggestions` - Get categorization suggestions
- **POST** `/ml/feedback` - Provide categorization feedback

### Account Management

- **GET** `/accounts` - List connected accounts
- **POST** `/accounts/connect` - Connect new account
- **DELETE** `/accounts/{id}` - Disconnect account
- **PUT** `/accounts/{id}/refresh` - Refresh account data

### WebSocket Events

- **GET** `/ws/updates` - Real-time event stream

## Key Features

### 🔐 Comprehensive Authentication

- JWT-based authentication with refresh tokens
- Password reset workflows
- Secure token management patterns

### 🏦 Plaid Integration

- Seamless bank account connectivity
- Automatic transaction synchronization
- Webhook handling for real-time updates
- Error handling for re-authentication scenarios

### 📊 Advanced Transaction Management

- Flexible filtering and search capabilities
- Bulk operations for efficiency
- Multiple export formats (CSV, Excel, QBO)
- ML-powered categorization

### 📈 Financial Reporting

- Standard financial statements (P&L, Balance Sheet, Cash Flow)
- KPI tracking and analysis
- Comparative reporting
- Custom report generation

### 🤖 Machine Learning Integration

- Automatic transaction categorization
- Confidence scoring
- Continuous learning from user feedback
- Suggestion engine for review workflows

### ⚡ Real-time Updates

- WebSocket connections for live data
- Event-driven architecture
- Progress tracking for long-running operations
- System status notifications

### 🛡️ Enterprise-Grade Features

- Comprehensive error handling
- Rate limiting with multiple tiers
- Request/response validation
- Audit trails and monitoring

## Rate Limiting

| Endpoint Category  | Limit          | Window |
| ------------------ | -------------- | ------ |
| Standard Endpoints | 1,000 requests | 1 hour |
| Plaid Integration  | 100 requests   | 1 hour |
| ML Categorization  | 500 requests   | 1 hour |
| Report Generation  | 50 requests    | 1 hour |
| Export Operations  | 20 requests    | 1 hour |

## WebSocket Events

### Transaction Events

- `transaction_added` - New transaction detected
- `transaction_updated` - Transaction modified
- `transactions_bulk_updated` - Bulk updates completed

### Categorization Events

- `categorization_started` - ML process initiated
- `categorization_progress` - Progress updates
- `categorization_complete` - Process finished
- `categorization_suggestion` - New suggestion available

### Sync Events

- `sync_started` - Account sync initiated
- `sync_progress` - Sync progress updates
- `sync_complete` - Sync finished
- `sync_error` - Sync encountered error

### Report Events

- `report_generation_started` - Report creation initiated
- `report_generation_progress` - Generation progress
- `report_ready` - Report available for download

## Error Handling

### Standard Error Format

```json
{
  "error": "Error Category",
  "message": "Human-readable description",
  "code": "MACHINE_READABLE_CODE",
  "details": { "additional": "context" },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_unique_id"
}
```

### Error Categories

- **Authentication Errors** (`AUTH_*`)
- **Authorization Errors** (`AUTHZ_*`)
- **Validation Errors** (`VALIDATION_*`)
- **Resource Errors** (`RESOURCE_*`)
- **Business Logic Errors** (`BUSINESS_*`)
- **External Service Errors** (`EXT_*`)
- **System Errors** (`SYSTEM_*`)
- **Rate Limiting Errors** (`RATE_*`)

## Integration Patterns

### Quick Start

```typescript
import { MannaApiClient } from '@manna/api-client';

const client = new MannaApiClient({
  baseURL: 'https://api.manna.financial/v1',
  accessToken: 'your_jwt_token',
});

// Get recent transactions
const transactions = await client.transactions.list({
  start_date: '2024-01-01',
  end_date: '2024-01-31',
});

// Connect to real-time updates
const ws = client.createWebSocketConnection();
ws.on('transaction_added', (data) => {
  console.log('New transaction:', data.transaction);
});
```

### Common Workflows

#### 1. Account Connection

1. Create Plaid Link token
2. User completes Plaid Link flow
3. Exchange public token for access token
4. Monitor sync progress via WebSocket
5. Handle sync completion

#### 2. Transaction Processing

1. Retrieve new/uncategorized transactions
2. Apply ML categorization
3. Apply business rules
4. Generate reports if needed
5. Update dashboard in real-time

#### 3. Report Generation

1. Request report with parameters
2. Monitor generation progress
3. Download completed report
4. Cache for future access

## Security Considerations

### Authentication

- JWT tokens with expiration
- Refresh token rotation
- Secure token storage recommendations

### Authorization

- Role-based access control
- Resource-level permissions
- Account isolation

### Data Protection

- TLS encryption for all communications
- Sensitive data exclusion from logs
- GDPR/CCPA compliance support

### Rate Limiting

- Per-user request limits
- Endpoint-specific restrictions
- Graceful degradation patterns

## Development Environment

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis (for rate limiting and caching)
- Node.js 18+ (for TypeScript support)

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/manna

# JWT Configuration
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN=3600

# Plaid Configuration
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENVIRONMENT=sandbox

# Redis
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_STANDARD_REQUESTS=1000
RATE_LIMIT_STANDARD_WINDOW=3600
```

## Testing

### API Testing

- Unit tests for all endpoint handlers
- Integration tests with test database
- Mock external service dependencies
- Rate limiting validation

### Load Testing

- Concurrent user simulation
- Rate limit boundary testing
- WebSocket connection limits
- Database performance under load

## Monitoring & Observability

### Metrics

- Request/response times
- Error rates by endpoint
- Rate limit hit rates
- WebSocket connection health
- External service latency

### Logging

- Structured JSON logs
- Request/response correlation
- User activity tracking
- System performance metrics

### Alerting

- High error rates
- External service failures
- Rate limit violations
- System resource exhaustion

## Deployment Considerations

### Scaling

- Horizontal API server scaling
- Database connection pooling
- Redis cluster for rate limiting
- WebSocket server distribution

### High Availability

- Multi-region deployment
- Database replication
- Circuit breaker patterns
- Graceful degradation

### Performance

- Response caching strategies
- Database query optimization
- CDN for static assets
- Async processing for reports

## Support & Resources

### Documentation

- [OpenAPI Specification](./openapi.yaml) - Interactive API documentation
- [Integration Guide](./integration-guide.md) - Implementation patterns
- [WebSocket Events](./websocket-events.md) - Real-time update specifications

### Development Tools

- Postman collection (generated from OpenAPI spec)
- TypeScript SDK with full type safety
- Mock server for testing
- API client examples

### Contact Information

- **API Support**: api-support@manna.financial
- **Documentation Issues**: docs@manna.financial
- **Integration Help**: integrations@manna.financial

---

## Version History

### v1.3.0 (Current)

- Complete OpenAPI specification
- TypeScript type definitions
- WebSocket event specifications
- Comprehensive error handling
- Rate limiting implementation
- Integration guide and examples

### Future Roadmap

- GraphQL endpoint support
- Enhanced ML categorization
- Multi-tenant architecture
- Advanced reporting capabilities
- Mobile SDK development

---

_This API specification is designed to provide a comprehensive, production-ready financial management platform. For questions or support, please refer to the contact information above._
