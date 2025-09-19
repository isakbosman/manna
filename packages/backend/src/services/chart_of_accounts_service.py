"""Chart of Accounts service for double-entry bookkeeping."""

import logging
from decimal import Decimal
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from models.tax_categorization import ChartOfAccount
from models.transaction import Transaction

logger = logging.getLogger(__name__)


class ChartOfAccountsService:
    """Service for managing chart of accounts."""

    def __init__(self, session: Session):
        self.session = session

    def create_account(
        self,
        user_id: str,
        account_code: str,
        account_name: str,
        account_type: str,
        normal_balance: str,
        parent_account_id: Optional[str] = None,
        description: Optional[str] = None,
        tax_category: Optional[str] = None,
        tax_line_mapping: Optional[str] = None
    ) -> ChartOfAccount:
        """Create a new chart of accounts entry."""

        try:
            # Validate account code uniqueness for user
            existing = self.session.query(ChartOfAccount).filter_by(
                user_id=user_id,
                account_code=account_code
            ).first()

            if existing:
                raise ValueError(f"Account code {account_code} already exists for this user")

            # Validate parent account if provided
            parent_account = None
            if parent_account_id:
                parent_account = self.session.query(ChartOfAccount).filter_by(
                    id=parent_account_id,
                    user_id=user_id,
                    is_active=True
                ).first()
                if not parent_account:
                    raise ValueError(f"Parent account {parent_account_id} not found")

            # Create new account
            account = ChartOfAccount(
                user_id=user_id,
                account_code=account_code,
                account_name=account_name,
                account_type=account_type,
                normal_balance=normal_balance,
                parent_account_id=parent_account_id,
                description=description,
                tax_category=tax_category,
                tax_line_mapping=tax_line_mapping,
                current_balance=Decimal("0.00")
            )

            self.session.add(account)
            self.session.commit()

            logger.info(f"Created account {account_code} - {account_name} for user {user_id}")
            return account
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create account {account_code}: {str(e)}")
            raise

    def update_account(
        self,
        account_id: str,
        user_id: str,
        **update_fields
    ) -> ChartOfAccount:
        """Update an existing chart of accounts entry."""

        try:
            account = self.session.query(ChartOfAccount).filter_by(
                id=account_id,
                user_id=user_id
            ).first()

            if not account:
                raise ValueError(f"Account {account_id} not found")

            # Don't allow updating system accounts' core fields
            if account.is_system_account:
                restricted_fields = {"account_code", "account_type", "normal_balance"}
                if any(field in update_fields for field in restricted_fields):
                    raise ValueError("Cannot modify core fields of system accounts")

            # Update allowed fields
            allowed_fields = {
                "account_name", "description", "tax_category", "tax_line_mapping",
                "requires_1099", "is_active", "metadata"
            }

            for field, value in update_fields.items():
                if field in allowed_fields and hasattr(account, field):
                    setattr(account, field, value)

            self.session.commit()

            logger.info(f"Updated account {account.account_code} for user {user_id}")
            return account
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update account {account_id}: {str(e)}")
            raise

    def get_account_balance(self, account_id: str, user_id: str, as_of_date: Optional[str] = None) -> Decimal:
        """Calculate the current balance of an account."""

        account = self.session.query(ChartOfAccount).filter_by(
            id=account_id,
            user_id=user_id
        ).first()

        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Build query for transactions
        query = self.session.query(func.sum(Transaction.amount)).filter(
            Transaction.chart_account_id == account_id
        )

        if as_of_date:
            query = query.filter(Transaction.date <= as_of_date)

        # Calculate balance based on normal balance and transaction types
        debits = query.filter(Transaction.transaction_type == "debit").scalar() or Decimal("0")
        credits = query.filter(Transaction.transaction_type == "credit").scalar() or Decimal("0")

        if account.normal_balance == "debit":
            balance = debits - credits
        else:
            balance = credits - debits

        # Update the stored balance
        try:
            account.current_balance = balance
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update account balance for {account_id}: {str(e)}")
            raise

        return balance

    def get_trial_balance(self, user_id: str, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate a trial balance report."""

        accounts = self.session.query(ChartOfAccount).filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(ChartOfAccount.account_code).all()

        trial_balance = {
            "accounts": [],
            "total_debits": Decimal("0"),
            "total_credits": Decimal("0"),
            "as_of_date": as_of_date,
            "is_balanced": True
        }

        for account in accounts:
            balance = self.get_account_balance(account.id, user_id, as_of_date)

            account_data = {
                "account_code": account.account_code,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "normal_balance": account.normal_balance,
                "balance": float(balance),
                "debit_balance": float(balance) if account.normal_balance == "debit" and balance > 0 else 0,
                "credit_balance": float(balance) if account.normal_balance == "credit" and balance > 0 else 0
            }

            trial_balance["accounts"].append(account_data)

            # Add to totals
            if account.normal_balance == "debit" and balance > 0:
                trial_balance["total_debits"] += balance
            elif account.normal_balance == "credit" and balance > 0:
                trial_balance["total_credits"] += balance

        # Check if trial balance balances
        trial_balance["is_balanced"] = trial_balance["total_debits"] == trial_balance["total_credits"]

        # Convert Decimals to floats for JSON serialization
        trial_balance["total_debits"] = float(trial_balance["total_debits"])
        trial_balance["total_credits"] = float(trial_balance["total_credits"])

        return trial_balance

    def get_accounts_by_type(self, user_id: str, account_type: str) -> List[ChartOfAccount]:
        """Get all accounts of a specific type."""

        return self.session.query(ChartOfAccount).filter_by(
            user_id=user_id,
            account_type=account_type,
            is_active=True
        ).order_by(ChartOfAccount.account_code).all()

    def get_account_hierarchy(self, user_id: str) -> List[Dict[str, Any]]:
        """Get chart of accounts as a hierarchical structure."""

        # Get all accounts
        accounts = self.session.query(ChartOfAccount).filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(ChartOfAccount.account_code).all()

        # Build hierarchy
        account_dict = {acc.id: self._account_to_dict(acc) for acc in accounts}
        hierarchy = []

        for account in accounts:
            if account.parent_account_id is None:
                # Root account
                account_data = account_dict[account.id]
                account_data["children"] = self._get_children(account.id, account_dict, accounts)
                hierarchy.append(account_data)

        return hierarchy

    def delete_account(self, account_id: str, user_id: str) -> bool:
        """Soft delete an account (mark as inactive)."""

        try:
            account = self.session.query(ChartOfAccount).filter_by(
                id=account_id,
                user_id=user_id
            ).first()

            if not account:
                raise ValueError(f"Account {account_id} not found")

            if account.is_system_account:
                raise ValueError("Cannot delete system accounts")

            # Check if account has transactions
            transaction_count = self.session.query(Transaction).filter_by(
                chart_account_id=account_id
            ).count()

            if transaction_count > 0:
                # Soft delete - mark as inactive
                account.is_active = False
                self.session.commit()
                logger.info(f"Soft deleted account {account.account_code} (has {transaction_count} transactions)")
                return True
            else:
                # Hard delete if no transactions
                self.session.delete(account)
                self.session.commit()
                logger.info(f"Hard deleted account {account.account_code}")
                return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete account {account_id}: {str(e)}")
            raise

    def _account_to_dict(self, account: ChartOfAccount) -> Dict[str, Any]:
        """Convert account to dictionary representation."""

        return {
            "id": str(account.id),
            "account_code": account.account_code,
            "account_name": account.account_name,
            "account_type": account.account_type,
            "normal_balance": account.normal_balance,
            "current_balance": float(account.current_balance),
            "description": account.description,
            "tax_category": account.tax_category,
            "tax_line_mapping": account.tax_line_mapping,
            "is_system_account": account.is_system_account,
            "is_active": account.is_active,
            "children": []
        }

    def _get_children(self, parent_id: str, account_dict: Dict[str, Any], accounts: List[ChartOfAccount]) -> List[Dict[str, Any]]:
        """Recursively get children accounts."""

        children = []
        for account in accounts:
            if account.parent_account_id == parent_id:
                child_data = account_dict[account.id]
                child_data["children"] = self._get_children(account.id, account_dict, accounts)
                children.append(child_data)

        return children

    def generate_financial_statements(self, user_id: str, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate basic financial statements."""

        trial_balance = self.get_trial_balance(user_id, as_of_date)

        # Separate accounts by type
        assets = []
        liabilities = []
        equity = []
        revenue = []
        expenses = []

        for account in trial_balance["accounts"]:
            account_type = account["account_type"]
            if account_type in ["asset", "contra_asset"]:
                assets.append(account)
            elif account_type in ["liability", "contra_liability"]:
                liabilities.append(account)
            elif account_type in ["equity", "contra_equity"]:
                equity.append(account)
            elif account_type == "revenue":
                revenue.append(account)
            elif account_type == "expense":
                expenses.append(account)

        # Calculate totals
        total_assets = sum(acc["balance"] for acc in assets if acc["account_type"] == "asset") - \
                      sum(acc["balance"] for acc in assets if acc["account_type"] == "contra_asset")

        total_liabilities = sum(acc["balance"] for acc in liabilities if acc["account_type"] == "liability") - \
                           sum(acc["balance"] for acc in liabilities if acc["account_type"] == "contra_liability")

        total_equity = sum(acc["balance"] for acc in equity if acc["account_type"] == "equity") - \
                      sum(acc["balance"] for acc in equity if acc["account_type"] == "contra_equity")

        total_revenue = sum(acc["balance"] for acc in revenue)
        total_expenses = sum(acc["balance"] for acc in expenses)

        net_income = total_revenue - total_expenses

        return {
            "balance_sheet": {
                "assets": {
                    "accounts": assets,
                    "total": total_assets
                },
                "liabilities": {
                    "accounts": liabilities,
                    "total": total_liabilities
                },
                "equity": {
                    "accounts": equity,
                    "total": total_equity,
                    "total_with_income": total_equity + net_income
                },
                "total_liabilities_and_equity": total_liabilities + total_equity + net_income
            },
            "income_statement": {
                "revenue": {
                    "accounts": revenue,
                    "total": total_revenue
                },
                "expenses": {
                    "accounts": expenses,
                    "total": total_expenses
                },
                "net_income": net_income
            },
            "as_of_date": as_of_date
        }