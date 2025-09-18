import React from 'react'
import {
  PlusIcon,
  EditIcon,
  TrashIcon,
  TagIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  CreditCardIcon,
  SearchIcon,
  DownloadIcon,
  UploadIcon,
  SettingsIcon,
  BarChart3Icon,
  FilterIcon,
  GripVerticalIcon,
  FolderIcon,
  FolderOpenIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  MergeIcon,
  CopyIcon,
  EyeIcon,
  RulerIcon,
  PaletteIcon,
  SmileIcon,
  TestTubeIcon,
  InfoIcon,
  AlertTriangleIcon,
  CheckIcon,
  XIcon
} from 'lucide-react'
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from '@dnd-kit/core'
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Button } from '../ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Input } from '../ui/input'
import { Modal } from '../ui/modal'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Checkbox } from '../ui/checkbox'
import { Label } from '../ui/label'
import { Tooltip } from '../ui/tooltip'
import { ScrollArea } from '../ui/scroll-area'
import {
  Category,
  categoriesApi,
  CategorySpending,
  CategoryStats,
  CategoryRule,
  ImportResult,
  TestRulesResult
} from '../../lib/api/categories'
import { cn, formatCurrency } from '../../lib/utils'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSuccessToast, useErrorToast } from '../ui/toast'

interface CategoryManagementProps {
  isOpen: boolean
  onClose: () => void
  className?: string
}

interface CategoryWithChildren extends Category {
  children?: CategoryWithChildren[]
  level?: number
  isExpanded?: boolean
}

interface CategoryFormData {
  name: string
  type: 'income' | 'expense' | 'transfer'
  icon: string
  color: string
  parent_id?: string
  keywords: string[]
  confidence_threshold?: number
}

interface RuleFormData {
  field: 'description' | 'merchant' | 'amount'
  operator: 'contains' | 'equals' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than'
  value: string
  priority: number
}

const CATEGORY_ICONS = [
  '🏠', '🚗', '🍔', '💊', '📚', '🎬', '✈️', '👕', '⚡', '📱',
  '🎵', '🏋️', '🎨', '🐕', '🌱', '🔧', '🎁', '☕', '🏦', '💼'
]

const CATEGORY_COLORS = [
  '#EF4444', '#F97316', '#EAB308', '#22C55E', '#06B6D4',
  '#3B82F6', '#8B5CF6', '#EC4899', '#F43F5E', '#84CC16',
  '#10B981', '#14B8A6', '#6366F1', '#8B5CF6', '#A855F7'
]

