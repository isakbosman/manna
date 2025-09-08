# API Integration Guide

## Overview

This guide provides comprehensive information for integrating with the Manna Financial Management Platform API. It covers authentication patterns, best practices, SDK usage, and common integration scenarios.

## Quick Start

### 1. Authentication Setup

```typescript
// Install the SDK
npm install @manna/api-client

// Initialize client
import { MannaApiClient } from '@manna/api-client';

const client = new MannaApiClient({
  baseURL: 'https://api.manna.financial/v1',
  apiKey: process.env.MANNA_API_KEY, // For server-to-server
  // OR
  accessToken: 'your_jwt_token', // For user-specific requests
});
```

### 2. Basic Transaction Retrieval

```typescript
// Get recent transactions
const transactions = await client.transactions.list({
  start_date: '2024-01-01',
  end_date: '2024-01-31',
  per_page: 50,
});

console.log(`Found ${transactions.pagination.total_items} transactions`);
transactions.transactions.forEach((txn) => {
  console.log(`${txn.date}: ${txn.name} - $${txn.amount}`);
});
```

### 3. WebSocket Connection

```typescript
// Connect to real-time updates
const wsClient = client.createWebSocketConnection();
wsClient.connect();

wsClient.on('transaction_added', (data) => {
  console.log('New transaction:', data.transaction);
});

wsClient.on('categorization_complete', (data) => {
  console.log('Categorization done:', data.results);
});
```

## Authentication Patterns

### JWT Token-Based (Recommended)

```typescript
class AuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  async login(email: string, password: string): Promise<void> {
    const response = await fetch('/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;

    // Store tokens securely (httpOnly cookies recommended)
    this.storeTokens(data.access_token, data.refresh_token);
  }

  async makeAuthenticatedRequest(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    if (!this.accessToken) {
      throw new Error('No access token available');
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${this.accessToken}`,
      },
    });

    // Handle token expiration
    if (response.status === 401) {
      await this.refreshAccessToken();
      // Retry with new token
      return this.makeAuthenticatedRequest(url, options);
    }

    return response;
  }

  private async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch('/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      this.storeTokens(data.access_token, this.refreshToken);
    } else {
      // Refresh failed, redirect to login
      this.logout();
      throw new Error('Token refresh failed');
    }
  }
}
```

### API Key Authentication (Server-to-Server)

```typescript
const client = new MannaApiClient({
  baseURL: 'https://api.manna.financial/v1',
  apiKey: process.env.MANNA_API_KEY,
  headers: {
    'X-Client-Version': '1.0.0',
    'X-Client-Name': 'MyApp',
  },
});
```

## Common Integration Patterns

### 1. Account Connection Flow

```typescript
class PlaidIntegration {
  private client: MannaApiClient;

  constructor(client: MannaApiClient) {
    this.client = client;
  }

  async initiatePlaidLink(userId: string): Promise<string> {
    // Step 1: Create link token
    const linkToken = await this.client.plaid.createLinkToken({
      user_id: userId,
      products: ['transactions'],
      country_codes: ['US'],
    });

    return linkToken.link_token;
  }

  async handlePlaidSuccess(publicToken: string, metadata: any): Promise<void> {
    try {
      // Step 2: Exchange public token for access token
      const result = await this.client.plaid.exchangeToken({
        public_token: publicToken,
        account_ids: metadata.accounts.map((acc) => acc.id),
      });

      console.log(`Connected ${result.accounts.length} accounts`);

      // Step 3: Initiate sync
      await this.client.plaid.sync({
        account_ids: result.accounts.map((acc) => acc.account_id),
        force_full_sync: true,
      });

      // Step 4: Set up WebSocket to monitor sync progress
      this.monitorSyncProgress();
    } catch (error) {
      console.error('Account connection failed:', error);
      throw error;
    }
  }

  private monitorSyncProgress(): void {
    const ws = this.client.createWebSocketConnection();

    ws.on('sync_complete', (data) => {
      console.log('Sync completed:', data.results);
      this.onSyncComplete(data);
    });

    ws.on('sync_error', (data) => {
      console.error('Sync error:', data);
      this.onSyncError(data);
    });
  }
}
```

### 2. Transaction Processing Pipeline

```typescript
class TransactionProcessor {
  private client: MannaApiClient;

