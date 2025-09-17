"""Report generation service for financial statements and tax documents."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
import logging

from ..database.models import Transaction, Account, Category, User
from ..schemas.reports import (
    ReportType, ReportPeriod, ProfitLossReport, BalanceSheetReport,
    CashFlowReport, TaxSummaryReport, OwnerPackageReport
)

logger = logging.getLogger(__name__)


class ReportGeneratorService:
    """Service for generating financial reports."""

    def __init__(self, db: Session):
        self.db = db

    def generate_profit_loss(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        is_business: bool = True
    ) -> Dict[str, Any]:
        """Generate P&L statement."""

        # Get all transactions in the period
        transactions = self.db.query(Transaction).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.is_business == is_business if is_business else True
            )
        ).all()

        # Initialize report structure
        report = {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'revenue': {},
            'expenses': {},
            'summary': {}
        }

        # Categorize transactions
        for transaction in transactions:
            if transaction.amount > 0:  # Revenue
                category = transaction.category_name or 'uncategorized'
                if category not in report['revenue']:
                    report['revenue'][category] = 0
                report['revenue'][category] += float(transaction.amount)
            else:  # Expense
                category = transaction.category_name or 'uncategorized'
                if category not in report['expenses']:
                    report['expenses'][category] = 0
                report['expenses'][category] += abs(float(transaction.amount))

        # Calculate totals
        report['revenue']['total'] = sum(report['revenue'].values())
        report['expenses']['total'] = sum(report['expenses'].values())

        # Summary
        report['summary']['gross_profit'] = report['revenue']['total']
        report['summary']['operating_income'] = report['revenue']['total'] - report['expenses']['total']
        report['summary']['net_income'] = report['summary']['operating_income']

        return report

    def generate_balance_sheet(
        self,
        user_id: str,
        as_of_date: datetime
    ) -> Dict[str, Any]:
        """Generate balance sheet."""

        # Get all accounts
        accounts = self.db.query(Account).filter(
            Account.user_id == user_id
        ).all()

        balance_sheet = {
            'as_of_date': as_of_date.isoformat(),
            'assets': {
                'current': {},
                'fixed': {},
                'total': 0
            },
            'liabilities': {
                'current': {},
                'long_term': {},
                'total': 0
            },
            'equity': {
                'retained_earnings': 0,
                'total': 0
            }
        }

        # Categorize accounts
        for account in accounts:
            balance = float(account.current_balance or 0)

            if account.type in ['depository', 'investment']:
                # Assets
                if account.subtype in ['checking', 'savings', 'money_market']:
                    balance_sheet['assets']['current'][account.name] = balance
                else:
                    balance_sheet['assets']['fixed'][account.name] = balance
            elif account.type in ['credit', 'loan']:
                # Liabilities
                if account.subtype == 'credit_card':
                    balance_sheet['liabilities']['current'][account.name] = abs(balance)
                else:
                    balance_sheet['liabilities']['long_term'][account.name] = abs(balance)

        # Calculate totals
        balance_sheet['assets']['total'] = (
            sum(balance_sheet['assets']['current'].values()) +
            sum(balance_sheet['assets']['fixed'].values())
        )
        balance_sheet['liabilities']['total'] = (
            sum(balance_sheet['liabilities']['current'].values()) +
            sum(balance_sheet['liabilities']['long_term'].values())
        )
        balance_sheet['equity']['total'] = (
            balance_sheet['assets']['total'] - balance_sheet['liabilities']['total']
        )
        balance_sheet['equity']['retained_earnings'] = balance_sheet['equity']['total']

        return balance_sheet

    def generate_cash_flow(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate cash flow statement."""

        # Get all cash transactions
        cash_accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.subtype.in_(['checking', 'savings'])
            )
        ).all()

        cash_flow = {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'operating': {},
            'investing': {},
            'financing': {},
            'summary': {}
        }

        total_inflow = 0
        total_outflow = 0

        for account in cash_accounts:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            ).all()

            for transaction in transactions:
                amount = float(transaction.amount)
                category = transaction.category_name or 'uncategorized'

                # Classify by activity type
                if transaction.is_business:
                    section = 'operating'
                elif category in ['investment', 'capital_gains']:
                    section = 'investing'
                elif category in ['loan_payment', 'financing']:
                    section = 'financing'
                else:
                    section = 'operating'

                if category not in cash_flow[section]:
                    cash_flow[section][category] = 0

                cash_flow[section][category] += amount

                if amount > 0:
                    total_inflow += amount
                else:
                    total_outflow += amount

        # Calculate totals
        cash_flow['operating']['total'] = sum(cash_flow['operating'].values())
        cash_flow['investing']['total'] = sum(cash_flow['investing'].values())
        cash_flow['financing']['total'] = sum(cash_flow['financing'].values())

        # Summary
        cash_flow['summary']['beginning_cash'] = self._get_beginning_balance(
            user_id, start_date, cash_accounts
        )
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

    def generate_tax_summary(
        self,
        user_id: str,
        year: int
    ) -> Dict[str, Any]:
        """Generate tax summary for the year."""

        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

        # Get P&L for tax calculations
        pl = self.generate_profit_loss(user_id, start_date, end_date, is_business=True)

        tax_summary = {
            'year': year,
            'business_income': pl['revenue']['total'],
            'business_expenses': pl['expenses']['total'],
            'net_business_income': pl['summary']['net_income'],
            'deductions': {},
            'estimated_tax': {}
        }

        # IRS Schedule C expense categories
        schedule_c_categories = {
            'advertising': 'Advertising',
            'car_and_truck': 'Car and truck expenses',
            'commissions': 'Commissions and fees',
            'contract_labor': 'Contract labor',
            'depreciation': 'Depreciation',
            'insurance': 'Insurance',
            'interest': 'Interest',
            'legal_professional': 'Legal and professional services',
            'office_expense': 'Office expense',
            'rent_lease': 'Rent or lease',
            'repairs': 'Repairs and maintenance',
            'supplies': 'Supplies',
            'taxes_licenses': 'Taxes and licenses',
            'travel': 'Travel',
            'meals': 'Meals and entertainment (50%)',
            'utilities': 'Utilities',
            'wages': 'Wages',
            'other': 'Other expenses'
        }

        # Map expenses to Schedule C categories
        for category, description in schedule_c_categories.items():
            tax_summary['deductions'][description] = pl['expenses'].get(category, 0)

        # Calculate estimated taxes (simplified)
        net_income = tax_summary['net_business_income']

        # Self-employment tax (15.3% of 92.35% of net income)
        se_income = net_income * 0.9235
        se_tax = se_income * 0.153

        # Income tax (simplified progressive calculation)
        taxable_income = net_income - (se_tax / 2)  # Deduct half of SE tax

        # 2024 tax brackets (simplified)
        if taxable_income <= 11600:
            income_tax = taxable_income * 0.10
        elif taxable_income <= 47150:
            income_tax = 1160 + (taxable_income - 11600) * 0.12
        elif taxable_income <= 100525:
            income_tax = 5426 + (taxable_income - 47150) * 0.22
        else:
            income_tax = 17168.50 + (taxable_income - 100525) * 0.24

        tax_summary['estimated_tax'] = {
            'self_employment_tax': round(se_tax, 2),
            'income_tax': round(income_tax, 2),
            'total_tax': round(se_tax + income_tax, 2),
            'quarterly_payment': round((se_tax + income_tax) / 4, 2)
        }

        return tax_summary

    def generate_owner_package(
        self,
        user_id: str,
        year: int,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive owner package."""

        # Determine period
        if month:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year, 12, 31)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        else:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)

        # Generate all reports
        package = {
            'generated_date': datetime.now().isoformat(),
            'period': {
                'year': year,
                'month': month,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'reports': {
                'profit_loss': self.generate_profit_loss(user_id, start_date, end_date),
                'balance_sheet': self.generate_balance_sheet(user_id, end_date),
                'cash_flow': self.generate_cash_flow(user_id, start_date, end_date)
            },
            'kpis': self._calculate_kpis(user_id, start_date, end_date),
            'insights': self._generate_insights(user_id, start_date, end_date)
        }

        # Add YTD if monthly
        if month:
            ytd_start = datetime(year, 1, 1)
            package['reports']['profit_loss_ytd'] = self.generate_profit_loss(
                user_id, ytd_start, end_date
            )

        # Add tax summary if full year
        if not month:
            package['reports']['tax_summary'] = self.generate_tax_summary(user_id, year)

        return package

    def _get_beginning_balance(
        self,
        user_id: str,
        date: datetime,
        accounts: List[Account]
    ) -> float:
        """Get total balance of accounts at a specific date."""
        total = 0
        for account in accounts:
            # Get balance at date by summing transactions before date
            transactions_sum = self.db.query(
                func.sum(Transaction.amount)
            ).filter(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.date < date
                )
            ).scalar() or 0
            total += float(transactions_sum)
        return total

    def _calculate_kpis(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate key performance indicators."""

        pl = self.generate_profit_loss(user_id, start_date, end_date)

        days_in_period = (end_date - start_date).days + 1
        months_in_period = days_in_period / 30.44  # Average days per month

        kpis = {
            'revenue_per_month': pl['revenue']['total'] / months_in_period if months_in_period > 0 else 0,
            'expense_per_month': pl['expenses']['total'] / months_in_period if months_in_period > 0 else 0,
            'profit_margin': (pl['summary']['net_income'] / pl['revenue']['total'] * 100) if pl['revenue']['total'] > 0 else 0,
            'expense_ratio': (pl['expenses']['total'] / pl['revenue']['total'] * 100) if pl['revenue']['total'] > 0 else 0,
            'burn_rate': pl['expenses']['total'] / months_in_period if months_in_period > 0 else 0
        }

        # Calculate effective hourly rate if consulting revenue exists
        if 'consulting' in pl['revenue'] and pl['revenue']['consulting'] > 0:
            # Assume 160 hours/month for now (can be made configurable)
            hours_worked = 160 * months_in_period
            kpis['effective_hourly_rate'] = pl['revenue']['consulting'] / hours_worked

        # Calculate cash runway
        cash_balance = self._get_current_cash_balance(user_id)
        if kpis['burn_rate'] > 0:
            kpis['cash_runway_months'] = cash_balance / kpis['burn_rate']

        return kpis

    def _get_current_cash_balance(self, user_id: str) -> float:
        """Get current total cash balance."""
        cash_accounts = self.db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.subtype.in_(['checking', 'savings'])
            )
        ).all()

        return sum(float(account.current_balance or 0) for account in cash_accounts)

    def _generate_insights(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[str]:
        """Generate actionable insights from financial data."""

        insights = []
        pl = self.generate_profit_loss(user_id, start_date, end_date)
        kpis = self._calculate_kpis(user_id, start_date, end_date)

        # Revenue insights
        if pl['revenue']['total'] == 0:
            insights.append("⚠️ No revenue recorded this period - focus on business development")
        elif kpis['profit_margin'] < 20:
            insights.append(f"⚠️ Low profit margin ({kpis['profit_margin']:.1f}%) - review pricing or reduce expenses")
        elif kpis['profit_margin'] > 40:
            insights.append(f"✅ Strong profit margin ({kpis['profit_margin']:.1f}%) - consider scaling operations")

        # Expense insights
        if kpis['expense_ratio'] > 80:
            insights.append(f"⚠️ High expense ratio ({kpis['expense_ratio']:.1f}%) - review cost structure")

        # Cash runway insights
        if 'cash_runway_months' in kpis:
            if kpis['cash_runway_months'] < 3:
                insights.append(f"🚨 Low cash runway ({kpis['cash_runway_months']:.1f} months) - urgent attention needed")
            elif kpis['cash_runway_months'] < 6:
                insights.append(f"⚠️ Limited cash runway ({kpis['cash_runway_months']:.1f} months) - monitor closely")
            else:
                insights.append(f"✅ Healthy cash runway ({kpis['cash_runway_months']:.1f} months)")

        # Largest expense categories
        if pl['expenses']:
            sorted_expenses = sorted(
                [(k, v) for k, v in pl['expenses'].items() if k != 'total'],
                key=lambda x: x[1],
                reverse=True
            )[:3]

            if sorted_expenses:
                top_expenses = ", ".join([f"{k}: ${v:,.0f}" for k, v in sorted_expenses])
                insights.append(f"📊 Top expenses: {top_expenses}")

        return insights