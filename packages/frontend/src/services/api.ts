/**
 * API Service Layer
 * Provides typed API methods for all backend endpoints
 */

import { api, API_ENDPOINTS } from '@/lib/api-client';
import type {
  User,
  Account,
  Transaction,
  Category,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  PlaidLinkTokenResponse,
  PlaidExchangeTokenRequest,
  MLPrediction,
  Report,
} from '@manna/shared';

// Authentication Service
export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>(API_ENDPOINTS.auth.login, credentials);
    
    // Store tokens
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
    }
    if (response.refresh_token) {
      localStorage.setItem('refresh_token', response.refresh_token);
    }
    
    return response;
  },
  
  async register(data: RegisterRequest): Promise<User> {
    return api.post<User>(API_ENDPOINTS.auth.register, data);
  },
  
  async logout(): Promise<void> {
    try {
      await api.post(API_ENDPOINTS.auth.logout);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },
  
  async getCurrentUser(): Promise<User> {
    return api.get<User>(API_ENDPOINTS.auth.me);
  },
  
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    return api.post<LoginResponse>(API_ENDPOINTS.auth.refresh, { refresh_token: refreshToken });
  },
};

// User Service
export const userService = {
  async getUsers(): Promise<User[]> {
    return api.get<User[]>(API_ENDPOINTS.users.list);
  },
  
  async getUser(id: string): Promise<User> {
    return api.get<User>(API_ENDPOINTS.users.get(id));
  },
  
  async updateUser(id: string, data: Partial<User>): Promise<User> {
    return api.patch<User>(API_ENDPOINTS.users.update(id), data);
  },
  
  async deleteUser(id: string): Promise<void> {
    return api.delete(API_ENDPOINTS.users.delete(id));
  },
  
  async getProfile(): Promise<User> {
    return api.get<User>(API_ENDPOINTS.users.profile);
  },
  
  async updateProfile(data: Partial<User>): Promise<User> {
    return api.patch<User>(API_ENDPOINTS.users.profile, data);
  },
};

// Account Service
export const accountService = {
  async getAccounts(): Promise<Account[]> {
    return api.get<Account[]>(API_ENDPOINTS.accounts.list);
  },
  
  async createAccount(data: Partial<Account>): Promise<Account> {
    return api.post<Account>(API_ENDPOINTS.accounts.create, data);
  },
  
  async getAccount(id: string): Promise<Account> {
    return api.get<Account>(API_ENDPOINTS.accounts.get(id));
  },
  
  async updateAccount(id: string, data: Partial<Account>): Promise<Account> {
    return api.patch<Account>(API_ENDPOINTS.accounts.update(id), data);
  },
  
  async deleteAccount(id: string): Promise<void> {
    return api.delete(API_ENDPOINTS.accounts.delete(id));
  },
  
  async syncAccount(id: string): Promise<{ message: string; transactions_added: number }> {
    return api.post(API_ENDPOINTS.accounts.sync(id));
  },
  
  async getAccountBalance(id: string): Promise<{ balance: number; available: number }> {
    return api.get(API_ENDPOINTS.accounts.balance(id));
  },
};

