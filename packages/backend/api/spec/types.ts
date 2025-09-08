/**
 * TypeScript type definitions for Manna Financial Management Platform API
 * Generated from OpenAPI 3.0 specification
 */

// ============================================================================
// Authentication Types
// ============================================================================

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  created_at: string;
  is_active: boolean;
}

// ============================================================================
// Plaid Integration Types
// ============================================================================

export interface LinkTokenRequest {
  user_id: string;
  products?: PlaidProduct[];
  country_codes?: string[];
}

export type PlaidProduct = 'transactions' | 'auth' | 'identity' | 'assets';

export interface LinkTokenResponse {
  link_token: string;
  expiration: string;
}

export interface ExchangeTokenRequest {
  public_token: string;
  account_ids?: string[];
}

export interface ExchangeTokenResponse {
  accounts: PlaidAccount[];
  item_id: string;
  sync_status: SyncStatus;
}

export type SyncStatus = 'pending' | 'syncing' | 'complete' | 'error';

export interface PlaidAccount {
  account_id: string;
  plaid_account_id: string;
  name: string;
  official_name?: string;
  type: PlaidAccountType;
  subtype: string;
  mask: string;
  institution_name: string;
  balance: AccountBalance;
  is_business: boolean;
  last_sync?: string;
}

export type PlaidAccountType =
  | 'depository'
  | 'credit'
  | 'loan'
  | 'investment'
  | 'other';

export interface AccountBalance {
  available?: number;
  current: number;
  limit?: number;
  iso_currency_code: string;
}

export interface SyncRequest {
  account_ids?: string[];
  force_full_sync?: boolean;
}

export interface SyncResponse {
  sync_id: string;
  status: SyncJobStatus;
  accounts: string[];
  estimated_completion?: string;
}

export type SyncJobStatus =
  | 'initiated'
  | 'in_progress'
  | 'completed'
  | 'failed';

export interface PlaidWebhook {
  webhook_type: string;
  webhook_code: string;
  item_id: string;
  error?: Record<string, unknown>;
  new_transactions?: number;
  removed_transactions?: string[];
}

// ============================================================================
// Transaction Types
// ============================================================================

