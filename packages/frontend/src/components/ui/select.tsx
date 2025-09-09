import * as React from 'react'
import { ChevronDownIcon, CheckIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  placeholder?: string
  error?: string
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, placeholder, error, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          className={cn(
            'flex h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm ring-offset-background placeholder:text-neutral-500 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-error-500 focus:border-error-500 focus:ring-error-500',
            className
          )}
          ref={ref}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {children}
        </select>
        <ChevronDownIcon className="absolute right-3 top-3 h-4 w-4 text-neutral-500 pointer-events-none" />
        {error && (
          <p className="mt-1 text-sm text-error-600">{error}</p>
        )}
      </div>
    )
  }
)
Select.displayName = 'Select'

// Custom Select Component for better UX
export interface CustomSelectOption {
  value: string
  label: string
  icon?: React.ReactNode
  disabled?: boolean
}

export interface CustomSelectProps {
  options: CustomSelectOption[]
  value?: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
  error?: string
}

export const CustomSelect = React.forwardRef<HTMLDivElement, CustomSelectProps>(
  ({ options, value, onChange, placeholder, className, disabled, error }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false)
    const [selectedOption, setSelectedOption] = React.useState<CustomSelectOption | null>(
      options.find(option => option.value === value) || null
    )

    const handleSelect = (option: CustomSelectOption) => {
      if (option.disabled) return
      setSelectedOption(option)
      onChange(option.value)
      setIsOpen(false)
    }

    React.useEffect(() => {
      const foundOption = options.find(option => option.value === value)
      setSelectedOption(foundOption || null)
    }, [value, options])

    return (
      <div className={cn('relative', className)} ref={ref}>
        <button
          type="button"
          className={cn(
            'flex h-10 w-full items-center justify-between rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm ring-offset-background placeholder:text-neutral-500 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-error-500 focus:border-error-500 focus:ring-error-500'
          )}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
        >
          <div className="flex items-center gap-2">
            {selectedOption?.icon}
            <span className={selectedOption ? 'text-neutral-900' : 'text-neutral-500'}>
              {selectedOption?.label || placeholder || 'Select an option'}
            </span>
          </div>
          <ChevronDownIcon className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')} />
        </button>
        
        {isOpen && (
          <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border border-neutral-200 bg-white py-1 shadow-lg">
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                className={cn(
                  'flex w-full items-center gap-2 px-3 py-2 text-sm text-left hover:bg-neutral-50',
                  option.disabled && 'cursor-not-allowed opacity-50',
                  selectedOption?.value === option.value && 'bg-primary-50 text-primary-700'
                )}
                onClick={() => handleSelect(option)}
                disabled={option.disabled}
              >
                {option.icon}
                <span>{option.label}</span>
                {selectedOption?.value === option.value && (
                  <CheckIcon className="ml-auto h-4 w-4" />
                )}
              </button>
            ))}
          </div>
        )}
        
        {error && (
          <p className="mt-1 text-sm text-error-600">{error}</p>
        )}
      </div>
    )
  }
)
CustomSelect.displayName = 'CustomSelect'

export { Select }