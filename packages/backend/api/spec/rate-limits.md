# Rate Limiting Configuration

## Overview

The Manna Financial Management Platform API implements rate limiting to ensure fair usage and system stability. Rate limits are applied per user and vary by endpoint category.

## Rate Limit Tiers

### Standard Endpoints

- **Limit**: 1,000 requests per hour
- **Window**: Rolling 1-hour window
- **Endpoints**: Most read operations, user management, account information

### Plaid Integration Endpoints

- **Limit**: 100 requests per hour
- **Window**: Rolling 1-hour window
- **Endpoints**: Plaid sync, account connection, webhook processing
- **Reasoning**: Plaid API has its own rate limits; this prevents cascading failures

### ML Categorization Endpoints

- **Limit**: 500 requests per hour
- **Window**: Rolling 1-hour window
- **Endpoints**: Batch categorization, training requests, suggestions
- **Reasoning**: ML operations are computationally expensive

### Report Generation

- **Limit**: 50 requests per hour
- **Window**: Rolling 1-hour window
- **Endpoints**: Report generation, complex analytics
- **Reasoning**: Report generation is resource-intensive

### Export Operations

- **Limit**: 20 requests per hour
- **Window**: Rolling 1-hour window
- **Endpoints**: CSV, Excel, QBO exports
- **Reasoning**: File generation and storage considerations

## Headers

All API responses include rate limit information in headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

## Rate Limit Response

When rate limit is exceeded, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 3600
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640998800

{
  "error": "Rate limit exceeded",
  "message": "You have exceeded the rate limit for this endpoint. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 1000,
    "window": 3600,
    "reset_time": "2024-01-01T13:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_12345"
}
```

## Implementation Details

### Algorithm

- **Token Bucket**: Used for burst handling with sustained rate limiting
- **Sliding Window**: 1-hour rolling windows for accurate rate limiting
- **Distributed**: Rate limits maintained in Redis for multi-instance deployments

### Storage

- **Redis Keys**: `rate_limit:{user_id}:{endpoint_category}`
- **Expiration**: Keys expire after the rate limit window
- **Atomic Operations**: Redis pipeline for thread-safe operations

### Bypass Conditions

- **Admin Users**: No rate limits (configurable)
- **System Health Checks**: Excluded from rate limiting
- **Webhooks**: Separate rate limiting (by IP/source)

## Configuration

Rate limits are configurable via environment variables:

```env
# Standard endpoints
RATE_LIMIT_STANDARD_REQUESTS=1000
RATE_LIMIT_STANDARD_WINDOW=3600

# Plaid endpoints
RATE_LIMIT_PLAID_REQUESTS=100
RATE_LIMIT_PLAID_WINDOW=3600

# ML endpoints
RATE_LIMIT_ML_REQUESTS=500
RATE_LIMIT_ML_WINDOW=3600

# Report generation
RATE_LIMIT_REPORTS_REQUESTS=50
RATE_LIMIT_REPORTS_WINDOW=3600

# Export operations
RATE_LIMIT_EXPORT_REQUESTS=20
RATE_LIMIT_EXPORT_WINDOW=3600

# Redis configuration for rate limiting
REDIS_RATE_LIMIT_URL=redis://localhost:6379/1
```

## Monitoring

### Metrics Tracked

- Rate limit hits per endpoint
- Top rate-limited users
- Average request rates
- Burst patterns

### Alerts

- High rate limit hit rates
- Potential abuse patterns
- System performance degradation due to rate limiting

## Best Practices for Clients

### Respect Headers

Always check rate limit headers and adjust request patterns accordingly.

### Exponential Backoff

Implement exponential backoff when receiving 429 responses:

```typescript
async function makeRequestWithBackoff(
  request: () => Promise<Response>,
  maxRetries = 3
) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await request();

    if (response.status !== 429) {
      return response;
    }

    const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
    const backoffDelay = Math.min(
      retryAfter * 1000,
      Math.pow(2, attempt) * 1000
    );

    if (attempt < maxRetries) {
      await new Promise((resolve) => setTimeout(resolve, backoffDelay));
    }
  }

  throw new Error('Max retries exceeded');
}
```

### Batch Operations

Use batch endpoints when available to reduce the number of API calls:

```typescript
// Instead of multiple individual updates
transactions.forEach(async (txn) => {
  await updateTransaction(txn.id, txn.updates);
});

// Use bulk update
await bulkUpdateTransactions({
  transaction_ids: transactions.map((t) => t.id),
  updates: commonUpdates,
});
```

### Caching

Implement client-side caching for frequently accessed, slowly changing data:

```typescript
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

async function getCachedAccounts() {
  const cacheKey = 'accounts';
  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  const accounts = await fetchAccounts();
  cache.set(cacheKey, { data: accounts, timestamp: Date.now() });
  return accounts;
}
```

## WebSocket Alternative

For real-time updates that would otherwise require frequent polling, use the WebSocket connection:

```typescript
// Instead of polling for new transactions
setInterval(async () => {
  const transactions = await getTransactions({ since: lastCheck });
  // Process new transactions
}, 30000);

// Use WebSocket for real-time updates
const ws = new WebSocket(
  'wss://api.manna.financial/ws/updates?token=jwt_token'
);
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'transaction_added') {
    // Handle new transaction
  }
};
```

## Enterprise Rate Limits

Enterprise customers may have higher rate limits. Contact support for custom rate limit configurations.

### Custom Tiers

- **Startup**: 2x standard limits
- **Growth**: 5x standard limits
- **Enterprise**: 10x standard limits + dedicated infrastructure
- **Custom**: Negotiated limits based on usage patterns

## Troubleshooting

### Common Issues

1. **Sudden Rate Limit Hits**
   - Check for infinite loops in client code
   - Verify correct use of pagination
   - Look for inefficient polling patterns

2. **Inconsistent Rate Limiting**
   - Ensure clock synchronization
   - Check for multiple client instances sharing credentials
   - Verify Redis connectivity

3. **False Positives**
   - Review rate limit configuration
   - Check for proxy/load balancer IP masking
   - Verify user identification logic

### Debug Headers

In development mode, additional debug headers are available:

```
X-RateLimit-Debug-Key: rate_limit:user_123:standard
X-RateLimit-Debug-Tokens: 995
X-RateLimit-Debug-Window-Start: 1640991600
```