export function CategoryManagement({ isOpen, onClose, className }: CategoryManagementProps) {
  const queryClient = useQueryClient()
  const successToast = useSuccessToast()
  const errorToast = useErrorToast()

  // State
  const [searchTerm, setSearchTerm] = React.useState('')
  const [showCreateModal, setShowCreateModal] = React.useState(false)
  const [editingCategory, setEditingCategory] = React.useState<Category | null>(null)
  const [viewMode, setViewMode] = React.useState<'hierarchy' | 'grid' | 'stats' | 'rules'>('hierarchy')
  const [filterType, setFilterType] = React.useState<'all' | 'system' | 'custom'>('all')
  const [selectedCategories, setSelectedCategories] = React.useState<string[]>([])
  const [expandedCategories, setExpandedCategories] = React.useState<Set<string>>(new Set())
  const [showRulesModal, setShowRulesModal] = React.useState(false)
  const [rulesCategory, setRulesCategory] = React.useState<Category | null>(null)
  const [showImportModal, setShowImportModal] = React.useState(false)
  const [showMergeModal, setShowMergeModal] = React.useState(false)
  const [mergeSource, setMergeSource] = React.useState<Category | null>(null)
  const [showPreviewModal, setShowPreviewModal] = React.useState(false)
  const [previewCategory, setPreviewCategory] = React.useState<Category | null>(null)

  // Queries
  const { data: categories = [], isLoading: categoriesLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.getCategories
  })

  const { data: categoryStats = [], isLoading: statsLoading } = useQuery({
    queryKey: ['category-stats'],
    queryFn: () => categoriesApi.getCategoryStats(),
    enabled: viewMode === 'stats'
  })

  const { data: categorySpending = [], isLoading: spendingLoading } = useQuery({
    queryKey: ['category-spending'],
    queryFn: () => categoriesApi.getCategorySpending(),
    enabled: viewMode === 'stats'
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: categoriesApi.createCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['category-stats'] })
      successToast('Category Created', 'Category created successfully')
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      errorToast('Create Failed', error.message || 'Failed to create category')
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Category> }) =>
      categoriesApi.updateCategory(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['category-stats'] })
      successToast('Category Updated', 'Category updated successfully')
      setEditingCategory(null)
    },
    onError: (error: any) => {
      errorToast('Update Failed', error.message || 'Failed to update category')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: categoriesApi.deleteCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['category-stats'] })
      successToast('Category Deleted', 'Category deleted successfully')
    },
    onError: (error: any) => {
      errorToast('Delete Failed', error.message || 'Failed to delete category')
    }
  })

  const bulkUpdateMutation = useMutation({
    mutationFn: categoriesApi.bulkUpdateCategories,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      successToast('Categories Updated', 'Category hierarchy updated successfully')
    },
    onError: (error: any) => {
      errorToast('Update Failed', error.message || 'Failed to update categories')
    }
  })

  const mergeMutation = useMutation({
    mutationFn: ({ sourceId, targetId }: { sourceId: string; targetId: string }) =>
      categoriesApi.mergeCategories(sourceId, targetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['category-stats'] })
      successToast('Categories Merged', 'Categories merged successfully')
      setShowMergeModal(false)
      setMergeSource(null)
    },
    onError: (error: any) => {
      errorToast('Merge Failed', error.message || 'Failed to merge categories')
    }
  })

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // Helper functions
  const buildCategoryHierarchy = (categories: Category[]): CategoryWithChildren[] => {
    const categoryMap = new Map<string, CategoryWithChildren>()
    const rootCategories: CategoryWithChildren[] = []

    // First pass: create map of all categories
    categories.forEach(category => {
      categoryMap.set(category.id, {
        ...category,
        children: [],
        level: 0,
        isExpanded: expandedCategories.has(category.id)
      })
    })

    // Second pass: build hierarchy
    categories.forEach(category => {
      const categoryWithChildren = categoryMap.get(category.id)!
      if (category.parent_id && categoryMap.has(category.parent_id)) {
        const parent = categoryMap.get(category.parent_id)!
        parent.children!.push(categoryWithChildren)
        categoryWithChildren.level = (parent.level || 0) + 1
      } else {
        rootCategories.push(categoryWithChildren)
      }
    })

    return rootCategories
  }

  const flattenHierarchy = (categories: CategoryWithChildren[]): CategoryWithChildren[] => {
    const result: CategoryWithChildren[] = []

    const addCategory = (category: CategoryWithChildren) => {
      result.push(category)
      if (category.isExpanded && category.children) {
        category.children.forEach(addCategory)
      }
    }

    categories.forEach(addCategory)
    return result
  }

  const filteredCategories = React.useMemo(() => {
    let filtered = categories.filter(category => {
      const matchesSearch = category.name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesFilter = filterType === 'all' ||
        (filterType === 'system' && category.is_system) ||
        (filterType === 'custom' && !category.is_system)
      return matchesSearch && matchesFilter
    })

    if (viewMode === 'hierarchy') {
      const hierarchy = buildCategoryHierarchy(filtered)
      return flattenHierarchy(hierarchy)
    }

    return filtered.map(cat => ({ ...cat, level: 0 }))
  }, [categories, searchTerm, filterType, viewMode, expandedCategories])

  const toggleCategoryExpansion = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId)
    } else {
      newExpanded.add(categoryId)
    }
    setExpandedCategories(newExpanded)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (!over || active.id === over.id) return

    const oldIndex = filteredCategories.findIndex(cat => cat.id === active.id)
    const newIndex = filteredCategories.findIndex(cat => cat.id === over.id)

    if (oldIndex === -1 || newIndex === -1) return

    const reorderedCategories = arrayMove(filteredCategories, oldIndex, newIndex)

    // Create bulk update payload
    const updates = reorderedCategories.map((cat, index) => ({
      id: (cat as CategoryWithChildren).id,
      sort_order: index
    }))

    bulkUpdateMutation.mutate(updates)
  }

  const handleBulkDelete = async () => {
    if (selectedCategories.length === 0) return

    const systemCategories = selectedCategories.filter(id =>
      categories.find(cat => cat.id === id)?.is_system
    )

    if (systemCategories.length > 0) {
      errorToast('Cannot Delete', 'System categories cannot be deleted')
      return
    }

    if (!confirm(`Delete ${selectedCategories.length} categories? This cannot be undone.`)) {
      return
    }

    try {
      await Promise.all(selectedCategories.map(id => categoriesApi.deleteCategory(id)))
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      successToast('Categories Deleted', `${selectedCategories.length} categories deleted`)
      setSelectedCategories([])
    } catch (error: any) {
      errorToast('Delete Failed', error.message || 'Failed to delete categories')
    }
  }

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await categoriesApi.exportCategories(format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `categories.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      successToast('Export Complete', `Categories exported as ${format.toUpperCase()}`)
    } catch (error: any) {
      errorToast('Export Failed', error.message || 'Failed to export categories')
    }
  }

  const handleDeleteCategory = async (category: Category) => {
    if (category.is_system) {
      errorToast('Cannot Delete', 'System categories cannot be deleted')
      return
    }

    if (!window.confirm(`Are you sure you want to delete "${category.name}"? This action cannot be undone.`)) {
      return
    }

    deleteMutation.mutate(category.id)
  }

  const handleCopyCategory = async (category: Category) => {
    const newCategory = {
      ...category,
      name: `${category.name} (Copy)`,
      is_system: false,
      parent_id: category.parent_id
    }
    delete (newCategory as any).id
    delete (newCategory as any).created_at
    delete (newCategory as any).updated_at

    createMutation.mutate(newCategory)
  }

  const handleMergeCategory = (sourceCategory: Category) => {
    setMergeSource(sourceCategory)
    setShowMergeModal(true)
  }

  const handlePreviewCategory = (category: Category) => {
    setPreviewCategory(category)
    setShowPreviewModal(true)
  }

  if (!isOpen) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Category Management"
      description="Create and manage categories for your transactions"
      size="xl"
      className={className}
    >
      <div className="space-y-6">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Select value={viewMode} onValueChange={(value) => setViewMode(value as any)}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hierarchy">
                  <div className="flex items-center gap-2">
                    <FolderIcon className="h-4 w-4" />
                    Hierarchy
                  </div>
                </SelectItem>
                <SelectItem value="grid">
                  <div className="flex items-center gap-2">
                    <TagIcon className="h-4 w-4" />
                    Grid
                  </div>
                </SelectItem>
                <SelectItem value="stats">
                  <div className="flex items-center gap-2">
                    <BarChart3Icon className="h-4 w-4" />
                    Statistics
                  </div>
                </SelectItem>
                <SelectItem value="rules">
                  <div className="flex items-center gap-2">
                    <RulerIcon className="h-4 w-4" />
                    Rules
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>

            <Select value={filterType} onValueChange={(value) => setFilterType(value as any)}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="system">System</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('csv')}
            >
              <DownloadIcon className="h-4 w-4 mr-1" />
              Export
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowImportModal(true)}
            >
              <UploadIcon className="h-4 w-4 mr-1" />
              Import
            </Button>

            <Button
              onClick={() => setShowCreateModal(true)}
              size="sm"
            >
              <PlusIcon className="h-4 w-4 mr-1" />
              New Category
            </Button>
          </div>
        </div>

        {/* Search and Bulk Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="relative max-w-sm">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
            <Input
              placeholder="Search categories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {selectedCategories.length > 0 && (
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {selectedCategories.length} selected
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={handleBulkDelete}
                disabled={deleteMutation.isPending}
              >
                <TrashIcon className="h-4 w-4 mr-1" />
                Delete Selected
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedCategories([])}
              >
                Clear
              </Button>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="h-[600px] overflow-hidden">
          <ScrollArea className="h-full">
            {viewMode === 'hierarchy' && (
              <HierarchyView
                categories={filteredCategories}
                selectedCategories={selectedCategories}
                onSelectionChange={setSelectedCategories}
                onEdit={setEditingCategory}
                onDelete={handleDeleteCategory}
                onCopy={handleCopyCategory}
                onMerge={handleMergeCategory}
                onPreview={handlePreviewCategory}
                onToggleExpand={toggleCategoryExpansion}
                onDragEnd={handleDragEnd}
                isLoading={categoriesLoading}
              />
            )}

            {viewMode === 'grid' && (
              <GridView
                categories={filteredCategories}
                selectedCategories={selectedCategories}
                onSelectionChange={setSelectedCategories}
                onEdit={setEditingCategory}
                onDelete={handleDeleteCategory}
                onCopy={handleCopyCategory}
                onMerge={handleMergeCategory}
                onPreview={handlePreviewCategory}
                isLoading={categoriesLoading}
              />
            )}

            {viewMode === 'stats' && (
              <StatsView
                categoryStats={categoryStats}
                categorySpending={categorySpending}
                searchTerm={searchTerm}
                isLoading={statsLoading || spendingLoading}
              />
            )}

            {viewMode === 'rules' && (
              <RulesView
                categories={filteredCategories}
                onManageRules={(category) => {
                  setRulesCategory(category)
                  setShowRulesModal(true)
                }}
                isLoading={categoriesLoading}
              />
            )}
          </ScrollArea>
        </div>

        {filteredCategories.length === 0 && !categoriesLoading && (
          <div className="text-center py-12">
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

      {/* Modals */}
      <CategoryFormModal
        isOpen={showCreateModal || !!editingCategory}
        onClose={() => {
          setShowCreateModal(false)
          setEditingCategory(null)
        }}
        category={editingCategory}
        categories={categories}
        onSubmit={(data) => {
          if (editingCategory) {
            updateMutation.mutate({ id: editingCategory.id, updates: data })
          } else {
            createMutation.mutate({ ...data, is_system: false })
          }
        }}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      <CategoryRulesModal
        isOpen={showRulesModal}
        onClose={() => {
          setShowRulesModal(false)
          setRulesCategory(null)
        }}
        category={rulesCategory}
      />

      <ImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImport={async (file, options) => {
          try {
            const result = await categoriesApi.importCategories(file, options)
            queryClient.invalidateQueries({ queryKey: ['categories'] })
            successToast('Import Complete', `Imported ${result.imported_count} categories`)
            setShowImportModal(false)
          } catch (error: any) {
            errorToast('Import Failed', error.message || 'Failed to import categories')
          }
        }}
      />

      <MergeModal
        isOpen={showMergeModal}
        onClose={() => {
          setShowMergeModal(false)
          setMergeSource(null)
        }}
        sourceCategory={mergeSource}
        categories={categories.filter(cat => cat.id !== mergeSource?.id)}
        onMerge={(targetId) => {
          if (mergeSource) {
            mergeMutation.mutate({ sourceId: mergeSource.id, targetId })
          }
        }}
        isLoading={mergeMutation.isPending}
      />

      <PreviewModal
        isOpen={showPreviewModal}
        onClose={() => {
          setShowPreviewModal(false)
          setPreviewCategory(null)
        }}
        category={previewCategory}
      />
    </Modal>
  )
}

// Sortable Category Item Component
interface SortableCategoryItemProps {
  category: CategoryWithChildren
  isSelected: boolean
  onSelect: (id: string, selected: boolean) => void
  onEdit: (category: Category) => void
  onDelete: (category: Category) => void
  onCopy: (category: Category) => void
  onMerge: (category: Category) => void
  onPreview: (category: Category) => void
  onToggleExpand?: (id: string) => void
}

function SortableCategoryItem({
  category,
  isSelected,
  onSelect,
  onEdit,
  onDelete,
  onCopy,
  onMerge,
  onPreview,
  onToggleExpand
}: SortableCategoryItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: category.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const hasChildren = category.children && category.children.length > 0
  const paddingLeft = (category.level || 0) * 24

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border transition-all',
        isSelected ? 'border-primary-500 bg-primary-50' : 'border-neutral-200 hover:border-neutral-300'
      )}
    >
      <div className="flex items-center gap-2" style={{ paddingLeft }}>
        <Checkbox
          checked={isSelected}
          onChange={(e) => onSelect(category.id, e.target.checked)}
        />

        <div {...attributes} {...listeners} className="cursor-grab hover:cursor-grabbing">
          <GripVerticalIcon className="h-4 w-4 text-neutral-400" />
        </div>

        {hasChildren && onToggleExpand && (
          <button
            onClick={() => onToggleExpand(category.id)}
            className="p-1 hover:bg-neutral-100 rounded"
          >
            {category.isExpanded ? (
              <ChevronDownIcon className="h-4 w-4" />
            ) : (
              <ChevronRightIcon className="h-4 w-4" />
            )}
          </button>
        )}

        <div
          className="w-6 h-6 rounded flex items-center justify-center text-sm"
          style={{ backgroundColor: category.color || '#6B7280' }}
        >
          {category.icon || getCategoryIcon(category.type)}
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-neutral-900 truncate">{category.name}</h3>
          <Badge variant={getCategoryVariant(category.type)} className="text-xs">
            {category.type}
          </Badge>
          {category.is_system && (
            <Badge variant="outline" className="text-xs">
              System
            </Badge>
          )}
        </div>

        {category.keywords && category.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {category.keywords.slice(0, 3).map((keyword) => (
              <Badge key={keyword} variant="outline" className="text-xs">
                {keyword}
              </Badge>
            ))}
            {category.keywords.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{category.keywords.length - 3} more
              </Badge>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1">
        <Tooltip content="Preview transactions">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPreview(category)}
            className="h-8 w-8 p-0"
          >
            <EyeIcon className="h-4 w-4" />
          </Button>
        </Tooltip>

        <Tooltip content="Copy category">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onCopy(category)}
            className="h-8 w-8 p-0"
          >
            <CopyIcon className="h-4 w-4" />
          </Button>
        </Tooltip>

        <Tooltip content="Edit category">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(category)}
            className="h-8 w-8 p-0"
          >
            <EditIcon className="h-4 w-4" />
          </Button>
        </Tooltip>

        {!category.is_system && (
          <>
            <Tooltip content="Merge category">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onMerge(category)}
                className="h-8 w-8 p-0"
              >
                <MergeIcon className="h-4 w-4" />
              </Button>
            </Tooltip>

            <Tooltip content="Delete category">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(category)}
                className="h-8 w-8 p-0 text-error-600 hover:text-error-700 hover:bg-error-50"
              >
                <TrashIcon className="h-4 w-4" />
              </Button>
            </Tooltip>
          </>
        )}
      </div>
    </div>
  )
}

// Category Form Modal Component
interface CategoryFormModalProps {
  isOpen: boolean
  onClose: () => void
  category?: Category | null
  categories: Category[]
  onSubmit: (data: CategoryFormData) => void
  isLoading: boolean
}

function CategoryFormModal({ isOpen, onClose, category, categories, onSubmit, isLoading }: CategoryFormModalProps) {
  const [formData, setFormData] = React.useState<CategoryFormData>({
    name: '',
    type: 'expense',
    icon: '',
    color: '#6B7280',
    keywords: [],
    confidence_threshold: 0.8
  })
  const [keywordInput, setKeywordInput] = React.useState('')
  const [showIconPicker, setShowIconPicker] = React.useState(false)
  const [showColorPicker, setShowColorPicker] = React.useState(false)

  React.useEffect(() => {
    if (category) {
      setFormData({
        name: category.name,
        type: category.type,
        icon: category.icon || '',
        color: category.color || '#6B7280',
        parent_id: category.parent_id,
        keywords: category.keywords || [],
        confidence_threshold: category.confidence_threshold || 0.8
      })
    } else {
      setFormData({
        name: '',
        type: 'expense',
        icon: '',
        color: '#6B7280',
        keywords: [],
        confidence_threshold: 0.8
      })
    }
  }, [category, isOpen])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) return
    onSubmit(formData)
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

  const parentCategories = categories.filter(cat =>
    cat.id !== category?.id && !cat.parent_id && cat.type === formData.type
  )

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={category ? 'Edit Category' : 'Create New Category'}
      description="Categories help organize your transactions for better financial insights"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="name">Category Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter category name"
              required
            />
          </div>

          <div>
            <Label htmlFor="type">Type *</Label>
            <Select value={formData.type} onValueChange={(value) => setFormData(prev => ({ ...prev, type: value as any }))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="income">
                  <div className="flex items-center gap-2">
                    <TrendingUpIcon className="h-4 w-4 text-success-600" />
                    Income
                  </div>
                </SelectItem>
                <SelectItem value="expense">
                  <div className="flex items-center gap-2">
                    <TrendingDownIcon className="h-4 w-4 text-error-600" />
                    Expense
                  </div>
                </SelectItem>
                <SelectItem value="transfer">
                  <div className="flex items-center gap-2">
                    <CreditCardIcon className="h-4 w-4 text-info-600" />
                    Transfer
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {parentCategories.length > 0 && (
          <div>
            <Label htmlFor="parent">Parent Category</Label>
            <Select
              value={formData.parent_id || 'none'}
              onValueChange={(value) => setFormData(prev => ({ ...prev, parent_id: value === 'none' ? undefined : value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select parent category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No parent (root category)</SelectItem>
                {parentCategories.map(cat => (
                  <SelectItem key={cat.id} value={cat.id}>
                    <div className="flex items-center gap-2">
                      <span className="text-sm" style={{ color: cat.color }}>
                        {cat.icon || getCategoryIcon(cat.type)}
                      </span>
                      {cat.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Icon</Label>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowIconPicker(!showIconPicker)}
                className="w-12 h-12 p-0"
              >
                {formData.icon ? (
                  <span className="text-lg">{formData.icon}</span>
                ) : (
                  <SmileIcon className="h-5 w-5" />
                )}
              </Button>
              {showIconPicker && (
                <div className="absolute z-10 mt-2 p-3 bg-white border rounded-lg shadow-lg grid grid-cols-5 gap-2">
                  {CATEGORY_ICONS.map(icon => (
                    <button
                      key={icon}
                      type="button"
                      onClick={() => {
                        setFormData(prev => ({ ...prev, icon }))
                        setShowIconPicker(false)
                      }}
                      className="w-8 h-8 text-lg hover:bg-neutral-100 rounded"
                    >
                      {icon}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <Label>Color</Label>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowColorPicker(!showColorPicker)}
                className="w-12 h-12 p-0"
                style={{ backgroundColor: formData.color }}
              >
                <PaletteIcon className="h-5 w-5 text-white" />
              </Button>
              {showColorPicker && (
                <div className="absolute z-10 mt-2 p-3 bg-white border rounded-lg shadow-lg grid grid-cols-5 gap-2">
                  {CATEGORY_COLORS.map(color => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => {
                        setFormData(prev => ({ ...prev, color }))
                        setShowColorPicker(false)
                      }}
                      className="w-8 h-8 rounded border-2 border-neutral-200"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div>
          <Label>Keywords (for auto-categorization)</Label>
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
              <Badge key={keyword} variant="outline" className="flex items-center gap-1">
                {keyword}
                <button
                  type="button"
                  onClick={() => removeKeyword(keyword)}
                  className="ml-1 hover:bg-neutral-200 rounded p-0.5"
                >
                  <XIcon className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <Label htmlFor="confidence">Confidence Threshold ({(formData.confidence_threshold! * 100).toFixed(0)}%)</Label>
          <input
            id="confidence"
            type="range"
            min="0.1"
            max="1"
            step="0.1"
            value={formData.confidence_threshold}
            onChange={(e) => setFormData(prev => ({ ...prev, confidence_threshold: parseFloat(e.target.value) }))}
            className="w-full"
          />
          <p className="text-sm text-neutral-600 mt-1">
            Minimum confidence level for automatic categorization
          </p>
        </div>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Saving...' : category ? 'Update' : 'Create'} Category
          </Button>
        </div>
      </form>
    </Modal>
  )
}

// Helper functions
const getCategoryIcon = (type: string) => {
  switch (type) {
    case 'income':
      return <TrendingUpIcon className="h-4 w-4 text-success-600" />
    case 'expense':
      return <TrendingDownIcon className="h-4 w-4 text-error-600" />
    case 'transfer':
      return <CreditCardIcon className="h-4 w-4 text-info-600" />
    default:
      return <TagIcon className="h-4 w-4 text-neutral-600" />
  }
}

const getCategoryVariant = (type: string) => {
  switch (type) {
    case 'income':
      return 'success' as const
    case 'expense':
      return 'destructive' as const
    case 'transfer':
      return 'default' as const
    default:
      return 'secondary' as const
  }
}

// View Components
function HierarchyView({ categories, selectedCategories, onSelectionChange, onEdit, onDelete, onCopy, onMerge, onPreview, onToggleExpand, onDragEnd, isLoading }: any) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  if (isLoading) {
    return <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-16 bg-neutral-100 animate-pulse rounded-lg" />
      ))}
    </div>
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={onDragEnd}
    >
      <SortableContext items={categories.map((c: any) => c.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-2">
          {categories.map((category: any) => (
            <SortableCategoryItem
              key={category.id}
              category={category}
              isSelected={selectedCategories.includes(category.id)}
              onSelect={(id, selected) => {
                if (selected) {
                  onSelectionChange([...selectedCategories, id])
                } else {
                  onSelectionChange(selectedCategories.filter((cid: string) => cid !== id))
                }
              }}
              onEdit={onEdit}
              onDelete={onDelete}
              onCopy={onCopy}
              onMerge={onMerge}
              onPreview={onPreview}
              onToggleExpand={onToggleExpand}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  )
}

function GridView({ categories, selectedCategories, onSelectionChange, onEdit, onDelete, onCopy, onMerge, onPreview, isLoading }: any) {
  if (isLoading) {
    return <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="h-32 bg-neutral-100 animate-pulse rounded-lg" />
      ))}
    </div>
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {categories.map((category: any) => (
        <Card key={category.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <Checkbox
                checked={selectedCategories.includes(category.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    onSelectionChange([...selectedCategories, category.id])
                  } else {
                    onSelectionChange(selectedCategories.filter((id: string) => id !== category.id))
                  }
                }}
              />
              <div
                className="w-8 h-8 rounded flex items-center justify-center"
                style={{ backgroundColor: category.color || '#6B7280' }}
              >
                <span className="text-white text-sm">
                  {category.icon || getCategoryIcon(category.type)}
                </span>
              </div>
              <div>
                <h3 className="font-medium text-neutral-900">{category.name}</h3>
                <Badge variant={getCategoryVariant(category.type)} className="text-xs">
                  {category.type}
                </Badge>
              </div>
            </div>
          </div>

          {category.is_system && (
            <Badge variant="outline" className="text-xs mb-2">
              System Category
            </Badge>
          )}

          {category.keywords && category.keywords.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-neutral-600 mb-1">Keywords:</p>
              <div className="flex flex-wrap gap-1">
                {category.keywords.slice(0, 3).map((keyword: string, index: number) => (
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

          <div className="flex items-center gap-1 mt-3">
            <Button variant="ghost" size="sm" onClick={() => onPreview(category)} className="h-8 w-8 p-0">
              <EyeIcon className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onCopy(category)} className="h-8 w-8 p-0">
              <CopyIcon className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onEdit(category)} className="h-8 w-8 p-0">
              <EditIcon className="h-4 w-4" />
            </Button>
            {!category.is_system && (
              <>
                <Button variant="ghost" size="sm" onClick={() => onMerge(category)} className="h-8 w-8 p-0">
                  <MergeIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(category)}
                  className="h-8 w-8 p-0 text-error-600 hover:text-error-700 hover:bg-error-50"
                >
                  <TrashIcon className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}

function StatsView({ categoryStats, categorySpending, searchTerm, isLoading }: any) {
  if (isLoading) {
    return <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-20 bg-neutral-100 animate-pulse rounded-lg" />
      ))}
    </div>
  }

  const filteredStats = categoryStats.filter((stat: any) =>
    stat.category.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-4">
      {filteredStats.map((stat: any) => (
        <Card key={stat.category.id} className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-8 h-8 rounded flex items-center justify-center"
                style={{ backgroundColor: stat.category.color || '#6B7280' }}
              >
                <span className="text-white text-sm">
                  {stat.category.icon || getCategoryIcon(stat.category.type)}
                </span>
              </div>
              <div>
                <h3 className="font-medium text-neutral-900">{stat.category.name}</h3>
                <p className="text-sm text-neutral-600">
                  {stat.transaction_count} transactions • Avg: {formatCurrency(stat.avg_amount)}
                </p>
              </div>
            </div>

            <div className="text-right">
              <p className="text-lg font-semibold">
                {formatCurrency(stat.total_amount)}
              </p>
              <p className="text-sm text-neutral-600">
                {stat.usage_frequency.toFixed(1)} tx/month
              </p>
            </div>
          </div>

          {stat.last_used && (
            <div className="mt-2 text-sm text-neutral-600">
              Last used: {new Date(stat.last_used).toLocaleDateString()}
            </div>
          )}
        </Card>
      ))}
    </div>
  )
}

function RulesView({ categories, onManageRules, isLoading }: any) {
  if (isLoading) {
    return <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-16 bg-neutral-100 animate-pulse rounded-lg" />
      ))}
    </div>
  }

  return (
    <div className="space-y-3">
      {categories.map((category: any) => (
        <Card key={category.id} className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-8 h-8 rounded flex items-center justify-center"
                style={{ backgroundColor: category.color || '#6B7280' }}
              >
                <span className="text-white text-sm">
                  {category.icon || getCategoryIcon(category.type)}
                </span>
              </div>
              <div>
                <h3 className="font-medium text-neutral-900">{category.name}</h3>
                <p className="text-sm text-neutral-600">
                  {category.rules?.length || 0} rules • Confidence: {((category.confidence_threshold || 0.8) * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => onManageRules(category)}
            >
              <RulerIcon className="h-4 w-4 mr-1" />
              Manage Rules
            </Button>
          </div>
        </Card>
      ))}
    </div>
  )
}

// Additional modal components would be implemented similarly
function CategoryRulesModal({ isOpen, onClose, category }: any) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Manage Category Rules" size="lg">
      <div className="space-y-4">
        <p className="text-neutral-600">
          Configure rules for automatic categorization of transactions for "{category?.name}"
        </p>
        {/* Rules management interface would go here */}
      </div>
    </Modal>
  )
}

function ImportModal({ isOpen, onClose, onImport }: any) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Import Categories">
      <div className="space-y-4">
        <p className="text-neutral-600">
          Import categories from a CSV or JSON file
        </p>
        {/* Import interface would go here */}
      </div>
    </Modal>
  )
}

function MergeModal({ isOpen, onClose, sourceCategory, categories, onMerge, isLoading }: any) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Merge Categories">
      <div className="space-y-4">
        <p className="text-neutral-600">
          Merge "{sourceCategory?.name}" into another category. All transactions will be moved.
        </p>
        {/* Merge interface would go here */}
      </div>
    </Modal>
  )
}

function PreviewModal({ isOpen, onClose, category }: any) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Category Preview">
      <div className="space-y-4">
        <p className="text-neutral-600">
          Preview transactions in "{category?.name}" category
        </p>
        {/* Transaction preview would go here */}
      </div>
    </Modal>
  )
}