// Transaction Service
export const transactionService = {
  async getTransactions(params?: {
    account_id?: string;
    category_id?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<Transaction[]> {
    return api.get<Transaction[]>(API_ENDPOINTS.transactions.list, params);
  },
  
  async getTransaction(id: string): Promise<Transaction> {
    return api.get<Transaction>(API_ENDPOINTS.transactions.get(id));
  },
  
  async updateTransaction(id: string, data: Partial<Transaction>): Promise<Transaction> {
    return api.patch<Transaction>(API_ENDPOINTS.transactions.update(id), data);
  },
  
  async categorizeTransaction(id: string, categoryId: string): Promise<Transaction> {
    return api.post<Transaction>(API_ENDPOINTS.transactions.categorize(id), { category_id: categoryId });
  },
  
  async bulkUpdateTransactions(transactions: Partial<Transaction>[]): Promise<Transaction[]> {
    return api.post<Transaction[]>(API_ENDPOINTS.transactions.bulk, { transactions });
  },
  
  async exportTransactions(format: 'csv' | 'excel' | 'pdf'): Promise<Blob> {
    const response = await api.get(API_ENDPOINTS.transactions.export, { 
      params: { format },
      responseType: 'blob',
    });
    return response;
  },
  
  async getTransactionStats(): Promise<{
    total: number;
    categorized: number;
    uncategorized: number;
    by_category: Record<string, number>;
  }> {
    return api.get(API_ENDPOINTS.transactions.stats);
  },
};

// Category Service
export const categoryService = {
  async getCategories(): Promise<Category[]> {
    return api.get<Category[]>(API_ENDPOINTS.categories.list);
  },
  
  async createCategory(data: Partial<Category>): Promise<Category> {
    return api.post<Category>(API_ENDPOINTS.categories.create, data);
  },
  
  async getCategory(id: string): Promise<Category> {
    return api.get<Category>(API_ENDPOINTS.categories.get(id));
  },
  
  async updateCategory(id: string, data: Partial<Category>): Promise<Category> {
    return api.patch<Category>(API_ENDPOINTS.categories.update(id), data);
  },
  
  async deleteCategory(id: string): Promise<void> {
    return api.delete(API_ENDPOINTS.categories.delete(id));
  },
};

// Plaid Service
export const plaidService = {
  async createLinkToken(): Promise<PlaidLinkTokenResponse> {
    return api.post<PlaidLinkTokenResponse>(API_ENDPOINTS.plaid.linkToken);
  },
  
  async exchangePublicToken(data: PlaidExchangeTokenRequest): Promise<{ account_id: string }> {
    return api.post(API_ENDPOINTS.plaid.exchangeToken, data);
  },
  
  async getPlaidAccounts(): Promise<Account[]> {
    return api.get<Account[]>(API_ENDPOINTS.plaid.accounts);
  },
  
  async syncTransactions(accountId: string): Promise<{ added: number; modified: number; removed: number }> {
    return api.post(API_ENDPOINTS.plaid.transactions, { account_id: accountId });
  },
  
  async getBalance(accountId: string): Promise<{ current: number; available: number }> {
    return api.get(API_ENDPOINTS.plaid.balance, { params: { account_id: accountId } });
  },
};

// Machine Learning Service
export const mlService = {
  async categorizeTransaction(transaction: Partial<Transaction>): Promise<MLPrediction> {
    return api.post<MLPrediction>(API_ENDPOINTS.ml.categorize, transaction);
  },
  
  async trainModel(transactions: Transaction[]): Promise<{ accuracy: number; model_id: string }> {
    return api.post(API_ENDPOINTS.ml.train, { transactions });
  },
  
  async predictCategories(transactions: Partial<Transaction>[]): Promise<MLPrediction[]> {
    return api.post<MLPrediction[]>(API_ENDPOINTS.ml.predict, { transactions });
  },
  
  async getInsights(): Promise<{
    spending_trends: any[];
    anomalies: any[];
    predictions: any[];
  }> {
    return api.get(API_ENDPOINTS.ml.insights);
  },
  
  async detectAnomalies(transactions: Transaction[]): Promise<{
    anomalies: Transaction[];
    confidence: number[];
  }> {
    return api.post(API_ENDPOINTS.ml.anomalies, { transactions });
  },
};

// Reports Service
export const reportsService = {
  async getProfitAndLoss(params: {
    start_date: string;
    end_date: string;
    compare_period?: boolean;
  }): Promise<Report> {
    return api.get<Report>(API_ENDPOINTS.reports.pnl, params);
  },
  
  async getBalanceSheet(date: string): Promise<Report> {
    return api.get<Report>(API_ENDPOINTS.reports.balanceSheet, { params: { date } });
  },
  
  async getCashFlow(params: {
    start_date: string;
    end_date: string;
  }): Promise<Report> {
    return api.get<Report>(API_ENDPOINTS.reports.cashFlow, params);
  },
  
  async generateCustomReport(config: any): Promise<Report> {
    return api.post<Report>(API_ENDPOINTS.reports.custom, config);
  },
  
  async exportReport(reportId: string, format: 'pdf' | 'excel' | 'csv'): Promise<Blob> {
    return api.get(API_ENDPOINTS.reports.export, {
      params: { report_id: reportId, format },
      responseType: 'blob',
    });
  },
};

// Settings Service
export const settingsService = {
  async getSettings(): Promise<any> {
    return api.get(API_ENDPOINTS.settings.get);
  },
  
  async updateSettings(settings: any): Promise<any> {
    return api.patch(API_ENDPOINTS.settings.update, settings);
  },
  
  async getPreferences(): Promise<any> {
    return api.get(API_ENDPOINTS.settings.preferences);
  },
  
  async updatePreferences(preferences: any): Promise<any> {
    return api.patch(API_ENDPOINTS.settings.preferences, preferences);
  },
  
  async getNotificationSettings(): Promise<any> {
    return api.get(API_ENDPOINTS.settings.notifications);
  },
  
  async updateNotificationSettings(settings: any): Promise<any> {
    return api.patch(API_ENDPOINTS.settings.notifications, settings);
  },
};

// Health Check Service
export const healthService = {
  async checkHealth(): Promise<{
    status: string;
    timestamp: string;
    environment: string;
    version: string;
    database: boolean;
    redis: boolean;
  }> {
    return api.get(API_ENDPOINTS.health);
  },
};

// Export all services as a single object for convenience
export const apiServices = {
  auth: authService,
  users: userService,
  accounts: accountService,
  transactions: transactionService,
  categories: categoryService,
  plaid: plaidService,
  ml: mlService,
  reports: reportsService,
  settings: settingsService,
  health: healthService,
};

export default apiServices;