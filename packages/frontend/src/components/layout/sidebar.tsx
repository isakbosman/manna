'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '../../lib/utils'
import {
  LayoutDashboard,
  CreditCard,
  Building2,
  FileText,
  Settings,
  PieChart,
  TrendingUp,
  Wallet,
  Receipt,
  Calculator,
  X
} from 'lucide-react'
import { Button } from '../ui/button'

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
  className?: string
}

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    description: 'Overview and key metrics'
  },
  {
    name: 'Transactions',
    href: '/transactions',
    icon: Receipt,
    description: 'View and manage transactions'
  },
  {
    name: 'Accounts',
    href: '/accounts',
    icon: Building2,
    description: 'Bank and credit accounts'
  },
  {
    name: 'Categories',
    href: '/categories',
    icon: Calculator,
    description: 'Transaction categorization'
  },
  {
    name: 'Reports',
    href: '/reports',
    icon: FileText,
    description: 'Financial reports and analysis',
    subItems: [
      {
        name: 'P&L Statement',
        href: '/reports/pl',
        icon: TrendingUp
      },
      {
        name: 'Balance Sheet',
        href: '/reports/balance-sheet',
        icon: PieChart
      },
      {
        name: 'Cash Flow',
        href: '/reports/cash-flow',
        icon: Wallet
      }
    ]
  },
  {
    name: 'Plaid Integration',
    href: '/plaid',
    icon: CreditCard,
    description: 'Connect bank accounts'
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    description: 'Application settings'
  }
]

export function Sidebar({ isOpen = true, onClose, className }: SidebarProps) {
  const pathname = usePathname()
  const [expandedItems, setExpandedItems] = React.useState<string[]>(['Reports'])

  const toggleExpanded = (name: string) => {
    setExpandedItems(prev =>
      prev.includes(name)
        ? prev.filter(item => item !== name)
        : [...prev, name]
    )
  }

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === href
    }
    return pathname.startsWith(href)
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full w-64 transform border-r bg-background transition-transform duration-200 ease-in-out md:relative md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          className
        )}
      >
        {/* Mobile close button */}
        <div className="flex h-14 items-center justify-between border-b px-4 md:hidden">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded bg-primary-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <span className="font-bold">Manna Financial</span>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-4">
          {navigation.map((item) => {
            const isItemActive = isActive(item.href)
            const isExpanded = expandedItems.includes(item.name)
            const hasSubItems = item.subItems && item.subItems.length > 0

            return (
              <div key={item.name}>
                {hasSubItems ? (
                  <button
                    onClick={() => toggleExpanded(item.name)}
                    className={cn(
                      'flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      isItemActive
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
                    )}
                  >
                    <div className="flex items-center">
                      <item.icon className="mr-3 h-5 w-5" />
                      {item.name}
                    </div>
                    <svg
                      className={cn(
                        'h-4 w-4 transition-transform',
                        isExpanded ? 'rotate-90' : ''
                      )}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                ) : (
                  <Link
                    href={item.href}
                    onClick={() => onClose?.()}
                    className={cn(
                      'flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      isItemActive
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
                    )}
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                )}

                {/* Sub-items */}
                {hasSubItems && isExpanded && (
                  <div className="ml-6 mt-1 space-y-1">
                    {item.subItems!.map((subItem) => {
                      const isSubItemActive = isActive(subItem.href)
                      return (
                        <Link
                          key={subItem.name}
                          href={subItem.href}
                          onClick={() => onClose?.()}
                          className={cn(
                            'flex items-center rounded-md px-3 py-2 text-sm transition-colors',
                            isSubItemActive
                              ? 'bg-primary-50 text-primary-600 font-medium'
                              : 'text-neutral-500 hover:bg-neutral-50 hover:text-neutral-700'
                          )}
                        >
                          <subItem.icon className="mr-3 h-4 w-4" />
                          {subItem.name}
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="border-t p-4">
          <div className="text-xs text-muted-foreground">
            <p>Manna Financial Platform</p>
            <p>Version 1.0.0</p>
          </div>
        </div>
      </aside>
    </>
  )
}