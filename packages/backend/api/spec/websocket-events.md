# WebSocket Events Specification

## Overview

The Manna Financial Management Platform provides real-time updates via WebSocket connections. This enables immediate notifications of transaction updates, categorization results, sync status, and system events.

## Connection

### Endpoint

```
wss://api.manna.financial/ws/updates
```

### Authentication

WebSocket connections require JWT authentication via query parameter:

```
wss://api.manna.financial/ws/updates?token=<jwt_access_token>
```

### Connection Lifecycle

1. **Connection Establishment**
   - Client connects with valid JWT token
   - Server validates token and establishes connection
   - Server sends `connection_established` event

2. **Heartbeat**
   - Server sends `ping` every 30 seconds
   - Client should respond with `pong`
   - Connection closed if no response within 60 seconds

3. **Graceful Disconnection**
   - Client sends `disconnect` message
   - Server acknowledges and closes connection

## Message Format

All messages follow a consistent JSON format:

```typescript
interface WebSocketMessage {
  type: string;
  data: Record<string, unknown>;
  timestamp: string; // ISO 8601
  sequence?: number; // Optional sequence number for ordering
  user_id?: string; // Optional user context
}
```

## Event Types

### System Events

#### connection_established

Sent immediately after successful connection.

```json
{
  "type": "connection_established",
  "data": {
    "user_id": "user_12345",
    "session_id": "ws_session_abc123",
    "server_time": "2024-01-01T12:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### ping

Server heartbeat to maintain connection.

```json
{
  "type": "ping",
  "data": {},
  "timestamp": "2024-01-01T12:00:30Z"
}
```

Expected client response:

```json
{
  "type": "pong",
  "data": {},
  "timestamp": "2024-01-01T12:00:30Z"
}
```

#### error

System or connection errors.

```json
{
  "type": "error",
  "data": {
    "error_code": "AUTHENTICATION_FAILED",
    "message": "JWT token has expired",
    "details": {
      "expires_at": "2024-01-01T11:00:00Z"
    },
    "recoverable": false
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Transaction Events

#### transaction_added

New transaction detected and added to the system.

```json
{
  "type": "transaction_added",
  "data": {
    "transaction": {
      "id": "txn_12345",
      "account_id": "acc_67890",
      "amount": -25.5,
      "date": "2024-01-01",
      "name": "STARBUCKS #1234",
      "merchant_name": "Starbucks",
      "pending": false,
      "is_business": true,
      "category": null,
      "ml_category": null
    },
    "account": {
      "id": "acc_67890",
      "name": "Business Checking",
      "institution_name": "Chase"
    },
    "source": "plaid_sync"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1001
}
```

#### transaction_updated

Existing transaction was modified.

```json
{
  "type": "transaction_updated",
  "data": {
    "transaction_id": "txn_12345",
    "changes": {
      "category": {
        "old": null,
        "new": "Business Meals"
      },
      "is_tax_deductible": {
        "old": false,
        "new": true
      }
    },
    "updated_by": "user_12345",
    "source": "manual_categorization"
  },
  "timestamp": "2024-01-01T12:05:00Z",
  "sequence": 1002
}
```

#### transactions_bulk_updated

Multiple transactions updated in a batch operation.

```json
{
  "type": "transactions_bulk_updated",
  "data": {
    "transaction_ids": ["txn_123", "txn_456", "txn_789"],
    "update_count": 3,
    "changes": {
      "category": "Office Supplies",
      "is_business": true
    },
    "updated_by": "user_12345",
    "source": "bulk_update"
  },
  "timestamp": "2024-01-01T12:10:00Z",
  "sequence": 1003
}
```

### Categorization Events

#### categorization_started

ML categorization process started.

```json
{
  "type": "categorization_started",
  "data": {
    "batch_id": "cat_batch_123",
    "transaction_count": 25,
    "estimated_completion": "2024-01-01T12:02:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1004
}
```

#### categorization_progress

Progress update during categorization.

```json
{
  "type": "categorization_progress",
  "data": {
    "batch_id": "cat_batch_123",
    "processed": 15,
    "total": 25,
    "progress_percent": 60,
    "estimated_remaining": "30s"
  },
  "timestamp": "2024-01-01T12:01:30Z",
  "sequence": 1005
}
```

#### categorization_complete

ML categorization finished.

```json
{
  "type": "categorization_complete",
  "data": {
    "batch_id": "cat_batch_123",
    "transaction_ids": ["txn_123", "txn_456", "txn_789"],
    "results": {
      "categorized_count": 23,
      "high_confidence_count": 18,
      "low_confidence_count": 5,
      "failed_count": 2
    },
    "average_confidence": 0.87,
    "processing_time_ms": 1250
  },
  "timestamp": "2024-01-01T12:02:00Z",
  "sequence": 1006
}
```

#### categorization_suggestion

New categorization suggestion available.

```json
{
  "type": "categorization_suggestion",
  "data": {
    "transaction_id": "txn_12345",
    "suggested_category": "Business Meals",
    "confidence": 0.75,
    "reasoning": "Similar transactions from this merchant are typically categorized as Business Meals",
    "similar_transactions": ["txn_111", "txn_222"],
    "requires_review": true
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1007
}
```

### Sync Events

#### sync_started

Account synchronization started.

```json
{
  "type": "sync_started",
  "data": {
    "sync_id": "sync_12345",
    "account_ids": ["acc_123", "acc_456"],
    "sync_type": "incremental",
    "estimated_completion": "2024-01-01T12:05:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1008
}
```

#### sync_progress

Progress update during sync operation.

```json
{
  "type": "sync_progress",
  "data": {
    "sync_id": "sync_12345",
    "current_account": "acc_123",
    "accounts_completed": 1,
    "total_accounts": 2,
    "transactions_fetched": 45,
    "new_transactions": 12,
    "progress_percent": 50
  },
  "timestamp": "2024-01-01T12:02:30Z",
  "sequence": 1009
}
```

#### sync_complete

Account synchronization completed.

```json
{
  "type": "sync_complete",
  "data": {
    "sync_id": "sync_12345",
    "account_ids": ["acc_123", "acc_456"],
    "results": {
      "total_transactions_fetched": 87,
      "new_transactions": 23,
      "updated_transactions": 5,
      "accounts_synced": 2,
      "accounts_failed": 0
    },
    "sync_duration_ms": 3250,
    "next_sync_recommended": "2024-01-01T18:00:00Z"
  },
  "timestamp": "2024-01-01T12:05:00Z",
  "sequence": 1010
}
```

#### sync_error

Error during sync operation.

```json
{
  "type": "sync_error",
  "data": {
    "sync_id": "sync_12345",
    "account_id": "acc_456",
    "error_code": "ITEM_LOGIN_REQUIRED",
    "error_message": "User authentication required to continue sync",
    "recoverable": true,
    "recovery_action": "reauth_required",
    "recovery_url": "https://app.manna.financial/reauth/acc_456"
  },
  "timestamp": "2024-01-01T12:03:00Z",
  "sequence": 1011
}
```

### Report Events

#### report_generation_started

Financial report generation started.

```json
{
  "type": "report_generation_started",
  "data": {
    "report_id": "report_12345",
    "report_type": "pnl",
    "parameters": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "include_comparison": true
    },
    "estimated_completion": "2024-01-01T12:02:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1012
}
```

#### report_generation_progress

Progress update for report generation.

```json
{
  "type": "report_generation_progress",
  "data": {
    "report_id": "report_12345",
    "stage": "calculating_totals",
    "progress_percent": 60,
    "current_operation": "Processing expense categories"
  },
  "timestamp": "2024-01-01T12:01:12Z",
  "sequence": 1013
}
```

#### report_ready

Financial report generation completed.

```json
{
  "type": "report_ready",
  "data": {
    "report_id": "report_12345",
    "report_type": "pnl",
    "download_url": "https://api.manna.financial/v1/reports/report_12345/download",
    "expires_at": "2024-01-08T12:00:00Z",
    "file_size": 245760,
    "format": "pdf",
    "generation_time_ms": 2150
  },
  "timestamp": "2024-01-01T12:02:00Z",
  "sequence": 1014
}
```

### Account Events

#### account_connected

New financial account connected.

```json
{
  "type": "account_connected",
  "data": {
    "account": {
      "id": "acc_new123",
      "name": "Savings Account",
      "institution_name": "Bank of America",
      "type": "depository",
      "subtype": "savings",
      "mask": "1234"
    },
    "connection_method": "plaid_link",
    "initial_balance": 5000.0,
    "sync_status": "pending"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1015
}
```

#### account_disconnected

Financial account disconnected.

```json
{
  "type": "account_disconnected",
  "data": {
    "account_id": "acc_123",
    "account_name": "Old Checking",
    "reason": "user_requested",
    "final_balance": 1250.75,
    "transaction_count": 1205
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1016
}
```

#### account_error

Account-related error occurred.

```json
{
  "type": "account_error",
  "data": {
    "account_id": "acc_123",
    "error_code": "ITEM_LOGIN_REQUIRED",
    "error_message": "User needs to re-authenticate with bank",
    "error_type": "auth_error",
    "requires_user_action": true,
    "action_url": "https://app.manna.financial/reauth/acc_123",
    "last_successful_sync": "2024-01-01T06:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1017
}
```

### Training Events

#### model_training_started

ML model training initiated.

```json
{
  "type": "model_training_started",
  "data": {
    "training_id": "training_12345",
    "model_type": "transaction_categorizer",
    "training_data_count": 5000,
    "estimated_completion": "2024-01-01T12:30:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "sequence": 1018
}
```

#### model_training_complete

ML model training completed.

```json
{
  "type": "model_training_complete",
  "data": {
    "training_id": "training_12345",
    "model_version": "v2.1.0",
    "accuracy_improvement": 0.03,
    "new_accuracy": 0.91,
    "training_time_ms": 1800000,
    "deployed": true
  },
  "timestamp": "2024-01-01T12:30:00Z",
  "sequence": 1019
}
```

## Client Implementation

### JavaScript/TypeScript Example

```typescript
class MannaWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(private token: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `wss://api.manna.financial/ws/updates?token=${this.token}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        resolve();
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.reason);
        this.stopHeartbeat();
        if (event.code !== 1000) {
          // Not a normal closure
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
    });
  }

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'ping':
        this.sendPong();
        break;
      case 'transaction_added':
        this.onTransactionAdded(message.data);
        break;
      case 'categorization_complete':
        this.onCategorizationComplete(message.data);
        break;
      case 'sync_complete':
        this.onSyncComplete(message.data);
        break;
      case 'report_ready':
        this.onReportReady(message.data);
        break;
      case 'error':
        this.onError(message.data);
        break;
    }
  }

  private sendPong(): void {
    this.send({
      type: 'pong',
      data: {},
      timestamp: new Date().toISOString(),
    });
  }

  private send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  private startHeartbeat(): void {
    // Server sends ping every 30s, we expect it within 45s
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) {
        this.attemptReconnect();
      }
    }, 45000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    setTimeout(() => {
      console.log(
        `Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`
      );
      this.connect().catch(() => {
        this.attemptReconnect();
      });
    }, delay);
  }

  // Event handlers - implement based on your application needs
  private onTransactionAdded(data: any): void {
    console.log('New transaction:', data.transaction);
  }

  private onCategorizationComplete(data: any): void {
    console.log('Categorization complete:', data.results);
  }

  private onSyncComplete(data: any): void {
    console.log('Sync complete:', data.results);
  }

  private onReportReady(data: any): void {
    console.log('Report ready:', data.download_url);
  }

  private onError(data: any): void {
    console.error('WebSocket error:', data);
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }
}
```

## Security Considerations

### Authentication

- JWT tokens must be valid and not expired
- Tokens are validated on connection and periodically during the session
- Invalid tokens result in immediate connection termination

### Authorization

- Users only receive events for their own data
- Admin users may receive system-wide events (configurable)
- Event filtering based on user permissions

### Rate Limiting

- WebSocket connections are limited per user (default: 3 concurrent)
- Message rate limiting to prevent abuse
- Automatic disconnection for excessive message rates

### Data Privacy

- All messages are encrypted in transit (WSS)
- Sensitive data is not included in events (only references/IDs)
- Event history is not stored on the server

## Monitoring and Debugging

### Connection Metrics

- Active connection count
- Connection duration
- Reconnection rates
- Message throughput

### Debug Events

In development mode, additional debug events are available:

```json
{
  "type": "debug_info",
  "data": {
    "connection_id": "conn_abc123",
    "server_load": 0.45,
    "event_queue_size": 12,
    "last_heartbeat": "2024-01-01T12:00:30Z"
  },
  "timestamp": "2024-01-01T12:00:35Z"
}
```
