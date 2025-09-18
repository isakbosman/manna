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

export interface CategoryStats {
  category: Category
  transaction_count: number
  total_amount: number
  avg_amount: number
  last_used: string | null
  first_used: string | null
  usage_frequency: number // transactions per month
  subcategory_count?: number
}

export interface ImportResult {
  imported_count: number
  updated_count: number
  errors: Array<{ row: number; message: string }>
  warnings: Array<{ row: number; message: string }>
}

export interface TestRulesResult {
  matched_transactions: number
  total_tested: number
  match_rate: number
  sample_matches: Array<{
    transaction_id: string
    description: string
    amount: number
    matched_rules: string[]
  }>
}

export const categoriesApi = {
  // Get all categories
  getCategories: async (): Promise<Category[]> => {
    return api.get('/api/v1/categories')
  },

  // Get category hierarchy
  getCategoryHierarchy: async (): Promise<Category[]> => {
    return api.get('/api/v1/categories?include_hierarchy=true')
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

  // Bulk update categories (for drag-and-drop hierarchy changes)
  bulkUpdateCategories: async (updates: Array<{ id: string; parent_id?: string; sort_order?: number }>): Promise<void> => {
    return api.patch('/api/v1/categories/bulk', { updates })
  },

  // Merge categories
  mergeCategories: async (sourceId: string, targetId: string): Promise<void> => {
    return api.post('/api/v1/categories/merge', { source_id: sourceId, target_id: targetId })
  },

  // Get category usage statistics
  getCategoryStats: async (categoryId?: string): Promise<CategoryStats[]> => {
    const params = categoryId ? `?category_id=${categoryId}` : ''
    return api.get(`/api/v1/categories/stats${params}`)
  },

  // Export categories
  exportCategories: async (format: 'json' | 'csv'): Promise<Blob> => {
    return api.get(`/api/v1/categories/export?format=${format}`, { responseType: 'blob' })
  },

  // Import categories
  importCategories: async (file: File, options?: { merge?: boolean; overwrite?: boolean }): Promise<ImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    if (options?.merge) formData.append('merge', 'true')
    if (options?.overwrite) formData.append('overwrite', 'true')
    return api.post('/api/v1/categories/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Get category rules
  getCategoryRules: async (categoryId: string): Promise<CategoryRule[]> => {
    return api.get(`/api/v1/categories/${categoryId}/rules`)
  },

  // Create category rule
  createCategoryRule: async (categoryId: string, rule: Omit<CategoryRule, 'id' | 'category_id'>): Promise<CategoryRule> => {
    return api.post(`/api/v1/categories/${categoryId}/rules`, rule)
  },

  // Update category rule
  updateCategoryRule: async (categoryId: string, ruleId: string, updates: Partial<CategoryRule>): Promise<CategoryRule> => {
    return api.put(`/api/v1/categories/${categoryId}/rules/${ruleId}`, updates)
  },

  // Delete category rule
  deleteCategoryRule: async (categoryId: string, ruleId: string): Promise<void> => {
    return api.delete(`/api/v1/categories/${categoryId}/rules/${ruleId}`)
  },

  // Test category rules
  testCategoryRules: async (rules: Omit<CategoryRule, 'id' | 'category_id'>[], sampleSize?: number): Promise<TestRulesResult> => {
    return api.post('/api/v1/categories/test-rules', { rules, sample_size: sampleSize })
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