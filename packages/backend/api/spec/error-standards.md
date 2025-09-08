# Error Response Standards

## Overview

The Manna Financial Management Platform API uses consistent error response formats across all endpoints. This document defines the error structure, status codes, error codes, and handling patterns.

## Error Response Format

All error responses follow this JSON structure:

```typescript
interface ApiError {
  error: string; // Short error description
  message: string; // Human-readable error message
  code: string; // Machine-readable error code
  details?: object; // Additional error context
  timestamp: string; // ISO 8601 timestamp
  request_id: string; // Unique request identifier
  path?: string; // API endpoint path
  method?: string; // HTTP method
}
```

### Example Error Response

```json
{
  "error": "Validation Error",
  "message": "The provided transaction data is invalid",
  "code": "VALIDATION_ERROR",
  "details": {
    "field_errors": {
      "amount": ["Amount must be a valid number"],
      "date": ["Date must be in YYYY-MM-DD format"],
      "account_id": ["Account ID is required"]
    },
    "validation_context": "transaction_update"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_abc123456",
  "path": "/v1/transactions/txn_123",
  "method": "PUT"
}
```

## HTTP Status Codes

### 400 Bad Request

Client error due to invalid request format, parameters, or data.

**Common scenarios:**

- Invalid JSON payload
- Missing required parameters
- Invalid parameter values
- Validation failures

