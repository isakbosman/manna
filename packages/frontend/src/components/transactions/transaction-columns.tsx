'use client'

import { ColumnDef } from '@tanstack/react-table'
import { Checkbox } from '../ui/checkbox'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '../ui/dropdown-menu'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '../ui/tooltip'
import {
  MoreHorizontal,
  Edit,
  Trash,
  Copy,
  Tag,
  FileText,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  CheckCircle
} from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { cn } from '../../lib/utils'
import type { Transaction } from '../../lib/api/transactions'
import type { Account } from '../../lib/api/accounts'
import type { Category } from '../../lib/api/categories'

interface TransactionColumnsProps {
  accounts: Account[]
  categories: Category[]
  onEdit?: (transaction: Transaction) => void
  onDelete?: (transaction: Transaction) => void
  onCategorize?: (transaction: Transaction) => void
  onDuplicate?: (transaction: Transaction) => void
  onViewDetails?: (transaction: Transaction) => void
}

export function getTransactionColumns({
  accounts,
  categories,
  onEdit,
  onDelete,
  onCategorize,
  onDuplicate,
  onViewDetails
}: TransactionColumnsProps): ColumnDef<Transaction>[] {
  return [
    // Selection Column
    {
      id: 'select',
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
          data-no-row-click
        />
      ),
      enableSorting: false,
      enableHiding: false
    },

    // Date Column
    {
      accessorKey: 'date',
      header: 'Date',
      cell: ({ row }) => {
        const date = parseISO(row.getValue('date'))
        return (
          <div className="whitespace-nowrap">
            <div className="font-medium">{format(date, 'MMM d, yyyy')}</div>
            <div className="text-xs text-muted-foreground">{format(date, 'EEEE')}</div>
          </div>
        )
      },
      sortingFn: 'datetime'
    },

    // Description Column
    {
      accessorKey: 'description',
      header: 'Description',
      cell: ({ row }) => {
        const transaction = row.original
        const isIncome = transaction.amount > 0

        return (
          <div className="flex items-start space-x-2">
            <div className={cn(
              'mt-1 p-1 rounded',
              isIncome ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            )}>
              {isIncome ? (
                <ArrowDownRight className="h-3 w-3" />
              ) : (
                <ArrowUpRight className="h-3 w-3" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{transaction.description}</div>
              {transaction.merchant_name && transaction.merchant_name !== transaction.description && (
                <div className="text-xs text-muted-foreground truncate">
                  {transaction.merchant_name}
                </div>
              )}
            </div>
            {transaction.is_pending && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Clock className="h-4 w-4 text-amber-500" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Pending transaction</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        )
      }
    },

    // Category Column
    {
      id: 'category',
      header: 'Category',
      accessorFn: (row) => row.category || 'Uncategorized',
      cell: ({ row }) => {
        const transaction = row.original
        const category = transaction.category_id
          ? categories.find(c => c.id === transaction.category_id)
          : null

        if (!category) {
          return (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-muted-foreground hover:text-foreground"
              onClick={(e) => {
                e.stopPropagation()
                if (onCategorize) onCategorize(transaction)
              }}
              data-no-row-click
            >
              <Tag className="mr-1 h-3 w-3" />
              Add category
            </Button>
          )
        }

        return (
          <Badge
            variant="outline"
            className="cursor-pointer"
            onClick={(e) => {
              e.stopPropagation()
              if (onCategorize) onCategorize(transaction)
            }}
            data-no-row-click
          >
            {category.icon && <span className="mr-1">{category.icon}</span>}
            {category.name}
            {transaction.subcategory && (
              <span className="ml-1 text-xs text-muted-foreground">
                / {transaction.subcategory}
              </span>
            )}
          </Badge>
        )
      },
      filterFn: (row, id, value) => {
        if (value === 'Uncategorized') {
          return !row.original.category_id
        }
        return row.original.category_id === value
      }
    },

    // Account Column
    {
      accessorKey: 'account_id',
      header: 'Account',
      cell: ({ row }) => {
        const account = accounts.find(a => a.id === row.getValue('account_id'))
        if (!account) return <span className="text-muted-foreground">Unknown</span>

        return (
          <div className="whitespace-nowrap">
            <div className="font-medium text-sm">{account.name}</div>
            {account.mask && (
              <div className="text-xs text-muted-foreground">•••• {account.mask}</div>
            )}
          </div>
        )
      },
      filterFn: (row, id, value) => {
        return row.getValue(id) === value
      }
    },

    // Amount Column
    {
      accessorKey: 'amount',
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="hover:bg-transparent p-0"
          >
            Amount
          </Button>
        )
      },
      cell: ({ row }) => {
        const amount = parseFloat(row.getValue('amount'))
        const isIncome = amount > 0

        return (
          <div className={cn(
            'font-mono font-semibold text-right whitespace-nowrap',
            isIncome ? 'text-green-600' : 'text-red-600'
          )}>
            {isIncome ? '+' : '-'}${Math.abs(amount).toFixed(2)}
          </div>
        )
      },
      sortingFn: 'basic'
    },

    // Status Column
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const transaction = row.original

        return (
          <div className="flex items-center space-x-2">
            {transaction.is_pending ? (
              <Badge variant="secondary" className="text-xs">
                <Clock className="mr-1 h-3 w-3" />
                Pending
              </Badge>
            ) : (
              <Badge variant="outline" className="text-xs">
                <CheckCircle className="mr-1 h-3 w-3" />
                Posted
              </Badge>
            )}
            {transaction.notes && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <FileText className="h-3 w-3 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="max-w-xs">{transaction.notes}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        )
      }
    },

    // Actions Column
    {
      id: 'actions',
      enableHiding: false,
      cell: ({ row }) => {
        const transaction = row.original

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="h-8 w-8 p-0"
                data-no-row-click
              >
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuItem
                onClick={() => onViewDetails && onViewDetails(transaction)}
              >
                <FileText className="mr-2 h-4 w-4" />
                View details
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onEdit && onEdit(transaction)}
              >
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onCategorize && onCategorize(transaction)}
              >
                <Tag className="mr-2 h-4 w-4" />
                Categorize
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onDuplicate && onDuplicate(transaction)}
              >
                <Copy className="mr-2 h-4 w-4" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete && onDelete(transaction)}
                className="text-red-600"
              >
                <Trash className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )
      }
    }
  ]
}