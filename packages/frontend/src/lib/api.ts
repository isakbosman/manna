import axios, { 
  AxiosInstance, 
  AxiosRequestConfig, 
  AxiosResponse, 
  AxiosError 
} from 'axios'
import Cookies from 'js-cookie'

// Types for API responses
export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: number
}

export interface ApiError {
  message: string
  status: number
  code?: string
  details?: any
}

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_TIMEOUT = 30000 // 30 seconds

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - DISABLED for local development
apiClient.interceptors.request.use(
  (config) => {
    // No auth token needed for local development
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling - SIMPLIFIED for local development
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    // No auth refresh needed for local development

    // Handle other errors
    const apiError: ApiError = {
      message: error.response?.data?.message || error.message || 'An error occurred',
      status: error.response?.status || 500,
      code: error.response?.data?.code,
      details: error.response?.data?.details,
    }

    return Promise.reject(apiError)
  }
)

// Generic API methods
export const api = {
  // GET request
  get: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.get<T>(url, config)
    return response.data
  },

  // POST request
  post: async <T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    const response = await apiClient.post<T>(url, data, config)
    return response.data
  },

  // PUT request
  put: async <T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    const response = await apiClient.put<T>(url, data, config)
    return response.data
  },

  // PATCH request
  patch: async <T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    const response = await apiClient.patch<T>(url, data, config)
    return response.data
  },

  // DELETE request
  delete: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const response = await apiClient.delete<T>(url, config)
    return response.data
  },

  // Upload file
  upload: async <T = any>(
    url: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<T> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(progress)
        }
      },
    })
    
    return response.data.data
  },

  // Download file
  download: async (
    url: string, 
    filename?: string
  ): Promise<void> => {
    const response = await apiClient.get(url, {
      responseType: 'blob',
    })

    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  },
}

// Authentication API methods
export const authApi = {
  login: async (credentials: { 
    email: string
    password: string
    rememberMe?: boolean 
  }) => {
    const response = await api.post('/api/v1/auth/login', credentials)
    
    // Store tokens in cookies with appropriate expiration
    const tokenExpiry = credentials.rememberMe ? 30 : 1 // 30 days or 1 day
    const refreshExpiry = credentials.rememberMe ? 90 : 7 // 90 days or 7 days
    
    if (response.access_token) {
      Cookies.set('access_token', response.access_token, { expires: tokenExpiry })
    }
    if (response.refresh_token) {
      Cookies.set('refresh_token', response.refresh_token, { expires: refreshExpiry })
    }
    
    return response
  },

  logout: async () => {
    try {
      await api.post('/api/v1/auth/logout')
    } catch (error) {
      // Even if logout fails on server, clear local tokens
      console.warn('Logout request failed:', error)
    } finally {
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
    }
  },

  register: async (userData: {
    email: string
    password: string
    firstName: string
    lastName: string
  }) => {
    return api.post('/api/v1/auth/register', userData)
  },

  forgotPassword: async (email: string) => {
    return api.post('/api/v1/auth/forgot-password', { email })
  },

  resetPassword: async (token: string, newPassword: string) => {
    return api.post('/api/v1/auth/reset-password', {
      token,
      password: newPassword,
    })
  },

  verifyEmail: async (token: string) => {
    return api.post('/api/v1/auth/verify-email', { token })
  },

  resendVerification: async (email: string) => {
    return api.post('/api/v1/auth/resend-verification', { email })
  },

  getCurrentUser: async () => {
    return api.get('/api/v1/users/me')
  },

  refreshToken: async () => {
    const refreshToken = Cookies.get('refresh_token')
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }
    
    const response = await api.post('/api/v1/auth/refresh', { 
      refresh_token: refreshToken 
    })
    
    // Store new tokens
    if (response.access_token) {
      Cookies.set('access_token', response.access_token, { expires: 1 })
    }
    if (response.refresh_token) {
      Cookies.set('refresh_token', response.refresh_token, { expires: 7 })
    }
    
    return response
  },
}

// Utility functions
export const getAuthToken = (): string | undefined => {
  return Cookies.get('access_token')
}

export const isAuthenticated = (): boolean => {
  return !!getAuthToken()
}

export const clearAuthTokens = (): void => {
  Cookies.remove('access_token')
  Cookies.remove('refresh_token')
}

export default api