export interface Transaction {
  id: string;
  plaid_transaction_id?: string;
  account_id: string;
  amount: number;
  date: string;
  authorized_date?: string;
  name: string;
  merchant_name?: string;
  category?: string;
  subcategory?: string;
  ml_category?: string;
  ml_confidence?: number;
  user_category?: string;
  is_business: boolean;
  is_tax_deductible: boolean;
  pending: boolean;
  location?: TransactionLocation;
  payment_method?: string;
  notes?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface TransactionLocation {
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  country?: string;
  lat?: number;
  lon?: number;
}

export interface TransactionListRequest {
  page?: number;
  per_page?: number;
  account_id?: string;
  category?: string;
  start_date?: string;
  end_date?: string;
  min_amount?: number;
  max_amount?: number;
  is_business?: boolean;
  needs_review?: boolean;
  search?: string;
  sort_by?: TransactionSortField;
  sort_order?: SortOrder;
}

export type TransactionSortField = 'date' | 'amount' | 'merchant_name';
export type SortOrder = 'asc' | 'desc';

export interface TransactionListResponse {
  transactions: Transaction[];
  pagination: Pagination;
  summary: TransactionSummary;
}

export interface TransactionSummary {
  total_transactions: number;
  total_amount: number;
  income_total: number;
  expense_total: number;
  by_category: Record<string, number>;
}

export interface TransactionUpdateRequest {
  category?: string;
  subcategory?: string;
  is_business?: boolean;
  is_tax_deductible?: boolean;
  notes?: string;
  tags?: string[];
}

export interface BulkUpdateRequest {
  transaction_ids: string[];
  updates: TransactionUpdateRequest;
}

export interface BulkUpdateResponse {
  updated_count: number;
  failed_count: number;
  failed_transactions: BulkUpdateFailure[];
}

export interface BulkUpdateFailure {
  transaction_id: string;
  error: string;
}

export interface ExportRequest {
  format: ExportFormat;
  start_date: string;
  end_date: string;
  account_ids?: string[];
  categories?: string[];
  is_business?: boolean;
}

export type ExportFormat = 'csv' | 'excel' | 'qbo';

// ============================================================================
// Financial Reports Types
// ============================================================================

export interface PnLReportRequest {
  start_date: string;
  end_date: string;
  is_business?: boolean;
  compare_to_previous?: boolean;
}

export interface PnLReport {
  period_start: string;
  period_end: string;
  income: IncomeStatement;
  expenses: ExpenseStatement;
  net_income: number;
  comparison?: PnLComparison;
  charts: ReportCharts;
}

export interface IncomeStatement {
  total: number;
  by_category: Record<string, number>;
}

export interface ExpenseStatement {
  total: number;
  by_category: Record<string, number>;
}

export interface PnLComparison {
  previous_period: {
    income: number;
    expenses: number;
    net_income: number;
  };
  change_percent: {
    income: number;
    expenses: number;
    net_income: number;
  };
}

export interface BalanceSheetRequest {
  as_of_date: string;
  is_business?: boolean;
}

export interface BalanceSheet {
  as_of_date: string;
  assets: Assets;
  liabilities: Liabilities;
  equity: Equity;
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
}

export interface Assets {
  current_assets: {
    cash: number;
    checking: number;
    savings: number;
    accounts_receivable: number;
  };
  fixed_assets: {
    equipment: number;
    furniture: number;
  };
}

export interface Liabilities {
  current_liabilities: {
    accounts_payable: number;
    credit_cards: number;
    accrued_expenses: number;
  };
  long_term_liabilities: {
    loans: number;
  };
}

export interface Equity {
  owner_equity: number;
  retained_earnings: number;
}

export interface CashFlowReportRequest {
  start_date: string;
  end_date: string;
  is_business?: boolean;
}

export interface CashFlowReport {
  period_start: string;
  period_end: string;
  operating_activities: CashFlowSection;
  investing_activities: CashFlowSection;
  financing_activities: CashFlowSection;
  net_cash_flow: number;
  beginning_cash: number;
  ending_cash: number;
}

export interface CashFlowSection {
  total: number;
  items: Record<string, number>;
}

export interface KPIReportRequest {
  period?: KPIPeriod;
  as_of_date?: string;
}

export type KPIPeriod = 'month' | 'quarter' | 'year';

export interface KPIReport {
  period: string;
  effective_hourly_rate: number;
  utilization_percentage: number;
  accounts_receivable_aging: ARAgingReport;
  project_margins: ProjectMargin[];
  cash_runway: {
    months: number;
    based_on_monthly_burn: number;
  };
  expense_ratios: Record<string, number>;
}

export interface ARAgingReport {
  total_outstanding: number;
  current: number;
  days_30: number;
  days_60: number;
  days_90_plus: number;
}

export interface ProjectMargin {
  project_name: string;
  revenue: number;
  costs: number;
  margin_percent: number;
}

export interface ReportGenerationRequest {
  report_type: ReportType;
  parameters: Record<string, unknown>;
  format?: ReportFormat;
  delivery_method?: DeliveryMethod;
}

export type ReportType =
  | 'pnl'
  | 'balance_sheet'
  | 'cash_flow'
  | 'tax_summary'
  | 'custom';
export type ReportFormat = 'json' | 'pdf' | 'excel';
export type DeliveryMethod = 'api' | 'email' | 'webhook';

export interface ReportGenerationResponse {
  report_id: string;
  status: ReportGenerationStatus;
  estimated_completion?: string;
  download_url?: string;
}

export type ReportGenerationStatus =
  | 'queued'
  | 'generating'
  | 'completed'
  | 'failed';

export interface ReportCharts {
  income_trend: ChartDataPoint[];
  expense_breakdown: PieChartDataPoint[];
}

export interface ChartDataPoint {
  period: string;
  value: number;
}

export interface PieChartDataPoint {
  category: string;
  value: number;
  percentage: number;
}

// ============================================================================
// ML Categorization Types
// ============================================================================

export interface CategorizationRequest {
  transaction_ids: string[];
  force_recategorize?: boolean;
}

export interface CategorizationResponse {
  categorized_count: number;
  results: CategorizationResult[];
}

export interface CategorizationResult {
  transaction_id: string;
  predicted_category: string;
  confidence: number;
  applied: boolean;
}

export interface TrainingRequest {
  include_recent_feedback?: boolean;
  training_data_cutoff?: string;
}

export interface TrainingResponse {
  training_id: string;
  status: TrainingStatus;
  estimated_completion?: string;
}

export type TrainingStatus = 'queued' | 'training' | 'completed' | 'failed';

export interface SuggestionsRequest {
  limit?: number;
  confidence_threshold?: number;
}

export interface SuggestionsResponse {
  suggestions: CategorySuggestion[];
}

export interface CategorySuggestion {
  transaction: Transaction;
  suggested_category: string;
  confidence: number;
  reasoning: string;
}

export interface FeedbackRequest {
  transaction_id: string;
  predicted_category: string;
  correct_category: string;
  was_correct: boolean;
  feedback_notes?: string;
}

// ============================================================================
// Account Management Types
// ============================================================================

export interface Account {
  id: string;
  plaid_account_id?: string;
  name: string;
  official_name?: string;
  type: PlaidAccountType;
  subtype: string;
  mask: string;
  institution_name: string;
  institution_id: string;
  balance: AccountBalance;
  is_business: boolean;
  is_active: boolean;
  last_sync?: string;
  sync_status: AccountSyncStatus;
  created_at: string;
}

export type AccountSyncStatus = 'healthy' | 'error' | 'requires_update';

export interface ConnectAccountRequest {
  institution_id: string;
  public_token: string;
}

export interface ConnectAccountResponse {
  connection_id: string;
  status: ConnectionStatus;
  accounts: Account[];
}

export type ConnectionStatus =
  | 'initiated'
  | 'connecting'
  | 'connected'
  | 'failed';

export interface RefreshAccountResponse {
  refresh_id: string;
  status: RefreshStatus;
  estimated_completion?: string;
}

export type RefreshStatus = 'initiated' | 'refreshing' | 'completed' | 'failed';

// ============================================================================
// WebSocket Types
// ============================================================================

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: Record<string, unknown>;
  timestamp: string;
}