  constructor(client: MannaApiClient) {
    this.client = client;
  }

  async processNewTransactions(): Promise<void> {
    // Step 1: Get uncategorized transactions
    const transactions = await this.client.transactions.list({
      needs_review: true,
      per_page: 100,
    });

    if (transactions.transactions.length === 0) {
      console.log('No transactions need processing');
      return;
    }

    // Step 2: Batch categorize using ML
    const categorizationResult = await this.client.ml.categorize({
      transaction_ids: transactions.transactions.map((t) => t.id),
      force_recategorize: false,
    });

    console.log(
      `Categorized ${categorizationResult.categorized_count} transactions`
    );

    // Step 3: Apply business rules
    await this.applyBusinessRules(transactions.transactions);

    // Step 4: Generate reports if month-end
    if (this.isMonthEnd()) {
      await this.generateMonthlyReports();
    }
  }

  private async applyBusinessRules(transactions: Transaction[]): Promise<void> {
    const bulkUpdates: Array<{ ids: string[]; updates: any }> = [];

    // Rule 1: Mark office supply purchases as tax deductible
    const officeSupplies = transactions.filter(
      (t) => t.ml_category === 'Office Supplies' && t.is_business
    );

    if (officeSupplies.length > 0) {
      bulkUpdates.push({
        ids: officeSupplies.map((t) => t.id),
        updates: { is_tax_deductible: true },
      });
    }

    // Rule 2: Flag large transactions for review
    const largeTransactions = transactions.filter(
      (t) => Math.abs(t.amount) > 1000
    );

    if (largeTransactions.length > 0) {
      bulkUpdates.push({
        ids: largeTransactions.map((t) => t.id),
        updates: {
          tags: ['review-required', 'large-amount'],
          notes: 'Flagged for review due to large amount',
        },
      });
    }

    // Apply bulk updates
    for (const update of bulkUpdates) {
      await this.client.transactions.bulkUpdate({
        transaction_ids: update.ids,
        updates: update.updates,
      });
    }
  }

  private async generateMonthlyReports(): Promise<void> {
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);

    const startDate = new Date(
      lastMonth.getFullYear(),
      lastMonth.getMonth(),
      1
    );
    const endDate = new Date(
      lastMonth.getFullYear(),
      lastMonth.getMonth() + 1,
      0
    );

    // Generate P&L report
    const reportRequest = await this.client.reports.generate({
      report_type: 'pnl',
      parameters: {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        include_comparison: true,
      },
      format: 'pdf',
      delivery_method: 'email',
    });

    console.log(`Report generation initiated: ${reportRequest.report_id}`);
  }

  private isMonthEnd(): boolean {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    return today.getMonth() !== tomorrow.getMonth();
  }
}
```

### 3. Real-time Dashboard Updates

```typescript
class DashboardService {
  private client: MannaApiClient;
  private wsClient: WebSocketClient;
  private eventBus: EventEmitter;

  constructor(client: MannaApiClient) {
    this.client = client;
    this.eventBus = new EventEmitter();
    this.setupWebSocketConnection();
  }

  private setupWebSocketConnection(): void {
    this.wsClient = this.client.createWebSocketConnection();

    // Handle different event types
    this.wsClient.on('transaction_added', this.handleNewTransaction.bind(this));
    this.wsClient.on(
      'categorization_complete',
      this.handleCategorizationUpdate.bind(this)
    );
    this.wsClient.on('sync_complete', this.handleSyncComplete.bind(this));
    this.wsClient.on('report_ready', this.handleReportReady.bind(this));

    this.wsClient.connect();
  }

  private handleNewTransaction(data: any): void {
    // Update transaction list in real-time
    this.eventBus.emit('dashboard:transaction_added', {
      transaction: data.transaction,
      account: data.account,
    });

    // Update account balance if provided
    if (data.account.balance) {
      this.eventBus.emit('dashboard:balance_updated', {
        account_id: data.account.id,
        new_balance: data.account.balance.current,
      });
    }

    // Update summary statistics
    this.updateDashboardSummary();
  }

