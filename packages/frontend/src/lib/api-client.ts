/**
 * API Client Configuration
 * Central configuration for all API calls from the frontend to backend
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// API base URL configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Send cookies with requests
});

// Request interceptor to add authentication token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage or cookie
    const token = localStorage.getItem('access_token');
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}${API_PREFIX}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// API endpoint definitions
export const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    refresh: '/auth/refresh',
    logout: '/auth/logout',
    me: '/auth/me',
  },
  
  // Users
  users: {
    list: '/users',
    get: (id: string) => `/users/${id}`,
    update: (id: string) => `/users/${id}`,
    delete: (id: string) => `/users/${id}`,
    profile: '/users/profile',
  },
  
  // Accounts
  accounts: {
    list: '/accounts',
    create: '/accounts',
    get: (id: string) => `/accounts/${id}`,
    update: (id: string) => `/accounts/${id}`,
    delete: (id: string) => `/accounts/${id}`,
    sync: (id: string) => `/accounts/${id}/sync`,
    balance: (id: string) => `/accounts/${id}/balance`,
  },
  
  // Transactions
  transactions: {
    list: '/transactions',
    get: (id: string) => `/transactions/${id}`,
    update: (id: string) => `/transactions/${id}`,
    categorize: (id: string) => `/transactions/${id}/categorize`,
    bulk: '/transactions/bulk',
    export: '/transactions/export',
    stats: '/transactions/stats',
  },
  
  // Categories
  categories: {
    list: '/categories',
    create: '/categories',
    get: (id: string) => `/categories/${id}`,
    update: (id: string) => `/categories/${id}`,
    delete: (id: string) => `/categories/${id}`,
  },
  
  // Plaid
  plaid: {
    linkToken: '/plaid/link-token',
    exchangeToken: '/plaid/exchange-token',
    accounts: '/plaid/accounts',
    transactions: '/plaid/transactions',
    balance: '/plaid/balance',
    webhooks: '/plaid/webhooks',
  },
  
  // Machine Learning
  ml: {
    categorize: '/ml/categorize',
    train: '/ml/train',
    predict: '/ml/predict',
    insights: '/ml/insights',
    anomalies: '/ml/anomalies',
  },
  
  // Reports
  reports: {
    pnl: '/reports/pnl',
    balanceSheet: '/reports/balance-sheet',
    cashFlow: '/reports/cash-flow',
    custom: '/reports/custom',
    export: '/reports/export',
  },
  
  // Settings
  settings: {
    get: '/settings',
    update: '/settings',
    preferences: '/settings/preferences',
    notifications: '/settings/notifications',
  },
  
  // Health
  health: '/health',
};

// Helper functions for common API operations
export const api = {
  // GET request
  get: async <T = any>(endpoint: string, params?: any) => {
    const response = await apiClient.get<T>(endpoint, { params });
    return response.data;
  },
  
  // POST request
  post: async <T = any>(endpoint: string, data?: any, config?: any) => {
    const response = await apiClient.post<T>(endpoint, data, config);
    return response.data;
  },
  
  // PUT request
  put: async <T = any>(endpoint: string, data?: any) => {
    const response = await apiClient.put<T>(endpoint, data);
    return response.data;
  },
  
  // PATCH request
  patch: async <T = any>(endpoint: string, data?: any) => {
    const response = await apiClient.patch<T>(endpoint, data);
    return response.data;
  },
  
  // DELETE request
  delete: async <T = any>(endpoint: string) => {
    const response = await apiClient.delete<T>(endpoint);
    return response.data;
  },
  
  // File upload
  upload: async <T = any>(endpoint: string, file: File, fieldName = 'file') => {
    const formData = new FormData();
    formData.append(fieldName, file);
    
    const response = await apiClient.post<T>(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// WebSocket connection for real-time updates
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectInterval = 5000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, Set<(data: any) => void>> = new Map();
  
  constructor(private url: string = `ws://localhost:8000/ws`) {}
  
  connect(token?: string) {
    const wsUrl = token ? `${this.url}?token=${token}` : this.url;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };
    
    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const { type, data } = message;
        
        // Notify all handlers for this message type
        const handlers = this.messageHandlers.get(type);
        if (handlers) {
          handlers.forEach(handler => handler(data));
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect();
    };
  }
  
  reconnect() {
    if (this.reconnectTimer) return;
    
    this.reconnectTimer = setTimeout(() => {
      console.log('Attempting to reconnect WebSocket...');
      this.connect();
    }, this.reconnectInterval);
  }
  
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  send(type: string, data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
  
  on(type: string, handler: (data: any) => void) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);
  }
  
  off(type: string, handler: (data: any) => void) {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      handlers.delete(handler);
    }
  }
}

// Export singleton WebSocket client
export const wsClient = new WebSocketClient();

export default apiClient;