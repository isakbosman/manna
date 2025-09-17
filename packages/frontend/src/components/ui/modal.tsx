import * as React from 'react'
import { XIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  className?: string
  hideCloseButton?: boolean
}

const Modal = React.forwardRef<HTMLDivElement, ModalProps>(
  ({ isOpen, onClose, title, description, children, size = 'md', className, hideCloseButton }, ref) => {
    React.useEffect(() => {
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose()
      }
      
      if (isOpen) {
        document.addEventListener('keydown', handleEscape)
        document.body.style.overflow = 'hidden'
      }
      
      return () => {
        document.removeEventListener('keydown', handleEscape)
        document.body.style.overflow = 'unset'
      }
    }, [isOpen, onClose])

    if (!isOpen) return null

    const sizeClasses = {
      sm: 'max-w-md',
      md: 'max-w-lg',
      lg: 'max-w-2xl',
      xl: 'max-w-4xl',
      full: 'max-w-full mx-4'
    }

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Backdrop */}
        <div 
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div 
          ref={ref}
          className={cn(
            'relative w-full rounded-lg bg-white shadow-xl',
            sizeClasses[size],
            className
          )}
        >
          {/* Header */}
          {(title || !hideCloseButton) && (
            <div className="flex items-center justify-between p-6 pb-4">
              <div>
                {title && (
                  <h2 className="text-lg font-semibold text-neutral-900">
                    {title}
                  </h2>
                )}
                {description && (
                  <p className="mt-1 text-sm text-neutral-600">
                    {description}
                  </p>
                )}
              </div>
              {!hideCloseButton && (
                <button
                  onClick={onClose}
                  className="rounded-md p-2 hover:bg-neutral-100"
                >
                  <XIcon className="h-5 w-5" />
                </button>
              )}
            </div>
          )}
          
          {/* Content */}
          <div className={cn('px-6', (title || !hideCloseButton) ? 'pb-6' : 'py-6')}>
            {children}
          </div>
        </div>
      </div>
    )
  }
)
Modal.displayName = 'Modal'

export { Modal }