  private handleCategorizationUpdate(data: any): void {
    this.eventBus.emit('dashboard:categorization_updated', {
      transaction_count: data.categorized_count,
      results: data.results,
    });

    // Refresh category breakdown chart
    this.refreshCategoryBreakdown();
  }

  private handleSyncComplete(data: any): void {
    this.eventBus.emit('dashboard:sync_complete', {
      accounts_synced: data.account_ids.length,
      new_transactions: data.results.new_transactions,
      updated_transactions: data.results.updated_transactions,
    });

    // Refresh all dashboard components
    this.refreshDashboard();
  }

  private handleReportReady(data: any): void {
    this.eventBus.emit('dashboard:report_ready', {
      report_type: data.report_type,
      download_url: data.download_url,
    });
  }

  async getDashboardData(): Promise<DashboardData> {
    const [accounts, recentTransactions, kpis] = await Promise.all([
      this.client.accounts.list(),
      this.client.transactions.list({
        per_page: 10,
        sort_by: 'date',
        sort_order: 'desc',
      }),
      this.client.reports.getKPIs({ period: 'month' }),
    ]);

    return {
      accounts: accounts.accounts,
      recent_transactions: recentTransactions.transactions,
      kpis: kpis,
      summary: recentTransactions.summary,
    };
  }

  // Subscribe to dashboard events
  onDashboardUpdate(callback: (event: string, data: any) => void): void {
    this.eventBus.on('dashboard:*', callback);
  }
}
```

## Error Handling Strategies

### 1. Comprehensive Error Handler

```typescript
class ApiErrorHandler {
  static handle(error: ApiError, context: string): void {
    switch (error.code) {
      case 'TOKEN_EXPIRED':
        this.handleTokenExpired(error);
        break;

      case 'RATE_LIMIT_EXCEEDED':
        this.handleRateLimit(error);
        break;

      case 'VALIDATION_ERROR':
        this.handleValidationError(error, context);
        break;

      case 'EXT_PLAID_ITEM_LOGIN_REQUIRED':
        this.handlePlaidReauth(error);
        break;

      case 'ACCOUNT_NOT_FOUND':
        this.handleMissingAccount(error);
        break;

      default:
        this.handleGenericError(error, context);
    }
  }

  private static handleTokenExpired(error: ApiError): void {
    // Clear stored tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    // Redirect to login
    window.location.href = '/login?expired=true';
  }

  private static handleRateLimit(error: ApiError): void {
    const retryAfter = error.details?.retry_after || 60;

    // Show user-friendly message
    showNotification({
      type: 'warning',
      title: 'Too Many Requests',
      message: `Please wait ${retryAfter} seconds before trying again.`,
      duration: retryAfter * 1000,
    });

    // Disable relevant UI elements
    disableActionButtons(retryAfter * 1000);
  }

  private static handleValidationError(error: ApiError, context: string): void {
    const fieldErrors = error.details?.field_errors || {};

    // Show field-specific errors in forms
    Object.entries(fieldErrors).forEach(([field, errors]) => {
      showFieldError(field, errors[0]);
    });

    // Log for debugging
    console.warn(`Validation error in ${context}:`, fieldErrors);
  }

  private static handlePlaidReauth(error: ApiError): void {
    const reAuthUrl = error.details?.reauth_url;

    showModal({
      title: 'Account Re-authentication Required',
      message:
        'Your bank account needs to be re-connected. This is normal for security reasons.',
      actions: [
        {
          label: 'Reconnect Account',
          action: () => window.open(reAuthUrl, '_blank'),
        },
        {
          label: 'Later',
          action: () => {},
        },
      ],
    });
  }
}
```

### 2. Retry Logic with Circuit Breaker

```typescript
class ResilientApiClient {
  private circuitBreaker: CircuitBreaker;
  private retryConfig = {
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 10000,
  };

