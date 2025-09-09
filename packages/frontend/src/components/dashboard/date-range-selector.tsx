'use client'

import React, { useState } from 'react'
import { format, subDays, subMonths, subYears, startOfMonth, endOfMonth, startOfYear, endOfYear } from 'date-fns'
import { Calendar, ChevronDown } from 'lucide-react'

export interface DateRange {
  start: Date
  end: Date
  label: string
}

interface DateRangeSelectorProps {
  selectedRange: DateRange
  onRangeChange: (range: DateRange) => void
  className?: string
  disabled?: boolean
}

const PRESET_RANGES = [
  {
    label: 'Last 7 days',
    getValue: () => ({
      start: subDays(new Date(), 6),
      end: new Date(),
      label: 'Last 7 days'
    })
  },
  {
    label: 'Last 30 days',
    getValue: () => ({
      start: subDays(new Date(), 29),
      end: new Date(),
      label: 'Last 30 days'
    })
  },
  {
    label: 'Last 90 days',
    getValue: () => ({
      start: subDays(new Date(), 89),
      end: new Date(),
      label: 'Last 90 days'
    })
  },
  {
    label: 'This month',
    getValue: () => ({
      start: startOfMonth(new Date()),
      end: endOfMonth(new Date()),
      label: 'This month'
    })
  },
  {
    label: 'Last month',
    getValue: () => {
      const lastMonth = subMonths(new Date(), 1)
      return {
        start: startOfMonth(lastMonth),
        end: endOfMonth(lastMonth),
        label: 'Last month'
      }
    }
  },
  {
    label: 'Last 3 months',
    getValue: () => ({
      start: subMonths(new Date(), 3),
      end: new Date(),
      label: 'Last 3 months'
    })
  },
  {
    label: 'Last 6 months',
    getValue: () => ({
      start: subMonths(new Date(), 6),
      end: new Date(),
      label: 'Last 6 months'
    })
  },
  {
    label: 'This year',
    getValue: () => ({
      start: startOfYear(new Date()),
      end: endOfYear(new Date()),
      label: 'This year'
    })
  },
  {
    label: 'Last year',
    getValue: () => {
      const lastYear = subYears(new Date(), 1)
      return {
        start: startOfYear(lastYear),
        end: endOfYear(lastYear),
        label: 'Last year'
      }
    }
  }
]

export function DateRangeSelector({
  selectedRange,
  onRangeChange,
  className = '',
  disabled = false
}: DateRangeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleRangeSelect = (range: DateRange) => {
    onRangeChange(range)
    setIsOpen(false)
  }

  const formatDateRange = (range: DateRange) => {
    if (range.label) return range.label
    
    const startDate = format(range.start, 'MMM dd, yyyy')
    const endDate = format(range.end, 'MMM dd, yyyy')
    return `${startDate} - ${endDate}`
  }

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          inline-flex items-center justify-between w-full px-3 py-2 text-sm font-medium
          text-neutral-700 bg-white border border-neutral-300 rounded-md shadow-sm
          hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
          transition-colors
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <div className="flex items-center">
          <Calendar className="h-4 w-4 mr-2 text-neutral-500" />
          <span>{formatDateRange(selectedRange)}</span>
        </div>
        <ChevronDown className={`h-4 w-4 text-neutral-500 transition-transform ${
          isOpen ? 'transform rotate-180' : ''
        }`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute right-0 z-20 w-64 mt-1 bg-white border border-neutral-200 rounded-md shadow-lg">
            <div className="py-1">
              {PRESET_RANGES.map((preset, index) => {
                const range = preset.getValue()
                const isSelected = selectedRange.label === range.label
                
                return (
                  <button
                    key={index}
                    onClick={() => handleRangeSelect(range)}
                    className={`
                      w-full px-4 py-2 text-left text-sm hover:bg-neutral-50
                      transition-colors
                      ${isSelected 
                        ? 'bg-primary-50 text-primary-700 font-medium' 
                        : 'text-neutral-700'
                      }
                    `}
                  >
                    <div className="flex justify-between items-center">
                      <span>{preset.label}</span>
                      {preset.label !== 'This month' && preset.label !== 'Last month' && 
                       preset.label !== 'This year' && preset.label !== 'Last year' && (
                        <span className="text-xs text-neutral-500">
                          {format(range.start, 'MMM dd')} - {format(range.end, 'MMM dd')}
                        </span>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>

            {/* Custom Range Section */}
            <div className="border-t border-neutral-200 py-2">
              <div className="px-4 py-2">
                <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">
                  Custom Range
                </p>
                <p className="text-xs text-neutral-400 mt-1">
                  Feature coming soon
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}