export type WebSocketMessageType =
  | 'transaction_added'
  | 'categorization_complete'
  | 'sync_status'
  | 'report_ready'
  | 'error';

export interface TransactionAddedMessage extends WebSocketMessage {
  type: 'transaction_added';
  data: {
    transaction: Transaction;
    account_id: string;
  };
}

export interface CategorizationCompleteMessage extends WebSocketMessage {
  type: 'categorization_complete';
  data: {
    transaction_ids: string[];
    categorized_count: number;
  };
}

export interface SyncStatusMessage extends WebSocketMessage {
  type: 'sync_status';
  data: {
    sync_id: string;
    status: SyncJobStatus;
    account_ids: string[];
    progress?: number;
  };
}

export interface ReportReadyMessage extends WebSocketMessage {
  type: 'report_ready';
  data: {
    report_id: string;
    report_type: ReportType;
    download_url: string;
  };
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  data: {
    error_code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

// ============================================================================
// Common Types
// ============================================================================

export interface Pagination {
  page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface MessageResponse {
  message: string;
}

export interface ApiError {
  error: string;
  message: string;
  code: string;
  details?: Record<string, unknown>;
  timestamp: string;
  request_id: string;
}

// ============================================================================
// API Client Types
// ============================================================================

export interface ApiConfig {
  baseURL: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  headers?: Record<string, string>;
}

export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
}

export interface ApiRequestConfig {
  params?: Record<string, unknown>;
  headers?: Record<string, string>;
  timeout?: number;
}

// ============================================================================
// Rate Limiting Types
// ============================================================================

export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: string;
  retry_after?: number;
}

export interface RateLimitError extends ApiError {
  code: 'RATE_LIMIT_EXCEEDED';
  rate_limit_info: RateLimitInfo;
}

// ============================================================================
// Webhook Types
// ============================================================================

export interface WebhookPayload {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
  signature: string;
}

export interface WebhookConfig {
  url: string;
  events: string[];
  secret: string;
  active: boolean;
}

// ============================================================================
// Type Guards
// ============================================================================

export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'error' in error &&
    'message' in error &&
    'code' in error
  );
}

export function isRateLimitError(error: unknown): error is RateLimitError {
  return isApiError(error) && error.code === 'RATE_LIMIT_EXCEEDED';
}

export function isTransactionAddedMessage(
  message: WebSocketMessage
): message is TransactionAddedMessage {
  return message.type === 'transaction_added';
}

export function isSyncStatusMessage(
  message: WebSocketMessage
): message is SyncStatusMessage {
  return message.type === 'sync_status';
}

export function isReportReadyMessage(
  message: WebSocketMessage
): message is ReportReadyMessage {
  return message.type === 'report_ready';
}

// ============================================================================
// Utility Types
// ============================================================================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type Required<T, K extends keyof T> = T & { [P in K]-?: T[P] };
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// ============================================================================
// Validation Types
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  value?: unknown;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

// ============================================================================
// Filter and Search Types
// ============================================================================

export interface DateRange {
  start_date: string;
  end_date: string;
}

export interface AmountRange {
  min_amount?: number;
  max_amount?: number;
}

export interface TransactionFilters extends DateRange, AmountRange {
  account_ids?: string[];
  categories?: string[];
  is_business?: boolean;
  needs_review?: boolean;
  search?: string;
  tags?: string[];
}

export interface SearchRequest {
  query: string;
  filters?: TransactionFilters;
  sort?: {
    field: string;
    order: SortOrder;
  };
  pagination?: {
    page: number;
    per_page: number;
  };
}

// ============================================================================
// Export Types
// ============================================================================

export {
  // Re-export commonly used types
  type Transaction as TransactionType,
  type Account as AccountType,
  type User as UserType,
  type PnLReport as PnLReportType,
  type BalanceSheet as BalanceSheetType,
  type CashFlowReport as CashFlowReportType,
};
