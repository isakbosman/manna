/**
 * Complete Tax Categorization System Integration Example
 *
 * This example demonstrates how to integrate all tax categorization components
 * into an existing application with proper state management and API integration.
 */

import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Calculator, Receipt, FileText, Settings, Users } from 'lucide-react';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import { TooltipProvider } from '../ui/tooltip';
import {
  TaxCategorizationModal,
  BulkTaxCategorization,
  TaxSummaryDashboard,
  ChartOfAccountsManager
} from './index';
import { taxCategorizationApi } from '../../services/taxCategorizationApi';
import { transactionsApi, Transaction } from '../../lib/api/transactions';

interface TaxSystemExampleProps {
  className?: string;
}

export function TaxSystemExample({ className }: TaxSystemExampleProps) {
  const queryClient = useQueryClient();

  // State for modals and selections
  const [isTaxModalOpen, setIsTaxModalOpen] = React.useState(false);
  const [isBulkTaxModalOpen, setIsBulkTaxModalOpen] = React.useState(false);
  const [selectedTransaction, setSelectedTransaction] = React.useState<Transaction | null>(null);
  const [selectedTransactions, setSelectedTransactions] = React.useState<Transaction[]>([]);

  // Load sample transactions (replace with your actual transaction loading logic)
  const { data: transactions = [], isLoading: isLoadingTransactions } = useQuery({
    queryKey: ['transactions'],
    queryFn: () => transactionsApi.getTransactions({ limit: 10 }),
  });

  // Load tax categories for quick stats
  const { data: taxCategories = [] } = useQuery({
    queryKey: ['tax-categories'],
    queryFn: taxCategorizationApi.getTaxCategories,
  });

  // Load tax summary for current year
  const { data: taxSummary } = useQuery({
    queryKey: ['tax-summary', new Date().getFullYear()],
    queryFn: () => taxCategorizationApi.getTaxSummary({
      tax_year: new Date().getFullYear()
    }),
  });

  // Handlers for tax categorization
  const handleTaxCategorize = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setIsTaxModalOpen(true);
  };

  const handleBulkTaxCategorize = () => {
    if (selectedTransactions.length > 0) {
      setIsBulkTaxModalOpen(true);
    }
  };

  const handleTransactionUpdated = (updatedTransaction: Transaction) => {
    // Invalidate queries to refresh data
    queryClient.invalidateQueries({ queryKey: ['transactions'] });
    queryClient.invalidateQueries({ queryKey: ['tax-summary'] });

    // Update selected transaction if it was the one being edited
    if (selectedTransaction?.id === updatedTransaction.id) {
      setSelectedTransaction(updatedTransaction);
    }
  };

  const handleBulkCategorized = (updatedTransactions: Transaction[]) => {
    // Refresh relevant queries
    queryClient.invalidateQueries({ queryKey: ['transactions'] });
    queryClient.invalidateQueries({ queryKey: ['tax-summary'] });

    // Clear selection
    setSelectedTransactions([]);
  };

  // Calculate quick stats
  const uncategorizedCount = transactions.transactions?.filter(t => !t.tax_categorization).length || 0;
  const totalDeductions = taxSummary?.total_deductions || 0;

  if (isLoadingTransactions) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading tax categorization system...</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className={`space-y-6 ${className}`}>
        {/* Header with Quick Stats */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Tax Categorization System</h1>
            <p className="text-gray-600 mt-1">
              Manage business expenses and tax deductions for Schedule C filing
            </p>
          </div>
          <div className="flex gap-4">
            <Card className="p-4">
              <div className="flex items-center gap-2">
                <Receipt className="h-5 w-5 text-orange-600" />
                <div>
                  <p className="text-sm text-gray-600">Uncategorized</p>
                  <p className="text-xl font-bold text-orange-600">{uncategorizedCount}</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm text-gray-600">Total Deductions</p>
                  <p className="text-xl font-bold text-green-600">
                    ${totalDeductions.toLocaleString()}
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* Main Tabs Interface */}
        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <Calculator className="h-4 w-4" />
              Tax Dashboard
            </TabsTrigger>
            <TabsTrigger value="transactions" className="flex items-center gap-2">
              <Receipt className="h-4 w-4" />
              Transactions
              {uncategorizedCount > 0 && (
                <Badge variant="destructive" className="ml-2 h-5">
                  {uncategorizedCount}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="bulk" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Bulk Actions
            </TabsTrigger>
            <TabsTrigger value="accounts" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Chart of Accounts
            </TabsTrigger>
          </TabsList>

          {/* Tax Summary Dashboard */}
          <TabsContent value="dashboard" className="space-y-4">
            <TaxSummaryDashboard />
          </TabsContent>

          {/* Transaction Categorization */}
          <TabsContent value="transactions" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Recent Transactions</h2>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setSelectedTransactions(transactions.transactions || [])}
                  disabled={!transactions.transactions?.length}
                >
                  Select All
                </Button>
                <Button
                  onClick={handleBulkTaxCategorize}
                  disabled={selectedTransactions.length === 0}
                >
                  Bulk Categorize ({selectedTransactions.length})
                </Button>
              </div>
            </div>

            {/* Sample Transaction List */}
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b bg-gray-50">
                    <tr>
                      <th className="text-left p-4">
                        <input
                          type="checkbox"
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedTransactions(transactions.transactions || []);
                            } else {
                              setSelectedTransactions([]);
                            }
                          }}
                          checked={selectedTransactions.length === (transactions.transactions?.length || 0)}
                        />
                      </th>
                      <th className="text-left p-4">Date</th>
                      <th className="text-left p-4">Description</th>
                      <th className="text-left p-4">Amount</th>
                      <th className="text-left p-4">Tax Category</th>
                      <th className="text-left p-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.transactions?.map((transaction) => (
                      <tr key={transaction.id} className="border-b hover:bg-gray-50">
                        <td className="p-4">
                          <input
                            type="checkbox"
                            checked={selectedTransactions.some(t => t.id === transaction.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedTransactions([...selectedTransactions, transaction]);
                              } else {
                                setSelectedTransactions(
                                  selectedTransactions.filter(t => t.id !== transaction.id)
                                );
                              }
                            }}
                          />
                        </td>
                        <td className="p-4">
                          {new Date(transaction.date).toLocaleDateString()}
                        </td>
                        <td className="p-4 font-medium">{transaction.description}</td>
                        <td className="p-4">
                          <span className={transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}>
                            ${Math.abs(transaction.amount).toFixed(2)}
                          </span>
                        </td>
                        <td className="p-4">
                          {transaction.tax_categorization ? (
                            <Badge variant="secondary">
                              Categorized
                            </Badge>
                          ) : (
                            <Badge variant="outline">
                              Uncategorized
                            </Badge>
                          )}
                        </td>
                        <td className="p-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleTaxCategorize(transaction)}
                          >
                            Categorize
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </TabsContent>

          {/* Bulk Categorization */}
          <TabsContent value="bulk" className="space-y-4">
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">Bulk Tax Categorization</h2>
              <p className="text-gray-600 mb-4">
                Select multiple transactions from the Transactions tab to categorize them all at once.
              </p>
              <Button
                onClick={handleBulkTaxCategorize}
                disabled={selectedTransactions.length === 0}
                className="w-full"
              >
                Start Bulk Categorization ({selectedTransactions.length} selected)
              </Button>
            </Card>
          </TabsContent>

          {/* Chart of Accounts Management */}
          <TabsContent value="accounts" className="space-y-4">
            <ChartOfAccountsManager />
          </TabsContent>
        </Tabs>

        {/* Modals */}
        {selectedTransaction && (
          <TaxCategorizationModal
            isOpen={isTaxModalOpen}
            onClose={() => {
              setIsTaxModalOpen(false);
              setSelectedTransaction(null);
            }}
            transaction={selectedTransaction}
            onTransactionUpdated={handleTransactionUpdated}
          />
        )}

        <BulkTaxCategorization
          isOpen={isBulkTaxModalOpen}
          onClose={() => setIsBulkTaxModalOpen(false)}
          transactions={selectedTransactions}
          onTransactionsUpdated={handleBulkCategorized}
        />
      </div>
    </TooltipProvider>
  );
}

export default TaxSystemExample;