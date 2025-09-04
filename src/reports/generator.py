"""CPA-ready report generator for financial statements and tax documents."""

import pandas as pd
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import xlsxwriter

class ReportGenerator:
    """Generate CPA-ready financial reports and exports."""
    
    def __init__(self, session):
        self.session = session
        self.styles = getSampleStyleSheet()
    
    def generate_cpa_package(self, year: int, quarter: Optional[int] = None) -> Dict:
        """Generate complete CPA package with all required documents."""
        package = {
            'generated_date': datetime.now().isoformat(),
            'year': year,
            'quarter': quarter,
            'reports': {}
        }
        
        # Generate all reports
        package['reports']['profit_loss'] = self.generate_profit_loss(year, quarter)
        package['reports']['balance_sheet'] = self.generate_balance_sheet(year, quarter)
        package['reports']['cash_flow'] = self.generate_cash_flow(year, quarter)
        package['reports']['general_ledger'] = self.generate_general_ledger(year, quarter)
        package['reports']['trial_balance'] = self.generate_trial_balance(year, quarter)
        package['reports']['tax_summary'] = self.generate_tax_summary(year, quarter)
        package['reports']['expense_detail'] = self.generate_expense_detail(year, quarter)
        
        # Save to files
        self._save_cpa_package(package, year, quarter)
        
        return package
    
    def generate_profit_loss(self, year: int, quarter: Optional[int] = None) -> Dict:
        """Generate P&L statement."""
        # Calculate date range
        if quarter:
            start_date = datetime(year, (quarter-1)*3 + 1, 1)
            if quarter == 4:
                end_date = datetime(year, 12, 31)
            else:
                end_date = datetime(year, quarter*3 + 1, 1) - timedelta(days=1)
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
        
        pl = {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'revenue': {},
            'expenses': {},
            'summary': {}
        }
        
        # Revenue categories
        pl['revenue']['consulting'] = self._calculate_revenue('consulting', start_date, end_date)
        pl['revenue']['products'] = self._calculate_revenue('products', start_date, end_date)
        pl['revenue']['other'] = self._calculate_revenue('other', start_date, end_date)
        pl['revenue']['total'] = sum(pl['revenue'].values())
        
        # Expense categories (IRS Schedule C categories)
        expense_categories = [
            'advertising', 'car_and_truck', 'commissions', 'contract_labor',
            'depletion', 'depreciation', 'employee_benefit', 'insurance',
            'interest', 'legal_professional', 'office_expense', 'pension',
            'rent_lease', 'repairs', 'supplies', 'taxes_licenses', 'travel',
            'meals', 'utilities', 'wages', 'other'
        ]
        
        for category in expense_categories:
            pl['expenses'][category] = self._calculate_expense(category, start_date, end_date)
        
        pl['expenses']['total'] = sum(pl['expenses'].values())
        
        # Summary
        pl['summary']['gross_profit'] = pl['revenue']['total']
        pl['summary']['operating_income'] = pl['revenue']['total'] - pl['expenses']['total']
        pl['summary']['net_income'] = pl['summary']['operating_income']  # Simplified
        
        return pl
    
    def generate_balance_sheet(self, year: int, quarter: Optional[int] = None) -> Dict:
        """Generate balance sheet."""
        if quarter:
            as_of_date = self._get_quarter_end_date(year, quarter)
        else:
            as_of_date = datetime(year, 12, 31)
        
        balance_sheet = {
            'as_of_date': as_of_date.isoformat(),
            'assets': {
                'current': {},
                'fixed': {},
                'other': {}
            },
            'liabilities': {
                'current': {},
                'long_term': {}
            },
            'equity': {}
        }
        
        # Assets
        balance_sheet['assets']['current']['cash'] = self._get_cash_balance(as_of_date)
        balance_sheet['assets']['current']['accounts_receivable'] = self._get_ar_balance(as_of_date)
        balance_sheet['assets']['current']['prepaid_expenses'] = 0
        balance_sheet['assets']['current']['total'] = sum(balance_sheet['assets']['current'].values())
        
        balance_sheet['assets']['fixed']['equipment'] = self._get_equipment_value(as_of_date)
        balance_sheet['assets']['fixed']['accumulated_depreciation'] = self._get_depreciation(as_of_date)
        balance_sheet['assets']['fixed']['total'] = (
            balance_sheet['assets']['fixed']['equipment'] - 
            balance_sheet['assets']['fixed']['accumulated_depreciation']
        )
        
        balance_sheet['assets']['total'] = (
            balance_sheet['assets']['current']['total'] + 
            balance_sheet['assets']['fixed']['total']
        )
        
        # Liabilities
        balance_sheet['liabilities']['current']['accounts_payable'] = self._get_ap_balance(as_of_date)
        balance_sheet['liabilities']['current']['credit_cards'] = self._get_cc_balance(as_of_date)
        balance_sheet['liabilities']['current']['total'] = sum(balance_sheet['liabilities']['current'].values())
        
        balance_sheet['liabilities']['total'] = balance_sheet['liabilities']['current']['total']
        
        # Equity
        balance_sheet['equity']['retained_earnings'] = (
            balance_sheet['assets']['total'] - balance_sheet['liabilities']['total']
        )
        balance_sheet['equity']['total'] = balance_sheet['equity']['retained_earnings']
        
        return balance_sheet
    
    def generate_cash_flow(self, year: int, quarter: Optional[int] = None) -> Dict:
        """Generate cash flow statement."""
        if quarter:
            start_date = datetime(year, (quarter-1)*3 + 1, 1)
            end_date = self._get_quarter_end_date(year, quarter)
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
        
        cash_flow = {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'operating': {},
            'investing': {},
            'financing': {},
            'summary': {}
        }
        
        # Operating activities
        cash_flow['operating']['net_income'] = self._calculate_net_income(start_date, end_date)
        cash_flow['operating']['depreciation'] = self._calculate_depreciation(start_date, end_date)
        cash_flow['operating']['ar_change'] = self._calculate_ar_change(start_date, end_date)
        cash_flow['operating']['ap_change'] = self._calculate_ap_change(start_date, end_date)
        cash_flow['operating']['total'] = sum(cash_flow['operating'].values())
        
        # Investing activities
        cash_flow['investing']['equipment_purchases'] = self._calculate_equipment_purchases(start_date, end_date)
        cash_flow['investing']['total'] = cash_flow['investing']['equipment_purchases']
        
        # Financing activities
        cash_flow['financing']['owner_draws'] = self._calculate_owner_draws(start_date, end_date)
        cash_flow['financing']['total'] = cash_flow['financing']['owner_draws']
        
        # Summary
        cash_flow['summary']['beginning_cash'] = self._get_cash_balance(start_date)
        cash_flow['summary']['net_change'] = (
            cash_flow['operating']['total'] + 
            cash_flow['investing']['total'] + 
            cash_flow['financing']['total']
        )
        cash_flow['summary']['ending_cash'] = (
            cash_flow['summary']['beginning_cash'] + 
            cash_flow['summary']['net_change']
        )
        
        return cash_flow
    
    def generate_general_ledger(self, year: int, quarter: Optional[int] = None) -> pd.DataFrame:
        """Generate general ledger detail."""
        from src.utils.database import Transaction
        
        if quarter:
            start_date = datetime(year, (quarter-1)*3 + 1, 1)
            end_date = self._get_quarter_end_date(year, quarter)
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
        
        transactions = self.session.query(Transaction).filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(Transaction.date).all()
        
        ledger_data = []
        for txn in transactions:
            ledger_data.append({
                'Date': txn.date,
                'Account': txn.account.account_name,
                'Description': txn.merchant_name or txn.name,
                'Category': txn.category,
                'Debit': abs(txn.amount) if txn.amount > 0 else 0,
                'Credit': abs(txn.amount) if txn.amount < 0 else 0,
                'Balance': 0,  # Will be calculated
                'Tax Deductible': txn.is_tax_deductible,
                'Business': txn.is_business
            })
        
        return pd.DataFrame(ledger_data)
    
    def generate_trial_balance(self, year: int, quarter: Optional[int] = None) -> pd.DataFrame:
        """Generate trial balance."""
        if quarter:
            as_of_date = self._get_quarter_end_date(year, quarter)
        else:
            as_of_date = datetime(year, 12, 31)
        
        accounts = []
        
        # Asset accounts
        accounts.append({
            'Account': 'Cash',
            'Debit': self._get_cash_balance(as_of_date),
            'Credit': 0
        })
        accounts.append({
            'Account': 'Accounts Receivable',
            'Debit': self._get_ar_balance(as_of_date),
            'Credit': 0
        })
        accounts.append({
            'Account': 'Equipment',
            'Debit': self._get_equipment_value(as_of_date),
            'Credit': 0
        })
        
        # Liability accounts
        accounts.append({
            'Account': 'Accounts Payable',
            'Debit': 0,
            'Credit': self._get_ap_balance(as_of_date)
        })
        accounts.append({
            'Account': 'Credit Cards',
            'Debit': 0,
            'Credit': self._get_cc_balance(as_of_date)
        })
        
        # Calculate totals
        df = pd.DataFrame(accounts)
        df.loc['Total'] = df.sum()
        
        return df
    
    def generate_tax_summary(self, year: int, quarter: Optional[int] = None) -> Dict:
        """Generate tax summary for CPA."""
        tax_summary = {
            'year': year,
            'quarter': quarter,
            'business_income': {},
            'business_expenses': {},
            'quarterly_estimates': {},
            'deductions': {}
        }
        
        # Business income
        tax_summary['business_income']['gross_receipts'] = self._calculate_gross_receipts(year)
        tax_summary['business_income']['returns_allowances'] = 0
        tax_summary['business_income']['net_receipts'] = tax_summary['business_income']['gross_receipts']
        
        # Business expenses by Schedule C category
        schedule_c_categories = {
            'line_8': 'advertising',
            'line_9': 'car_and_truck',
            'line_10': 'commissions_fees',
            'line_11': 'contract_labor',
            'line_12': 'depletion',
            'line_13': 'depreciation',
            'line_14': 'employee_benefits',
            'line_15': 'insurance',
            'line_16a': 'mortgage_interest',
            'line_16b': 'other_interest',
            'line_17': 'legal_professional',
            'line_18': 'office_expense',
            'line_19': 'pension_profit_sharing',
            'line_20a': 'rent_vehicles',
            'line_20b': 'rent_other',
            'line_21': 'repairs_maintenance',
            'line_22': 'supplies',
            'line_23': 'taxes_licenses',
            'line_24a': 'travel',
            'line_24b': 'meals',
            'line_25': 'utilities',
            'line_26': 'wages',
            'line_27a': 'other_expenses'
        }
        
        for line, category in schedule_c_categories.items():
            tax_summary['business_expenses'][line] = self._calculate_schedule_c_expense(category, year)
        
        tax_summary['business_expenses']['total'] = sum(tax_summary['business_expenses'].values())
        
        # Net profit
        tax_summary['net_profit'] = (
            tax_summary['business_income']['net_receipts'] - 
            tax_summary['business_expenses']['total']
        )
        
        # Quarterly estimates
        for q in range(1, 5):
            tax_summary['quarterly_estimates'][f'Q{q}'] = {
                'federal': self._calculate_quarterly_federal(year, q),
                'state': self._calculate_quarterly_state(year, q),
                'self_employment': self._calculate_quarterly_se(year, q)
            }
        
        return tax_summary
    
    def generate_expense_detail(self, year: int, quarter: Optional[int] = None) -> pd.DataFrame:
        """Generate detailed expense report for tax purposes."""
        from src.utils.database import Transaction
        
        if quarter:
            start_date = datetime(year, (quarter-1)*3 + 1, 1)
            end_date = self._get_quarter_end_date(year, quarter)
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
        
        expenses = self.session.query(Transaction).filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_business == True,
            Transaction.amount < 0
        ).order_by(Transaction.category, Transaction.date).all()
        
        expense_data = []
        for exp in expenses:
            expense_data.append({
                'Date': exp.date.strftime('%Y-%m-%d'),
                'Merchant': exp.merchant_name or exp.name,
                'Category': exp.category,
                'Schedule C Line': self._map_to_schedule_c(exp.category),
                'Amount': abs(exp.amount),
                'Tax Deductible': exp.is_tax_deductible,
                'Notes': exp.notes or ''
            })
        
        return pd.DataFrame(expense_data)
    
    def export_to_excel(self, package: Dict, filename: str):
        """Export CPA package to Excel."""
        os.makedirs('reports', exist_ok=True)
        filepath = f"reports/{filename}"
        
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            # P&L Sheet
            pl_df = self._dict_to_dataframe(package['reports']['profit_loss'])
            pl_df.to_excel(writer, sheet_name='Profit & Loss', index=False)
            
            # Balance Sheet
            bs_df = self._dict_to_dataframe(package['reports']['balance_sheet'])
            bs_df.to_excel(writer, sheet_name='Balance Sheet', index=False)
            
            # Cash Flow
            cf_df = self._dict_to_dataframe(package['reports']['cash_flow'])
            cf_df.to_excel(writer, sheet_name='Cash Flow', index=False)
            
            # General Ledger
            package['reports']['general_ledger'].to_excel(writer, sheet_name='General Ledger', index=False)
            
            # Trial Balance
            package['reports']['trial_balance'].to_excel(writer, sheet_name='Trial Balance')
            
            # Tax Summary
            tax_df = self._dict_to_dataframe(package['reports']['tax_summary'])
            tax_df.to_excel(writer, sheet_name='Tax Summary', index=False)
            
            # Expense Detail
            package['reports']['expense_detail'].to_excel(writer, sheet_name='Expense Detail', index=False)
            
            # Format the Excel file
            workbook = writer.book
            money_format = workbook.add_format({'num_format': '$#,##0.00'})
            
            for worksheet in writer.sheets.values():
                worksheet.set_column('B:Z', 15, money_format)
    
    def export_to_pdf(self, package: Dict, filename: str):
        """Export CPA package to PDF."""
        os.makedirs('reports', exist_ok=True)
        filepath = f"reports/{filename}"
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Title
        title = Paragraph(f"Financial Reports - {package['year']}", self.styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # P&L Statement
        elements.append(Paragraph("Profit & Loss Statement", self.styles['Heading1']))
        pl_data = self._format_for_pdf(package['reports']['profit_loss'])
        pl_table = Table(pl_data)
        pl_table.setStyle(self._get_table_style())
        elements.append(pl_table)
        elements.append(Spacer(1, 20))
        
        # Balance Sheet
        elements.append(Paragraph("Balance Sheet", self.styles['Heading1']))
        bs_data = self._format_for_pdf(package['reports']['balance_sheet'])
        bs_table = Table(bs_data)
        bs_table.setStyle(self._get_table_style())
        elements.append(bs_table)
        
        doc.build(elements)
    
    def export_to_quickbooks(self, package: Dict, filename: str):
        """Export to QuickBooks IIF format."""
        os.makedirs('reports', exist_ok=True)
        filepath = f"reports/{filename}"
        
        # IIF format for QuickBooks import
        iif_content = "!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tMEMO\n"
        iif_content += "!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tMEMO\n"
        iif_content += "!ENDTRNS\n"
        
        # Add transactions
        gl = package['reports']['general_ledger']
        for _, row in gl.iterrows():
            iif_content += f"TRNS\t\tGENERAL JOURNAL\t{row['Date']}\t{row['Account']}\t\t\t{row['Debit'] - row['Credit']}\t{row['Description']}\n"
            iif_content += f"SPL\t\tGENERAL JOURNAL\t{row['Date']}\t{row['Category']}\t\t\t{row['Credit'] - row['Debit']}\t\n"
            iif_content += "ENDTRNS\n"
        
        with open(filepath, 'w') as f:
            f.write(iif_content)
    
    # Helper methods
    def _get_quarter_end_date(self, year: int, quarter: int) -> datetime:
        if quarter == 1:
            return datetime(year, 3, 31)
        elif quarter == 2:
            return datetime(year, 6, 30)
        elif quarter == 3:
            return datetime(year, 9, 30)
        else:
            return datetime(year, 12, 31)
    
    def _calculate_revenue(self, category: str, start_date: datetime, end_date: datetime) -> float:
        # Placeholder - would query database
        return 25000.0
    
    def _calculate_expense(self, category: str, start_date: datetime, end_date: datetime) -> float:
        # Placeholder - would query database
        return 1500.0
    
    def _get_cash_balance(self, as_of_date: datetime) -> float:
        from src.utils.database import Account
        cash_accounts = self.session.query(Account).filter(
            Account.account_type.in_(['checking', 'savings'])
        ).all()
        return sum(acc.current_balance for acc in cash_accounts)
    
    def _get_ar_balance(self, as_of_date: datetime) -> float:
        return 15000.0  # Placeholder
    
    def _get_equipment_value(self, as_of_date: datetime) -> float:
        return 25000.0  # Placeholder
    
    def _get_depreciation(self, as_of_date: datetime) -> float:
        return 5000.0  # Placeholder
    
    def _get_ap_balance(self, as_of_date: datetime) -> float:
        return 3000.0  # Placeholder
    
    def _get_cc_balance(self, as_of_date: datetime) -> float:
        from src.utils.database import Account
        cc_accounts = self.session.query(Account).filter(
            Account.account_type == 'credit'
        ).all()
        return sum(abs(acc.current_balance) for acc in cc_accounts)
    
    def _calculate_net_income(self, start_date: datetime, end_date: datetime) -> float:
        return 35000.0  # Placeholder
    
    def _calculate_depreciation(self, start_date: datetime, end_date: datetime) -> float:
        return 1250.0  # Placeholder
    
    def _calculate_ar_change(self, start_date: datetime, end_date: datetime) -> float:
        return -2000.0  # Placeholder
    
    def _calculate_ap_change(self, start_date: datetime, end_date: datetime) -> float:
        return 500.0  # Placeholder
    
    def _calculate_equipment_purchases(self, start_date: datetime, end_date: datetime) -> float:
        return -5000.0  # Placeholder
    
    def _calculate_owner_draws(self, start_date: datetime, end_date: datetime) -> float:
        return -10000.0  # Placeholder
    
    def _calculate_gross_receipts(self, year: int) -> float:
        return 150000.0  # Placeholder
    
    def _calculate_schedule_c_expense(self, category: str, year: int) -> float:
        return 2000.0  # Placeholder
    
    def _calculate_quarterly_federal(self, year: int, quarter: int) -> float:
        return 5000.0  # Placeholder
    
    def _calculate_quarterly_state(self, year: int, quarter: int) -> float:
        return 1500.0  # Placeholder
    
    def _calculate_quarterly_se(self, year: int, quarter: int) -> float:
        return 2500.0  # Placeholder
    
    def _map_to_schedule_c(self, category: str) -> str:
        """Map category to Schedule C line item."""
        mapping = {
            'Advertising': 'Line 8',
            'Office Supplies': 'Line 18',
            'Software': 'Line 18',
            'Professional Services': 'Line 17',
            'Travel': 'Line 24a',
            'Meals': 'Line 24b',
            'Equipment': 'Line 13',
            'Insurance': 'Line 15',
            'Utilities': 'Line 25',
            'Bank Fees': 'Line 27a'
        }
        return mapping.get(category, 'Line 27a')
    
    def _dict_to_dataframe(self, data: Dict) -> pd.DataFrame:
        """Convert nested dict to DataFrame for Excel export."""
        rows = []
        for key, value in data.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    rows.append({'Category': key, 'Item': subkey, 'Amount': subvalue})
            else:
                rows.append({'Category': key, 'Item': '', 'Amount': value})
        return pd.DataFrame(rows)
    
    def _format_for_pdf(self, data: Dict) -> List[List]:
        """Format dict data for PDF table."""
        rows = [['Item', 'Amount']]
        for key, value in data.items():
            if isinstance(value, dict):
                rows.append([key.upper(), ''])
                for subkey, subvalue in value.items():
                    rows.append([f"  {subkey}", f"${subvalue:,.2f}"])
            else:
                rows.append([key, f"${value:,.2f}"])
        return rows
    
    def _get_table_style(self) -> TableStyle:
        """Get standard table style for PDF."""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
    
    def _save_cpa_package(self, package: Dict, year: int, quarter: Optional[int] = None):
        """Save CPA package to multiple formats."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        period = f"Q{quarter}_{year}" if quarter else f"FY_{year}"
        
        # Save as JSON
        os.makedirs('reports/cpa', exist_ok=True)
        with open(f'reports/cpa/{period}_{timestamp}.json', 'w') as f:
            json.dump(package, f, indent=2, default=str)
        
        # Export to Excel
        self.export_to_excel(package, f'cpa/{period}_{timestamp}.xlsx')
        
        # Export to PDF
        self.export_to_pdf(package, f'cpa/{period}_{timestamp}.pdf')
        
        # Export to QuickBooks
        self.export_to_quickbooks(package, f'cpa/{period}_{timestamp}.iif')