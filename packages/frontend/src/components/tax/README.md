# Tax Categorization System

A comprehensive frontend implementation for tax categorization and business expense tracking, built with React, TypeScript, and Tailwind CSS.

## Overview

The tax categorization system provides a complete solution for categorizing financial transactions for tax purposes, particularly focusing on Schedule C business expenses. It includes components for single and bulk categorization, tax summaries, and chart of accounts management.

## Components

### Core Components

#### 1. TaxCategorizationModal
**File**: `tax-categorization-modal.tsx`

Modal component for categorizing individual transactions with tax-specific fields.

**Features**:
- Select tax category (Schedule C lines)
- Business use percentage slider (0-100%)
- Business purpose text field
- Receipt URL field
- Mileage tracking for vehicle expenses
- Auto-detection based on merchant name
- 50% deduction indicator for meals
- Real-time deductible amount calculation

**Props**:
```typescript
interface TaxCategorizationModalProps {
  isOpen: boolean
  onClose: () => void
  transaction: Transaction
  onTransactionUpdated: (transaction: Transaction) => void
}
```

**Usage**:
```tsx
<TaxCategorizationModal
  isOpen={isModalOpen}
  onClose={() => setIsModalOpen(false)}
  transaction={selectedTransaction}
  onTransactionUpdated={handleTransactionUpdate}
/>
```

#### 2. BulkTaxCategorization
**File**: `bulk-tax-categorization.tsx`

Component for applying tax categorization to multiple transactions simultaneously.

**Features**:
- Multi-select transactions support
- Batch processing with progress indicator
- Same category applied to all selected transactions
- Error handling for failed batches
- Progress tracking during bulk operations

**Props**:
```typescript
interface BulkTaxCategorizationProps {
  isOpen: boolean
  onClose: () => void
  transactions: Transaction[]
  onTransactionsUpdated: (transactions: Transaction[]) => void
}
```

#### 3. TaxSummaryDashboard
**File**: `tax-summary-dashboard.tsx`

Dashboard component showing tax deduction summaries and documentation status.

**Features**:
- Total deductions by category
- Documentation status indicators
- Export functionality (CSV/PDF)
- Year selector
- Quick action buttons for common tasks
- Progress tracking for documentation completeness

#### 4. ChartOfAccountsManager
**File**: `chart-of-accounts-manager.tsx`

Component for managing the chart of accounts with hierarchical display.

**Features**:
- Tree view of accounts by type (Assets, Liabilities, etc.)
- Add/Edit/Delete accounts
- Account balance display
- Search and filter functionality
- Expand/collapse hierarchical structure

### Integration Components

#### TaxEnhancedTransactionsTable
**File**: `transactions/tax-enhanced-transactions-table.tsx`

Enhanced version of the transactions table with tax categorization features.

**Features**:
- Tax status column showing categorization completeness
- Quick tax categorization buttons
- Bulk tax categorization support
- Deductible amount display
- Integration with existing transaction management

## API Integration

### Tax API Module
**File**: `lib/api/tax.ts`

TypeScript API client for tax-related operations.

**Key Functions**:
- `categorizeSingle()` - Categorize single transaction
- `categorizeBulk()` - Bulk categorize transactions
- `getTaxSummary()` - Get tax summary for year
- `getTaxCategories()` - List available tax categories
- `exportScheduleC()` - Export Schedule C data

**Types**:
```typescript
interface TaxCategory {
  id: string
  name: string
  schedule_c_line: string
  description: string
  is_deductible: boolean
  requires_receipt: boolean
  has_business_use_percentage: boolean
  is_meals_50_percent: boolean
  is_vehicle_expense: boolean
}

interface TaxCategorization {
  id: string
  transaction_id: string
  tax_category_id: string
  business_use_percentage: number
  business_purpose?: string
  receipt_url?: string
  mileage?: number
}
```

## Usage Examples

### Basic Tax Categorization

```tsx
import { TaxCategorizationModal } from '@/components/tax'

function TransactionList() {
  const [selectedTransaction, setSelectedTransaction] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleCategorize = (transaction) => {
    setSelectedTransaction(transaction)
    setIsModalOpen(true)
  }

  return (
    <>
      {/* Transaction list with categorize buttons */}
      <TaxCategorizationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        transaction={selectedTransaction}
        onTransactionUpdated={handleUpdate}
      />
    </>
  )
}
```

### Bulk Categorization

```tsx
import { BulkTaxCategorization } from '@/components/tax'

function BulkActions({ selectedTransactions }) {
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false)

  return (
    <>
      <Button onClick={() => setIsBulkModalOpen(true)}>
        Bulk Categorize {selectedTransactions.length} Transactions
      </Button>

      <BulkTaxCategorization
        isOpen={isBulkModalOpen}
        onClose={() => setIsBulkModalOpen(false)}
        transactions={selectedTransactions}
        onTransactionsUpdated={handleBulkUpdate}
      />
    </>
  )
}
```

### Tax Dashboard

```tsx
import { TaxSummaryDashboard } from '@/components/tax'

function TaxPage() {
  return (
    <div className="space-y-6">
      <h1>Tax Management</h1>
      <TaxSummaryDashboard />
    </div>
  )
}
```

## Features

### Tax-Specific Fields

1. **Business Use Percentage**: Slider for partial business use (1-100%)
2. **Business Purpose**: Required text field for expense justification
3. **Receipt URL**: Optional field for receipt documentation
4. **Mileage**: Required for vehicle expenses
5. **Category Detection**: Auto-suggest categories based on merchant/description

### Schedule C Integration

- Maps to Schedule C line items
- Handles 50% meal deduction limit
- Vehicle expense tracking
- Receipt requirements by category
- Business purpose documentation

### Documentation Status

- **Complete**: Has receipt and business purpose
- **Partial**: Missing either receipt or business purpose
- **Minimal**: Has categorization but missing documentation
- **None**: No tax categorization

### Export Features

- Schedule C CSV export
- Schedule C PDF export
- Tax summary reports
- Documentation status reports

## Styling

The components use Tailwind CSS with a consistent design system:

- **Colors**: Blue for primary actions, Green for income/positive, Red for expenses/negative
- **Icons**: Lucide React icons for consistency
- **Layout**: Responsive design with mobile-first approach
- **Components**: shadcn/ui components for consistency

## Accessibility

- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader compatibility
- Focus management
- High contrast support

## Performance

- React Query for efficient data fetching
- Batch processing for bulk operations
- Optimistic updates for better UX
- Lazy loading for large datasets
- Debounced search functionality

## Error Handling

- Comprehensive error boundaries
- User-friendly error messages
- Retry mechanisms for failed operations
- Validation with clear feedback
- Graceful degradation

## Testing

Components are designed to be testable with:

- Clear prop interfaces
- Separation of concerns
- Mock-friendly API calls
- Predictable state management
- Isolated side effects

## Future Enhancements

1. **Offline Support**: Cache categorizations for offline work
2. **Advanced Rules**: Auto-categorization rules based on patterns
3. **Receipt OCR**: Extract data from receipt images
4. **Tax Optimization**: Suggest optimal categorizations
5. **Audit Trail**: Track all categorization changes
6. **Multi-Year Analysis**: Compare tax data across years

## Dependencies

- React 18+
- TypeScript 5+
- @tanstack/react-query 5+
- @radix-ui components
- Tailwind CSS 3+
- Lucide React icons
- date-fns for date formatting

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+