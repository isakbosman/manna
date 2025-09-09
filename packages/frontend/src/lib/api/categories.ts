import { api } from '@/lib/api'

export interface Category {
  id: string
  name: string
  type: 'income' | 'expense' | 'transfer'
  icon?: string
  color?: string
  parent_id?: string
  is_system: boolean
  confidence_threshold?: number
  keywords?: string[]
  rules?: CategoryRule[]
  created_at: string
  updated_at: string
}

export interface CategoryRule {
  id: string
  category_id: string
  field: 'description' | 'merchant' | 'amount'
  operator: 'contains' | 'equals' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than'
  value: string
  priority: number
}

export interface MLCategoryPrediction {
  category_id: string
  confidence: number
  explanation?: string
}

export interface CategorySpending {
  category: Category
  total_amount: number
  transaction_count: number
  avg_amount: number
  percentage_of_total: number
  trend: 'up' | 'down' | 'stable'
}

export const categoriesApi = {
  // Get all categories
  getCategories: async (): Promise<Category[]> => {
    return api.get('/api/v1/categories')
  },

  // Get a specific category
  getCategory: async (id: string): Promise<Category> => {
    return api.get(`/api/v1/categories/${id}`)
  },

  // Create a new category
  createCategory: async (category: Omit<Category, 'id' | 'created_at' | 'updated_at'>): Promise<Category> => {
    return api.post('/api/v1/categories', category)
  },

  // Update a category
  updateCategory: async (id: string, updates: Partial<Category>): Promise<Category> => {
    return api.put(`/api/v1/categories/${id}`, updates)
  },

  // Delete a category
  deleteCategory: async (id: string): Promise<void> => {
    return api.delete(`/api/v1/categories/${id}`)
  },

  // Get category spending analysis
  getCategorySpending: async (filters?: {
    date_from?: string
    date_to?: string
    account_id?: string
  }): Promise<CategorySpending[]> => {
    const params = new URLSearchParams()
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString())
        }
      })
    }
    
    return api.get(`/api/v1/categories/spending?${params.toString()}`)
  },

  // ML categorization
  categorizeTransaction: async (transactionId: string): Promise<MLCategoryPrediction[]> => {
    return api.post('/api/v1/ml/categorize', { transaction_id: transactionId })
  },

  // Provide ML feedback
  provideFeedback: async (transactionId: string, categoryId: string, isCorrect: boolean): Promise<void> => {
    return api.post('/api/v1/ml/feedback', {
      transaction_id: transactionId,
      category_id: categoryId,
      is_correct: isCorrect
    })
  },

  // Bulk categorize transactions
  bulkCategorize: async (transactionIds: string[]): Promise<{
    categorized_count: number
    predictions: Record<string, MLCategoryPrediction[]>
  }> => {
    return api.post('/api/v1/ml/bulk-categorize', { transaction_ids: transactionIds })
  }
}