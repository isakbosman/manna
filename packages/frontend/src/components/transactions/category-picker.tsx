import React from 'react'
import { 
  TagIcon, 
  HomeIcon, 
  CarIcon, 
  ShoppingCartIcon, 
  UtensilsIcon,
  HeartIcon,
  GraduationCapIcon,
  PlaneIcon,
  ShieldIcon,
  DollarSignIcon,
  TrendingUpIcon,
  CreditCardIcon,
  PiggyBankIcon,
  BuildingIcon,
  PhoneIcon,
  ZapIcon,
  WifiIcon,
  TvIcon,
  GamepadIcon,
  BookIcon,
  MusicIcon,
  CameraIcon,
  SparklesIcon,
  SearchIcon
} from 'lucide-react'
import { CustomSelect, CustomSelectOption } from '../ui/select'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Modal } from '../ui/modal'
import { Category, categoriesApi } from '../../lib/api/categories'
import { cn } from '../../lib/utils'

// Category icons mapping
const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  // Income
  salary: <DollarSignIcon className="h-4 w-4" />,
  freelance: <TrendingUpIcon className="h-4 w-4" />,
  investment: <TrendingUpIcon className="h-4 w-4" />,
  business: <BuildingIcon className="h-4 w-4" />,
  other_income: <DollarSignIcon className="h-4 w-4" />,
  
  // Housing
  rent: <HomeIcon className="h-4 w-4" />,
  mortgage: <HomeIcon className="h-4 w-4" />,
  utilities: <ZapIcon className="h-4 w-4" />,
  insurance: <ShieldIcon className="h-4 w-4" />,
  maintenance: <HomeIcon className="h-4 w-4" />,
  
  // Transportation
  gas: <CarIcon className="h-4 w-4" />,
  parking: <CarIcon className="h-4 w-4" />,
  public_transport: <CarIcon className="h-4 w-4" />,
  car_payment: <CarIcon className="h-4 w-4" />,
  maintenance_auto: <CarIcon className="h-4 w-4" />,
  
  // Food
  groceries: <ShoppingCartIcon className="h-4 w-4" />,
  restaurants: <UtensilsIcon className="h-4 w-4" />,
  fast_food: <UtensilsIcon className="h-4 w-4" />,
  coffee: <UtensilsIcon className="h-4 w-4" />,
  
  // Healthcare
  medical: <HeartIcon className="h-4 w-4" />,
  dental: <HeartIcon className="h-4 w-4" />,
  pharmacy: <HeartIcon className="h-4 w-4" />,
  
  // Education
  tuition: <GraduationCapIcon className="h-4 w-4" />,
  books: <BookIcon className="h-4 w-4" />,
  supplies: <GraduationCapIcon className="h-4 w-4" />,
  
  // Entertainment
  movies: <TvIcon className="h-4 w-4" />,
  games: <GamepadIcon className="h-4 w-4" />,
  music: <MusicIcon className="h-4 w-4" />,
  hobbies: <SparklesIcon className="h-4 w-4" />,
  
  // Travel
  flights: <PlaneIcon className="h-4 w-4" />,
  hotels: <PlaneIcon className="h-4 w-4" />,
  vacation: <PlaneIcon className="h-4 w-4" />,
  
  // Technology
  internet: <WifiIcon className="h-4 w-4" />,
  phone: <PhoneIcon className="h-4 w-4" />,
  software: <ZapIcon className="h-4 w-4" />,
  
  // Personal Care
  clothing: <SparklesIcon className="h-4 w-4" />,
  beauty: <SparklesIcon className="h-4 w-4" />,
  gym: <HeartIcon className="h-4 w-4" />,
  
  // Financial
  savings: <PiggyBankIcon className="h-4 w-4" />,
  investments: <TrendingUpIcon className="h-4 w-4" />,
  debt_payment: <CreditCardIcon className="h-4 w-4" />,
  fees: <DollarSignIcon className="h-4 w-4" />,
  
  // Default
  default: <TagIcon className="h-4 w-4" />,
}

interface CategoryPickerProps {
  selectedCategory?: string
  onCategorySelect: (categoryId: string) => void
  className?: string
  disabled?: boolean
  placeholder?: string
  allowCustom?: boolean
  transactionDescription?: string // For AI suggestions
  mlPredictions?: { category_id: string; confidence: number }[]
}

