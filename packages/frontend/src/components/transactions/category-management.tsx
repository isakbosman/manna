import React from 'react'
import {
  PlusIcon,
  EditIcon,
  TrashIcon,
  TagIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  CreditCardIcon,
  SearchIcon
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Modal } from '@/components/ui/modal'
import { CustomSelect } from '@/components/ui/select'
import { Category, categoriesApi, CategorySpending } from '@/lib/api/categories'
import { cn } from '@/lib/utils'

interface CategoryManagementProps {
  categories: Category[]
  onCategoriesChange: () => void
  categorySpending?: CategorySpending[]
  className?: string
}

export function CategoryManagement({
  categories,
  onCategoriesChange,
  categorySpending = [],
  className
}: CategoryManagementProps) {
  const [searchTerm, setSearchTerm] = React.useState('')
  const [showCreateModal, setShowCreateModal] = React.useState(false)
  const [editingCategory, setEditingCategory] = React.useState<Category | null>(null)
  const [viewMode, setViewMode] = React.useState<'grid' | 'spending'>('grid')

  const filteredCategories = categories.filter(category =>
    category.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getCategoryIcon = (type: string) => {
    switch (type) {
      case 'income':
        return <TrendingUpIcon className="h-5 w-5 text-success-600" />
      case 'expense':
        return <TrendingDownIcon className="h-5 w-5 text-error-600" />
      case 'transfer':
        return <CreditCardIcon className="h-5 w-5 text-info-600" />
      default:
        return <TagIcon className="h-5 w-5 text-neutral-600" />
    }
  }

  const getCategoryVariant = (type: string) => {
    switch (type) {
      case 'income':
        return 'success' as const
      case 'expense':
        return 'destructive' as const
      case 'transfer':
        return 'info' as const
      default:
        return 'secondary' as const
    }
  }

  const handleDeleteCategory = async (category: Category) => {
    if (category.is_system) {
      alert('System categories cannot be deleted')
      return
    }

    if (!window.confirm(`Are you sure you want to delete "${category.name}"? This action cannot be undone.`)) {
      return
    }

    try {
      await categoriesApi.deleteCategory(category.id)
      onCategoriesChange()
    } catch (error) {
      console.error('Failed to delete category:', error)
      alert('Failed to delete category')
    }
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(Math.abs(amount))
  }

  return (
    <>
      <div className={cn('space-y-6', className)}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-neutral-900">Category Management</h2>
            <p className="text-neutral-600 mt-1">
              Create and manage categories for your transactions
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <CustomSelect
              options={[
                { value: 'grid', label: 'Grid View' },
                { value: 'spending', label: 'Spending View' }
              ]}
              value={viewMode}
              onChange={(value) => setViewMode(value as 'grid' | 'spending')}
            />
            
            <Button onClick={() => setShowCreateModal(true)}>
              <PlusIcon className="h-4 w-4 mr-1" />
              New Category
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-sm">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
          <Input
            placeholder="Search categories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Categories Display */}
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCategories.map((category) => (
              <Card key={category.id} className="p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {getCategoryIcon(category.type)}
                    <div>
                      <h3 className="font-medium text-neutral-900">{category.name}</h3>
                      <Badge variant={getCategoryVariant(category.type)} className="text-xs mt-1">
                        {category.type}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditingCategory(category)}
                      className="h-6 w-6 p-0"
                    >
                      <EditIcon className="h-3 w-3" />
                    </Button>
                    
                    {!category.is_system && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteCategory(category)}
                        className="h-6 w-6 p-0 text-error-600 hover:text-error-700 hover:bg-error-50"
                      >
                        <TrashIcon className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
                
                {category.is_system && (
                  <Badge variant="outline" className="text-xs">
                    System Category
                  </Badge>
                )}
                
                {category.keywords && category.keywords.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-neutral-600 mb-1">Keywords:</p>
                    <div className="flex flex-wrap gap-1">
                      {category.keywords.slice(0, 3).map((keyword, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                      {category.keywords.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{category.keywords.length - 3} more
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {categorySpending
              .filter(cs => cs.category.name.toLowerCase().includes(searchTerm.toLowerCase()))
              .map((categorySpend) => (
                <Card key={categorySpend.category.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getCategoryIcon(categorySpend.category.type)}
                      <div>
                        <h3 className="font-medium text-neutral-900">
                          {categorySpend.category.name}
                        </h3>
                        <p className="text-sm text-neutral-600">
                          {categorySpend.transaction_count} transactions
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className={cn(
                        "text-lg font-semibold",
                        categorySpend.category.type === 'income' ? "text-success-600" : "text-error-600"
                      )}>
                        {formatAmount(categorySpend.total_amount)}
                      </p>
                      <p className="text-sm text-neutral-600">
                        {categorySpend.percentage_of_total.toFixed(1)}% of total
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-2 flex items-center gap-2">
                    <Badge variant={getCategoryVariant(categorySpend.category.type)} className="text-xs">
                      {categorySpend.category.type}
                    </Badge>
                    
                    {categorySpend.trend && (
                      <Badge 
                        variant={categorySpend.trend === 'up' ? 'warning' : 
                                categorySpend.trend === 'down' ? 'success' : 'outline'}
                        className="text-xs"
                      >
                        {categorySpend.trend === 'up' ? 'Trending Up' :
                         categorySpend.trend === 'down' ? 'Trending Down' : 'Stable'}
                      </Badge>
                    )}
                  </div>
                </Card>
              ))
            }
          </div>
        )}

        {filteredCategories.length === 0 && (
          <div className="text-center py-8">
            <TagIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">No categories found</h3>
            <p className="text-neutral-600 mb-4">
              {searchTerm ? 'Try adjusting your search term.' : 'Create your first category to get started.'}
            </p>
            {!searchTerm && (
              <Button onClick={() => setShowCreateModal(true)}>
                <PlusIcon className="h-4 w-4 mr-1" />
                Create Category
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Create/Edit Category Modal */}
      <CategoryFormModal
        isOpen={showCreateModal || !!editingCategory}
        onClose={() => {
          setShowCreateModal(false)
          setEditingCategory(null)
        }}
        category={editingCategory}
        onSuccess={() => {
          setShowCreateModal(false)
          setEditingCategory(null)
          onCategoriesChange()
        }}
      />
    </>
  )
}

// Category Form Modal Component
interface CategoryFormModalProps {
  isOpen: boolean
  onClose: () => void
  category?: Category | null
  onSuccess: () => void
}

function CategoryFormModal({ isOpen, onClose, category, onSuccess }: CategoryFormModalProps) {
  const [formData, setFormData] = React.useState({
    name: '',
    type: 'expense' as const,
    icon: '',
    color: '#6B7280',
    keywords: [] as string[]
  })
  const [keywordInput, setKeywordInput] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)

  React.useEffect(() => {
    if (category) {
      setFormData({
        name: category.name,
        type: category.type,
        icon: category.icon || '',
        color: category.color || '#6B7280',
        keywords: category.keywords || []
      })
    } else {
      setFormData({
        name: '',
        type: 'expense',
        icon: '',
        color: '#6B7280',
        keywords: []
      })
    }
  }, [category, isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) return

    try {
      setIsLoading(true)
      if (category) {
        await categoriesApi.updateCategory(category.id, formData)
      } else {
        await categoriesApi.createCategory({
          ...formData,
          is_system: false
        })
      }
      onSuccess()
    } catch (error) {
      console.error('Failed to save category:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const addKeyword = () => {
    if (keywordInput.trim() && !formData.keywords.includes(keywordInput.trim())) {
      setFormData(prev => ({
        ...prev,
        keywords: [...prev.keywords, keywordInput.trim()]
      }))
      setKeywordInput('')
    }
  }

  const removeKeyword = (keyword: string) => {
    setFormData(prev => ({
      ...prev,
      keywords: prev.keywords.filter(k => k !== keyword)
    }))
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={category ? 'Edit Category' : 'Create New Category'}
      description="Categories help organize your transactions for better financial insights"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Category Name *
          </label>
          <Input
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Enter category name"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Type *
          </label>
          <CustomSelect
            options={[
              { 
                value: 'income', 
                label: 'Income', 
                icon: <TrendingUpIcon className="h-4 w-4 text-success-600" /> 
              },
              { 
                value: 'expense', 
                label: 'Expense', 
                icon: <TrendingDownIcon className="h-4 w-4 text-error-600" /> 
              },
              { 
                value: 'transfer', 
                label: 'Transfer', 
                icon: <CreditCardIcon className="h-4 w-4 text-info-600" /> 
              },
            ]}
            value={formData.type}
            onChange={(value) => setFormData(prev => ({ ...prev, type: value as any }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Keywords (for auto-categorization)
          </label>
          <div className="flex gap-2 mb-2">
            <Input
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              placeholder="Add keyword"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  addKeyword()
                }
              }}
            />
            <Button type="button" onClick={addKeyword} variant="outline">
              Add
            </Button>
          </div>
          
          <div className="flex flex-wrap gap-1">
            {formData.keywords.map((keyword) => (
              <Badge key={keyword} variant="outline" className="text-xs flex items-center gap-1">
                {keyword}
                <button
                  type="button"
                  onClick={() => removeKeyword(keyword)}
                  className="ml-1 hover:bg-neutral-200 rounded"
                >
                  ×
                </button>
              </Badge>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={isLoading}>
            {category ? 'Update' : 'Create'} Category
          </Button>
        </div>
      </form>
    </Modal>
  )
}