  constructor(private baseClient: MannaApiClient) {
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 5,
      recoveryTimeout: 30000,
    });
  }

  async makeRequest<T>(operation: () => Promise<T>): Promise<T> {
    return this.circuitBreaker.execute(async () => {
      return this.retryWithBackoff(operation);
    });
  }

  private async retryWithBackoff<T>(operation: () => Promise<T>): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= this.retryConfig.maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;

        // Don't retry certain errors
        if (error instanceof ApiError) {
          if (!error.isRetryable() || error.isValidationError()) {
            throw error;
          }
        }

        // Calculate delay for next attempt
        if (attempt < this.retryConfig.maxAttempts) {
          const delay = Math.min(
            this.retryConfig.baseDelay * Math.pow(2, attempt - 1),
            this.retryConfig.maxDelay
          );

          console.log(`Attempt ${attempt} failed, retrying in ${delay}ms`);
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError;
  }
}
```

## Performance Optimization

### 1. Request Batching

```typescript
class BatchedApiClient {
  private batchQueue: Array<{
    operation: () => Promise<any>;
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = [];

  private batchTimeout: NodeJS.Timeout | null = null;

  constructor(
    private client: MannaApiClient,
    private batchDelay = 100,
    private maxBatchSize = 10
  ) {}

  async getTransaction(id: string): Promise<Transaction> {
    return this.batchRequest(() => this.client.transactions.get(id));
  }

  private batchRequest<T>(operation: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.batchQueue.push({ operation, resolve, reject });

      if (this.batchQueue.length >= this.maxBatchSize) {
        this.processBatch();
      } else if (!this.batchTimeout) {
        this.batchTimeout = setTimeout(
          () => this.processBatch(),
          this.batchDelay
        );
      }
    });
  }

  private async processBatch(): Promise<void> {
    const batch = this.batchQueue.splice(0, this.maxBatchSize);

    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }

    // Execute all operations in parallel
    const results = await Promise.allSettled(
      batch.map((item) => item.operation())
    );

    // Resolve/reject individual promises
    results.forEach((result, index) => {
      const item = batch[index];
      if (result.status === 'fulfilled') {
        item.resolve(result.value);
      } else {
        item.reject(result.reason);
      }
    });
  }
}
```

### 2. Response Caching

```typescript
class CachedApiClient {
  private cache = new Map<
    string,
    {
      data: any;
      timestamp: number;
      ttl: number;
    }
  >();

  constructor(private client: MannaApiClient) {}

  async getAccounts(ttl = 5 * 60 * 1000): Promise<Account[]> {
    const cacheKey = 'accounts';
    const cached = this.cache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data;
    }

    const accounts = await this.client.accounts.list();
    this.cache.set(cacheKey, {
      data: accounts.accounts,
      timestamp: Date.now(),
      ttl,
    });

    return accounts.accounts;
  }

  async getTransactions(
    filters: TransactionFilters,
    ttl = 2 * 60 * 1000
  ): Promise<TransactionListResponse> {
    const cacheKey = `transactions:${JSON.stringify(filters)}`;
    const cached = this.cache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data;
    }

    const transactions = await this.client.transactions.list(filters);
    this.cache.set(cacheKey, {
      data: transactions,
      timestamp: Date.now(),
      ttl,
    });

    return transactions;
  }

  invalidateCache(pattern?: string): void {
    if (pattern) {
      const regex = new RegExp(pattern);
      for (const key of this.cache.keys()) {
        if (regex.test(key)) {
          this.cache.delete(key);
        }
      }
    } else {
      this.cache.clear();
    }
  }
}
```

## Testing Strategies

### 1. Mock API Responses

```typescript
// jest.setup.ts
import { jest } from '@jest/globals';

const mockApiClient = {
  transactions: {
    list: jest.fn(),
    get: jest.fn(),
    update: jest.fn(),
    bulkUpdate: jest.fn(),
  },
  accounts: {
    list: jest.fn(),
    connect: jest.fn(),
  },
  plaid: {
    createLinkToken: jest.fn(),
    exchangeToken: jest.fn(),
    sync: jest.fn(),
  },
};

