// Financial domain types

export interface Transaction {
  id: string;
  accountId: string;
  amount: number;
  description: string;
  date: string;
  category?: string;
  subcategory?: string;
  merchantName?: string;
  pending?: boolean;
}

export interface Account {
  id: string;
  name: string;
  officialName: string;
  type: AccountType;
  subtype: AccountSubtype;
  balances: AccountBalance;
  institutionId: string;
}

export interface AccountBalance {
  available: number | null;
  current: number | null;
  limit: number | null;
  isoCurrencyCode: string | null;
  unofficialCurrencyCode: string | null;
}

export enum AccountType {
  DEPOSITORY = 'depository',
  CREDIT = 'credit',
  LOAN = 'loan',
  INVESTMENT = 'investment',
  OTHER = 'other',
}

export enum AccountSubtype {
  // Depository
  CHECKING = 'checking',
  SAVINGS = 'savings',
  MONEY_MARKET = 'money market',
  CD = 'cd',
  // Credit
  CREDIT_CARD = 'credit card',
  // Investment
  BROKERAGE = 'brokerage',
  IRA = 'ira',
  FOUR_OH_ONE_K = '401k',
}

export interface FinancialReport {
  id: string;
  type: ReportType;
  period: ReportPeriod;
  generatedAt: string;
  data: Record<string, unknown>;
}

export enum ReportType {
  PROFIT_LOSS = 'profit_loss',
  BALANCE_SHEET = 'balance_sheet',
  CASH_FLOW = 'cash_flow',
  OWNER_PACKAGE = 'owner_package',
}

export interface ReportPeriod {
  startDate: string;
  endDate: string;
  label: string;
}
