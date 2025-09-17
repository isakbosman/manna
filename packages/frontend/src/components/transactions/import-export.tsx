import React from 'react'
import {
  UploadIcon,
  DownloadIcon,
  FileSpreadsheetIcon,
  CheckCircleIcon,
  XCircleIcon,
  AlertCircleIcon
} from 'lucide-react'
import { Button } from '../ui/button'
import { Modal } from '../ui/modal'
import { Badge } from '../ui/badge'
import { transactionsApi, TransactionFilters } from '@/lib/api'
import { cn } from '../../lib/utils'

interface ImportExportProps {
  filters?: TransactionFilters
  selectedTransactionIds?: string[]
  onTransactionsImported?: () => void
  className?: string
}

export function ImportExport({
  filters,
  selectedTransactionIds,
  onTransactionsImported,
  className
}: ImportExportProps) {
  const [showImportModal, setShowImportModal] = React.useState(false)
  const [showExportModal, setShowExportModal] = React.useState(false)
  const [isExporting, setIsExporting] = React.useState(false)
  const [isImporting, setIsImporting] = React.useState(false)
  const [importResults, setImportResults] = React.useState<any>(null)
  const [dragOver, setDragOver] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const handleExport = async (format: 'csv' | 'xlsx') => {
    try {
      setIsExporting(true)
      
      if (selectedTransactionIds && selectedTransactionIds.length > 0) {
        // Export selected transactions
        await transactionsApi.exportTransactions(
          { transaction_ids: selectedTransactionIds } as any,
          format
        )
      } else {
        // Export with current filters
        await transactionsApi.exportTransactions(filters, format)
      }
      
      setShowExportModal(false)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    if (!file) return
    
    // Validate file type
    const validTypes = ['.csv', '.xlsx', '.xls']
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    
    if (!validTypes.includes(fileExtension)) {
      alert('Please upload a CSV or Excel file')
      return
    }

    try {
      setIsImporting(true)
      
      // For demo purposes, we'll simulate the import
      // In a real implementation, this would upload to the backend
      const formData = new FormData()
      formData.append('file', file)
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Mock import results
      setImportResults({
        total_rows: 150,
        imported: 142,
        skipped: 8,
        errors: [],
        warnings: [
          'Row 23: Amount format unclear, please verify',
          'Row 67: Category not found, assigned to "Other"',
          'Row 89: Date format unclear, using current date'
        ]
      })
      
      if (onTransactionsImported) {
        onTransactionsImported()
      }
    } catch (error) {
      console.error('Import failed:', error)
      setImportResults({
        total_rows: 0,
        imported: 0,
        skipped: 0,
        errors: ['Failed to process file. Please check the format and try again.'],
        warnings: []
      })
    } finally {
      setIsImporting(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  return (
    <>
      <div className={cn('flex items-center gap-2', className)}>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowImportModal(true)}
        >
          <UploadIcon className="h-4 w-4 mr-1" />
          Import
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowExportModal(true)}
        >
          <DownloadIcon className="h-4 w-4 mr-1" />
          Export
        </Button>
      </div>

      {/* Import Modal */}
      <Modal
        isOpen={showImportModal}
        onClose={() => {
          setShowImportModal(false)
          setImportResults(null)
        }}
        title="Import Transactions"
        description="Upload a CSV or Excel file containing your transactions"
        size="lg"
      >
        <div className="space-y-6">
          {/* File Upload Area */}
          {!importResults && (
            <div
              className={cn(
                'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
                dragOver ? 'border-primary-400 bg-primary-50' : 'border-neutral-300',
                isImporting && 'opacity-50 pointer-events-none'
              )}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              {isImporting ? (
                <div className="space-y-4">
                  <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary-600 mx-auto" />
                  <p className="text-sm text-neutral-600">Processing file...</p>
                </div>
              ) : (
                <>
                  <FileSpreadsheetIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
                  <p className="text-lg font-medium text-neutral-900 mb-2">
                    Drop your file here or click to browse
                  </p>
                  <p className="text-sm text-neutral-600 mb-4">
                    Supports CSV, Excel (.xlsx, .xls) files up to 10MB
                  </p>
                  
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isImporting}
                  >
                    Choose File
                  </Button>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) handleFileUpload(file)
                    }}
                    className="hidden"
                  />
                </>
              )}
            </div>
          )}

          {/* Import Results */}
          {importResults && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="h-5 w-5 text-success-600" />
                <h3 className="font-medium text-success-900">Import Complete</h3>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-success-50 rounded-lg">
                  <p className="text-2xl font-bold text-success-600">{importResults.imported}</p>
                  <p className="text-sm text-success-700">Imported</p>
                </div>
                
                <div className="text-center p-3 bg-warning-50 rounded-lg">
                  <p className="text-2xl font-bold text-warning-600">{importResults.skipped}</p>
                  <p className="text-sm text-warning-700">Skipped</p>
                </div>
                
                <div className="text-center p-3 bg-neutral-50 rounded-lg">
                  <p className="text-2xl font-bold text-neutral-600">{importResults.total_rows}</p>
                  <p className="text-sm text-neutral-700">Total Rows</p>
                </div>
              </div>
              
              {/* Warnings */}
              {importResults.warnings.length > 0 && (
                <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircleIcon className="h-4 w-4 text-warning-600" />
                    <h4 className="font-medium text-warning-900">Warnings</h4>
                  </div>
                  <ul className="text-sm text-warning-700 space-y-1">
                    {importResults.warnings.map((warning: string, index: number) => (
                      <li key={index}>• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Errors */}
              {importResults.errors.length > 0 && (
                <div className="bg-error-50 border border-error-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <XCircleIcon className="h-4 w-4 text-error-600" />
                    <h4 className="font-medium text-error-900">Errors</h4>
                  </div>
                  <ul className="text-sm text-error-700 space-y-1">
                    {importResults.errors.map((error: string, index: number) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Format Guide */}
          {!importResults && (
            <div className="bg-info-50 border border-info-200 rounded-lg p-4">
              <h4 className="font-medium text-info-900 mb-2">File Format Guide</h4>
              <p className="text-sm text-info-700 mb-2">Your file should include these columns:</p>
              <div className="grid grid-cols-2 gap-2 text-xs text-info-600">
                <div>• Date (required)</div>
                <div>• Amount (required)</div>
                <div>• Description (required)</div>
                <div>• Category (optional)</div>
                <div>• Merchant (optional)</div>
                <div>• Account (optional)</div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowImportModal(false)
                setImportResults(null)
              }}
            >
              {importResults ? 'Close' : 'Cancel'}
            </Button>
            
            {importResults && (
              <Button
                onClick={() => {
                  setShowImportModal(false)
                  setImportResults(null)
                }}
              >
                Done
              </Button>
            )}
          </div>
        </div>
      </Modal>

      {/* Export Modal */}
      <Modal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="Export Transactions"
        description={selectedTransactionIds?.length 
          ? `Export ${selectedTransactionIds.length} selected transactions`
          : "Export all transactions with current filters"
        }
      >
        <div className="space-y-4">
          <div className="text-sm text-neutral-600">
            {selectedTransactionIds?.length 
              ? `${selectedTransactionIds.length} selected transactions will be exported.`
              : "All transactions matching your current filters will be exported."
            }
          </div>
          
          <div className="flex flex-col gap-2">
            <Button
              onClick={() => handleExport('csv')}
              loading={isExporting}
              disabled={isExporting}
              className="justify-start"
            >
              <FileSpreadsheetIcon className="h-4 w-4 mr-2" />
              Export as CSV
              <Badge variant="outline" className="ml-auto">
                Recommended
              </Badge>
            </Button>
            
            <Button
              variant="outline"
              onClick={() => handleExport('xlsx')}
              loading={isExporting}
              disabled={isExporting}
              className="justify-start"
            >
              <FileSpreadsheetIcon className="h-4 w-4 mr-2" />
              Export as Excel (.xlsx)
            </Button>
          </div>
          
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setShowExportModal(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </>
  )
}