// Test file
describe('TransactionProcessor', () => {
  let processor: TransactionProcessor;

  beforeEach(() => {
    processor = new TransactionProcessor(mockApiClient as any);
  });

  it('should process uncategorized transactions', async () => {
    // Setup mocks
    mockApiClient.transactions.list.mockResolvedValue({
      transactions: [
        { id: 'txn_1', name: 'Starbucks', amount: -5.99, ml_category: null },
        {
          id: 'txn_2',
          name: 'Office Depot',
          amount: -49.99,
          ml_category: null,
        },
      ],
      pagination: { total_items: 2 },
    });

    mockApiClient.ml.categorize.mockResolvedValue({
      categorized_count: 2,
      results: [
        {
          transaction_id: 'txn_1',
          predicted_category: 'Food',
          confidence: 0.9,
        },
        {
          transaction_id: 'txn_2',
          predicted_category: 'Office Supplies',
          confidence: 0.95,
        },
      ],
    });

    // Execute
    await processor.processNewTransactions();

    // Verify
    expect(mockApiClient.transactions.list).toHaveBeenCalledWith({
      needs_review: true,
      per_page: 100,
    });

    expect(mockApiClient.ml.categorize).toHaveBeenCalledWith({
      transaction_ids: ['txn_1', 'txn_2'],
      force_recategorize: false,
    });
  });
});
```

### 2. Integration Tests

```typescript
describe('API Integration Tests', () => {
  let client: MannaApiClient;

  beforeAll(() => {
    client = new MannaApiClient({
      baseURL: 'http://localhost:8000/v1',
      accessToken: process.env.TEST_ACCESS_TOKEN,
    });
  });

  it('should authenticate and fetch user data', async () => {
    const accounts = await client.accounts.list();
    expect(accounts.accounts).toBeDefined();
    expect(Array.isArray(accounts.accounts)).toBe(true);
  });

  it('should handle pagination correctly', async () => {
    const page1 = await client.transactions.list({
      per_page: 10,
      page: 1,
    });

    expect(page1.transactions.length).toBeLessThanOrEqual(10);
    expect(page1.pagination.page).toBe(1);

    if (page1.pagination.has_next) {
      const page2 = await client.transactions.list({
        per_page: 10,
        page: 2,
      });

      expect(page2.transactions.length).toBeLessThanOrEqual(10);
      expect(page2.pagination.page).toBe(2);
    }
  });
});
```

## SDK Configuration

### Environment-Specific Configurations

```typescript
// config/api.ts
interface ApiConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  rateLimit: {
    maxRequests: number;
    windowMs: number;
  };
}

const configs: Record<string, ApiConfig> = {
  development: {
    baseURL: 'http://localhost:8000/v1',
    timeout: 30000,
    retries: 3,
    rateLimit: {
      maxRequests: 1000,
      windowMs: 3600000,
    },
  },
  staging: {
    baseURL: 'https://staging-api.manna.financial/v1',
    timeout: 15000,
    retries: 3,
    rateLimit: {
      maxRequests: 500,
      windowMs: 3600000,
    },
  },
  production: {
    baseURL: 'https://api.manna.financial/v1',
    timeout: 10000,
    retries: 2,
    rateLimit: {
      maxRequests: 1000,
      windowMs: 3600000,
    },
  },
};

export const getApiConfig = (): ApiConfig => {
  const env = process.env.NODE_ENV || 'development';
  return configs[env] || configs.development;
};
```

### Custom Client Configuration

```typescript
const client = new MannaApiClient({
  ...getApiConfig(),

  // Custom headers
  headers: {
    'X-Client-Name': 'MyFinanceApp',
    'X-Client-Version': '1.2.0',
    'X-Request-Source': 'web-app',
  },

  // Request interceptors
  interceptors: {
    request: (config) => {
      // Add request ID for tracking
      config.headers['X-Request-ID'] = generateRequestId();

      // Add timestamp
      config.headers['X-Request-Timestamp'] = new Date().toISOString();

      return config;
    },

    response: (response) => {
      // Log response metrics
      console.log(
        `API Response: ${response.status} in ${response.headers['X-Response-Time']}ms`
      );

      return response;
    },
  },

  // Error handling
  onError: (error) => {
    // Custom error handling
    if (error.code === 'NETWORK_ERROR') {
      showNetworkErrorDialog();
    }

    // Send to error tracking service
    errorTracker.captureException(error);
  },
});
```

This comprehensive integration guide covers the major patterns and best practices for working with the Manna Financial Management Platform API. The examples demonstrate real-world usage scenarios and provide production-ready code patterns for robust integrations.