export function CategoryPicker({
  selectedCategory,
  onCategorySelect,
  className,
  disabled,
  placeholder = "Select category",
  allowCustom = true,
  transactionDescription,
  mlPredictions = []
}: CategoryPickerProps) {
  const [categories, setCategories] = React.useState<Category[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [showCreateModal, setShowCreateModal] = React.useState(false)
  const [searchTerm, setSearchTerm] = React.useState('')

  React.useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    try {
      setIsLoading(true)
      const data = await categoriesApi.getCategories()
      setCategories(data)
    } catch (error) {
      console.error('Failed to load categories:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Filter categories based on search
  const filteredCategories = categories.filter(category =>
    category.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Sort categories: ML predictions first, then alphabetically
  const sortedCategories = React.useMemo(() => {
    const predicted = new Set(mlPredictions.map(p => p.category_id))
    
    return [...filteredCategories].sort((a, b) => {
      const aIsPredicted = predicted.has(a.id)
      const bIsPredicted = predicted.has(b.id)
      
      if (aIsPredicted && !bIsPredicted) return -1
      if (!aIsPredicted && bIsPredicted) return 1
      
      return a.name.localeCompare(b.name)
    })
  }, [filteredCategories, mlPredictions])

  const getCategoryIcon = (category: Category) => {
    return CATEGORY_ICONS[category.name.toLowerCase().replace(/\s+/g, '_')] || 
           CATEGORY_ICONS[category.icon || 'default'] || 
           CATEGORY_ICONS.default
  }

  const getCategoryColor = (category: Category) => {
    if (category.type === 'income') return 'success'
    if (category.type === 'expense') return 'destructive'
    return 'secondary'
  }

  const getMLConfidence = (categoryId: string) => {
    const prediction = mlPredictions.find(p => p.category_id === categoryId)
    return prediction?.confidence || 0
  }

  const categoryOptions: CustomSelectOption[] = sortedCategories.map(category => ({
    value: category.id,
    label: category.name,
    icon: (
      <div className="flex items-center gap-2">
        {getCategoryIcon(category)}
        <div className="flex items-center gap-1">
          <Badge variant={getCategoryColor(category)} className="text-xs">
            {category.type}
          </Badge>
          {getMLConfidence(category.id) > 0 && (
            <Badge variant="info" className="text-xs">
              {Math.round(getMLConfidence(category.id) * 100)}%
            </Badge>
          )}
        </div>
      </div>
    ),
  }))

  // Add "Create New" option if allowed
  if (allowCustom && searchTerm && !categories.some(c => 
    c.name.toLowerCase() === searchTerm.toLowerCase()
  )) {
    categoryOptions.push({
      value: '__create_new__',
      label: `Create "${searchTerm}"`,
      icon: <TagIcon className="h-4 w-4" />
    })
  }

  const handleCategoryChange = (value: string) => {
    if (value === '__create_new__') {
      setShowCreateModal(true)
    } else {
      onCategorySelect(value)
    }
  }

  const selectedOption = categories.find(c => c.id === selectedCategory)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <>
      <div className={className}>
        <div className="space-y-2">
          {/* Search */}
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
            <Input
              placeholder="Search categories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Category Grid */}
          <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
            {sortedCategories.map((category) => {
              const isSelected = category.id === selectedCategory
              const mlConfidence = getMLConfidence(category.id)
              
              return (
                <button
                  key={category.id}
                  type="button"
                  onClick={() => onCategorySelect(category.id)}
                  disabled={disabled}
                  className={cn(
                    'flex items-center gap-2 p-3 rounded-md border text-left transition-colors hover:bg-neutral-50',
                    isSelected && 'border-primary-500 bg-primary-50 text-primary-700',
                    !isSelected && 'border-neutral-200',
                    disabled && 'opacity-50 cursor-not-allowed',
                    mlConfidence > 0.7 && 'ring-2 ring-info-200'
                  )}
                >
                  <div className="flex-shrink-0">
                    {getCategoryIcon(category)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{category.name}</p>
                    <div className="flex items-center gap-1 mt-1">
                      <Badge variant={getCategoryColor(category)} className="text-xs">
                        {category.type}
                      </Badge>
                      {mlConfidence > 0 && (
                        <Badge variant="info" className="text-xs">
                          {Math.round(mlConfidence * 100)}% match
                        </Badge>
                      )}
                    </div>
                  </div>
                </button>
              )
            })}

            {/* Create New Category Button */}
            {allowCustom && (
              <button
                type="button"
                onClick={() => setShowCreateModal(true)}
                disabled={disabled}
                className="flex items-center gap-2 p-3 rounded-md border border-dashed border-neutral-300 text-left transition-colors hover:bg-neutral-50"
              >
                <TagIcon className="h-4 w-4" />
                <span className="text-sm font-medium">Create New Category</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Create Category Modal */}
      <CreateCategoryModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCategoryCreated={(category) => {
          setCategories(prev => [...prev, category])
          onCategorySelect(category.id)
          setShowCreateModal(false)
        }}
        initialName={searchTerm}
      />
    </>
  )
}

// Create Category Modal Component
interface CreateCategoryModalProps {
  isOpen: boolean
  onClose: () => void
  onCategoryCreated: (category: Category) => void
  initialName?: string
}

function CreateCategoryModal({
  isOpen,
  onClose,
  onCategoryCreated,
  initialName = ''
}: CreateCategoryModalProps) {
  const [name, setName] = React.useState(initialName)
  const [type, setType] = React.useState<'income' | 'expense' | 'transfer'>('expense')
  const [icon, setIcon] = React.useState('default')
  const [color, setColor] = React.useState('#6B7280')
  const [isLoading, setIsLoading] = React.useState(false)

  React.useEffect(() => {
    if (isOpen) {
      setName(initialName)
      setType('expense')
      setIcon('default')
      setColor('#6B7280')
    }
  }, [isOpen, initialName])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    try {
      setIsLoading(true)
      const category = await categoriesApi.createCategory({
        name: name.trim(),
        type,
        icon,
        color,
        is_system: false
      })
      onCategoryCreated(category)
    } catch (error) {
      console.error('Failed to create category:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Category"
      description="Add a custom category for your transactions"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Category Name
          </label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter category name"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Type
          </label>
          <CustomSelect
            options={[
              { value: 'income', label: 'Income', icon: <TrendingUpIcon className="h-4 w-4" /> },
              { value: 'expense', label: 'Expense', icon: <DollarSignIcon className="h-4 w-4" /> },
              { value: 'transfer', label: 'Transfer', icon: <CreditCardIcon className="h-4 w-4" /> },
            ]}
            value={type}
            onChange={(value) => setType(value as any)}
          />
        </div>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={isLoading}>
            Create Category
          </Button>
        </div>
      </form>
    </Modal>
  )
}