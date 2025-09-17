import * as React from 'react'
import { cn } from '../../lib/utils'

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const Spinner = React.forwardRef<HTMLDivElement, SpinnerProps>(
  ({ className, size = 'md', ...props }, ref) => {
    const sizeClasses = {
      sm: 'h-4 w-4',
      md: 'h-6 w-6',
      lg: 'h-8 w-8',
      xl: 'h-12 w-12',
    }

    return (
      <div
        ref={ref}
        className={cn(
          'animate-spin rounded-full border-b-2 border-primary-600',
          sizeClasses[size],
          className
        )}
        {...props}
      />
    )
  }
)
Spinner.displayName = 'Spinner'

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  text?: string
  className?: string
  fullScreen?: boolean
}

const Loading = React.forwardRef<HTMLDivElement, LoadingProps>(
  ({ size = 'md', text, className, fullScreen = false }, ref) => {
    const containerClasses = fullScreen
      ? 'fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm'
      : 'flex items-center justify-center p-4'

    return (
      <div ref={ref} className={cn(containerClasses, className)}>
        <div className="flex flex-col items-center space-y-3">
          <Spinner size={size} />
          {text && (
            <p className="text-sm text-muted-foreground animate-pulse">
              {text}
            </p>
          )}
        </div>
      </div>
    )
  }
)
Loading.displayName = 'Loading'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'animate-pulse rounded-md bg-neutral-200',
        className
      )}
      {...props}
    />
  )
)
Skeleton.displayName = 'Skeleton'

// Pre-built skeleton components
const SkeletonCard = () => (
  <div className="rounded-lg border border-neutral-200 p-6 space-y-3">
    <Skeleton className="h-6 w-3/4" />
    <div className="space-y-2">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
    <Skeleton className="h-10 w-1/3" />
  </div>
)

const SkeletonTable = ({ rows = 5 }: { rows?: number }) => (
  <div className="space-y-3">
    {/* Header */}
    <div className="flex space-x-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-24" />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex space-x-4">
        {Array.from({ length: 4 }).map((_, j) => (
          <Skeleton key={j} className="h-4 w-24" />
        ))}
      </div>
    ))}
  </div>
)

export { Spinner, Loading, Skeleton, SkeletonCard, SkeletonTable }