```json
{
  "error": "Bad Request",
  "message": "Invalid JSON in request body",
  "code": "INVALID_JSON",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 401 Unauthorized

Authentication required or authentication failed.

**Common scenarios:**

- Missing authentication token
- Invalid or expired JWT token
- Token signature verification failure

```json
{
  "error": "Unauthorized",
  "message": "JWT token has expired",
  "code": "TOKEN_EXPIRED",
  "details": {
    "expires_at": "2024-01-01T11:00:00Z",
    "current_time": "2024-01-01T12:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 403 Forbidden

Authentication successful but access denied due to insufficient permissions.

**Common scenarios:**

- User lacks required permissions
- Account access restrictions
- Business plan limitations

```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions to access this resource",
  "code": "INSUFFICIENT_PERMISSIONS",
  "details": {
    "required_permission": "accounts:write",
    "user_permissions": ["accounts:read", "transactions:read"]
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 404 Not Found

Requested resource does not exist.

**Common scenarios:**

- Transaction not found
- Account not found
- Report not found
- User not found

```json
{
  "error": "Not Found",
  "message": "Transaction not found",
  "code": "TRANSACTION_NOT_FOUND",
  "details": {
    "transaction_id": "txn_nonexistent",
    "user_id": "user_123"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 409 Conflict

Request conflicts with current resource state.

**Common scenarios:**

- Duplicate account connection
- Email already in use during registration
- Transaction already categorized

```json
{
  "error": "Conflict",
  "message": "Account is already connected",
  "code": "ACCOUNT_ALREADY_CONNECTED",
  "details": {
    "account_id": "acc_123",
    "existing_connection": "2024-01-01T10:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 422 Unprocessable Entity

Request is syntactically correct but semantically invalid.

**Common scenarios:**

- Business rule violations
- Invalid date ranges
- Inconsistent data relationships

```json
{
  "error": "Unprocessable Entity",
  "message": "Start date must be before end date",
  "code": "INVALID_DATE_RANGE",
  "details": {
    "start_date": "2024-01-31",
    "end_date": "2024-01-01"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 429 Too Many Requests

Rate limit exceeded.

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 1000,
    "window": 3600,
    "reset_time": "2024-01-01T13:00:00Z",
    "retry_after": 1800
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 500 Internal Server Error

Unexpected server error.

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred. Please try again later.",
  "code": "INTERNAL_SERVER_ERROR",
  "details": {
    "incident_id": "inc_abc123",
    "support_reference": "Please provide this reference when contacting support"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 502 Bad Gateway

External service error (e.g., Plaid API issues).

```json
{
  "error": "Bad Gateway",
  "message": "External service is temporarily unavailable",
  "code": "EXTERNAL_SERVICE_ERROR",
  "details": {
    "service": "plaid_api",
    "service_status": "degraded",
    "retry_recommended": true,
    "estimated_resolution": "2024-01-01T12:30:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 503 Service Unavailable

Service temporarily unavailable (maintenance, overload).

```json
{
  "error": "Service Unavailable",
  "message": "Service is temporarily unavailable for maintenance",
  "code": "MAINTENANCE_MODE",
  "details": {
    "maintenance_window": {
      "start": "2024-01-01T12:00:00Z",
      "end": "2024-01-01T13:00:00Z"
    },
    "retry_after": 3600
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

## Error Codes

### Authentication Errors (AUTH\_\*)

| Code                     | Description                        | HTTP Status |
| ------------------------ | ---------------------------------- | ----------- |
| `AUTH_MISSING_TOKEN`     | No authentication token provided   | 401         |
| `AUTH_INVALID_TOKEN`     | Invalid JWT token format           | 401         |
| `AUTH_TOKEN_EXPIRED`     | JWT token has expired              | 401         |
| `AUTH_SIGNATURE_INVALID` | JWT signature verification failed  | 401         |
| `AUTH_USER_NOT_FOUND`    | User referenced in token not found | 401         |
| `AUTH_USER_INACTIVE`     | User account is deactivated        | 401         |

### Authorization Errors (AUTHZ\_\*)

| Code                             | Description                         | HTTP Status |
| -------------------------------- | ----------------------------------- | ----------- |
| `AUTHZ_INSUFFICIENT_PERMISSIONS` | User lacks required permissions     | 403         |
| `AUTHZ_RESOURCE_ACCESS_DENIED`   | Access to specific resource denied  | 403         |
| `AUTHZ_ACCOUNT_SUSPENDED`        | User account is suspended           | 403         |
| `AUTHZ_FEATURE_NOT_AVAILABLE`    | Feature not available for user plan | 403         |

### Validation Errors (VALIDATION\_\*)

| Code                        | Description               | HTTP Status |
| --------------------------- | ------------------------- | ----------- |
| `VALIDATION_ERROR`          | General validation error  | 400         |
| `VALIDATION_REQUIRED_FIELD` | Required field missing    | 400         |
| `VALIDATION_INVALID_FORMAT` | Field format invalid      | 400         |
| `VALIDATION_INVALID_VALUE`  | Field value invalid       | 400         |
| `VALIDATION_INVALID_LENGTH` | Field length invalid      | 400         |
| `VALIDATION_INVALID_RANGE`  | Value outside valid range | 400         |

### Resource Errors (RESOURCE\_\*)

| Code                      | Description                         | HTTP Status |
| ------------------------- | ----------------------------------- | ----------- |
| `RESOURCE_NOT_FOUND`      | Requested resource not found        | 404         |
| `RESOURCE_ALREADY_EXISTS` | Resource already exists             | 409         |
| `RESOURCE_CONFLICT`       | Resource state conflict             | 409         |
| `RESOURCE_LOCKED`         | Resource is locked for modification | 423         |

### Business Logic Errors (BUSINESS\_\*)

| Code                         | Description                            | HTTP Status |
| ---------------------------- | -------------------------------------- | ----------- |
| `BUSINESS_RULE_VIOLATION`    | Business rule violated                 | 422         |
| `BUSINESS_INVALID_OPERATION` | Operation not allowed in current state | 422         |
| `BUSINESS_DEPENDENCY_ERROR`  | Required dependency not met            | 422         |
| `BUSINESS_QUOTA_EXCEEDED`    | User quota exceeded                    | 422         |

### External Service Errors (EXT\_\*)

| Code                            | Description                           | HTTP Status |
| ------------------------------- | ------------------------------------- | ----------- |
| `EXT_PLAID_ERROR`               | Plaid API error                       | 502         |
| `EXT_PLAID_ITEM_LOGIN_REQUIRED` | Plaid item requires re-authentication | 422         |
| `EXT_PLAID_ITEM_NOT_FOUND`      | Plaid item not found                  | 404         |
| `EXT_PLAID_RATE_LIMIT`          | Plaid rate limit exceeded             | 429         |
| `EXT_SERVICE_UNAVAILABLE`       | External service unavailable          | 502         |

### System Errors (SYSTEM\_\*)

| Code                    | Description               | HTTP Status |
| ----------------------- | ------------------------- | ----------- |
| `SYSTEM_DATABASE_ERROR` | Database operation failed | 500         |
| `SYSTEM_INTERNAL_ERROR` | Unexpected internal error | 500         |
| `SYSTEM_MAINTENANCE`    | System under maintenance  | 503         |
| `SYSTEM_OVERLOADED`     | System overloaded         | 503         |

### Rate Limiting Errors (RATE\_\*)

| Code                  | Description                  | HTTP Status |
| --------------------- | ---------------------------- | ----------- |
| `RATE_LIMIT_EXCEEDED` | General rate limit exceeded  | 429         |
| `RATE_LIMIT_PLAID`    | Plaid endpoint rate limit    | 429         |
| `RATE_LIMIT_ML`       | ML endpoint rate limit       | 429         |
| `RATE_LIMIT_REPORTS`  | Report generation rate limit | 429         |

## Error Context by Domain

### Transaction Errors

```json
{
  "error": "Transaction Error",
  "message": "Cannot categorize a pending transaction",
  "code": "TRANSACTION_PENDING_CATEGORIZATION",
  "details": {
    "transaction_id": "txn_123",
    "transaction_status": "pending",
    "authorized_date": null,
    "date": "2024-01-01"
  }
}
```

### Account Errors

```json
{
  "error": "Account Error",
  "message": "Account requires re-authentication with bank",
  "code": "ACCOUNT_AUTH_REQUIRED",
  "details": {
    "account_id": "acc_123",
    "institution_name": "Chase Bank",
    "last_successful_sync": "2024-01-01T06:00:00Z",
    "error_type": "item_login_required",
    "reauth_url": "https://app.manna.financial/reauth/acc_123"
  }
}
```

### Report Generation Errors

```json
{
  "error": "Report Generation Error",
  "message": "Insufficient data for requested date range",
  "code": "REPORT_INSUFFICIENT_DATA",
  "details": {
    "report_type": "pnl",
    "requested_start_date": "2024-01-01",
    "requested_end_date": "2024-01-31",
    "earliest_transaction_date": "2024-01-15",
    "transaction_count": 5
  }
}
```

### ML Categorization Errors

```json
{
  "error": "ML Error",
  "message": "Model training failed due to insufficient data",
  "code": "ML_TRAINING_INSUFFICIENT_DATA",
  "details": {
    "required_samples": 100,
    "available_samples": 25,
    "categories_with_insufficient_data": ["Travel", "Entertainment"],
    "recommendation": "Manually categorize more transactions before training"
  }
}
```

## Client Error Handling

### TypeScript Error Handler

```typescript
interface ApiErrorResponse {
  error: string;
  message: string;
  code: string;
  details?: any;
  timestamp: string;
  request_id: string;
}

class ApiClient {
  private async handleApiResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData: ApiErrorResponse = await response.json();
      throw new ApiError(errorData, response.status);
    }
    return response.json();
  }
}

class ApiError extends Error {
  constructor(
    public errorResponse: ApiErrorResponse,
    public statusCode: number
  ) {
    super(errorResponse.message);
    this.name = 'ApiError';
  }

  get code(): string {
    return this.errorResponse.code;
  }

  get details(): any {
    return this.errorResponse.details;
  }

  get requestId(): string {
    return this.errorResponse.request_id;
  }

  isAuthenticationError(): boolean {
    return this.statusCode === 401;
  }

  isAuthorizationError(): boolean {
    return this.statusCode === 403;
  }

  isValidationError(): boolean {
    return this.statusCode === 400 || this.statusCode === 422;
  }

  isRateLimitError(): boolean {
    return this.statusCode === 429;
  }

  isServerError(): boolean {
    return this.statusCode >= 500;
  }

  isRetryable(): boolean {
    return (
      this.statusCode >= 500 ||
      this.statusCode === 429 ||
      this.statusCode === 502
    );
  }
}

// Usage example
try {
  const transactions = await apiClient.getTransactions();
} catch (error) {
  if (error instanceof ApiError) {
    if (error.isAuthenticationError()) {
      // Redirect to login
      window.location.href = '/login';
    } else if (error.isValidationError()) {
      // Show validation errors to user
      displayValidationErrors(error.details.field_errors);
    } else if (error.isRateLimitError()) {
      // Implement retry with backoff
      setTimeout(() => retryRequest(), error.details.retry_after * 1000);
    } else if (error.isRetryable()) {
      // Retry the request
      retryWithExponentialBackoff();
    } else {
      // Show generic error message
      showErrorMessage(error.message);
    }
  }
}
```

### Error Recovery Patterns

#### Retry with Exponential Backoff

```typescript
async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (
        error instanceof ApiError &&
        error.isRetryable() &&
        attempt < maxRetries
      ) {
        const delay = baseDelay * Math.pow(2, attempt - 1);
        await new Promise((resolve) => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

#### Circuit Breaker Pattern

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private failureThreshold = 5,
    private recoveryTimeout = 60000
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.recoveryTimeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = 'closed';
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();
    if (this.failures >= this.failureThreshold) {
      this.state = 'open';
    }
  }
}
```

## Error Monitoring and Alerting

### Error Metrics to Track

1. **Error Rate**: Percentage of requests resulting in errors
2. **Error Distribution**: Breakdown by status code and error code
3. **Error Trends**: Error patterns over time
4. **User Impact**: Users affected by errors
5. **Endpoint Health**: Error rates per endpoint

### Alert Thresholds

- **Critical**: Error rate > 5% for 5 minutes
- **Warning**: Error rate > 2% for 10 minutes
- **Info**: New error code introduced
- **External**: Plaid API errors > 1% for 3 minutes

### Error Logging Format

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "ERROR",
  "message": "Transaction validation failed",
  "error_code": "VALIDATION_ERROR",
  "request_id": "req_123",
  "user_id": "user_456",
  "endpoint": "/v1/transactions/txn_789",
  "method": "PUT",
  "status_code": 400,
  "response_time_ms": 150,
  "details": {
    "validation_errors": ["amount must be a number"],
    "request_body_size": 256
  },
  "trace_id": "trace_abc123",
  "span_id": "span_def456"
}
```
