import * as React from 'react'
import { CheckIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  description?: string
  error?: string
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, description, error, ...props }, ref) => {
    return (
      <div className="space-y-1">
        <div className="flex items-start space-x-2">
          <div className="relative flex items-center">
            <input
              type="checkbox"
              className={cn(
                'h-4 w-4 rounded border-neutral-300 text-primary-600 shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-50',
                error && 'border-error-500 focus:border-error-500 focus:ring-error-500',
                className
              )}
              ref={ref}
              {...props}
            />
          </div>
          {label && (
            <div className="space-y-1">
              <label className="text-sm font-medium text-neutral-900">
                {label}
              </label>
              {description && (
                <p className="text-sm text-neutral-600">{description}</p>
              )}
            </div>
          )}
        </div>
        {error && (
          <p className="text-sm text-error-600">{error}</p>
        )}
      </div>
    )
  }
)
Checkbox.displayName = 'Checkbox'

export { Checkbox }