"""Tax categorization service for business expense classification."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.transaction import Transaction
from models.tax_categorization import (
    TaxCategory, ChartOfAccount, BusinessExpenseTracking,
    CategoryMapping, CategorizationAudit
)
from models.category import Category

logger = logging.getLogger(__name__)


class TaxCategorizationService:
    """Service for tax categorization of business transactions."""

    def __init__(self, session: Session):
        self.session = session

    def categorize_for_tax(
        self,
        transaction_id: str,
        user_id: str,
        tax_category_id: Optional[str] = None,
        chart_account_id: Optional[str] = None,
        business_percentage: Decimal = Decimal("100.00"),
        business_purpose: Optional[str] = None,
        override_automated: bool = False
    ) -> Dict[str, Any]:
        """Categorize a transaction for tax purposes."""

        transaction = self.session.query(Transaction).filter_by(id=transaction_id).first()
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Store original values for audit
        old_tax_category_id = transaction.tax_category_id
        old_chart_account_id = transaction.chart_account_id

        try:
            # Auto-detect if not provided
            if not tax_category_id or not chart_account_id:
                detected = self.auto_detect_tax_category(transaction, user_id)
                if not tax_category_id:
                    tax_category_id = detected.get("tax_category_id")
                if not chart_account_id:
                    chart_account_id = detected.get("chart_account_id")

            # Validate tax category and chart account
            tax_category = None
            chart_account = None

            if tax_category_id:
                tax_category = self.session.query(TaxCategory).filter_by(id=tax_category_id).first()
                if not tax_category or not tax_category.is_currently_effective():
                    raise ValueError(f"Invalid or inactive tax category: {tax_category_id}")

            if chart_account_id:
                chart_account = self.session.query(ChartOfAccount).filter_by(
                    id=chart_account_id, user_id=user_id, is_active=True
                ).first()
                if not chart_account:
                    raise ValueError(f"Invalid chart account: {chart_account_id}")

            # Update transaction
            transaction.tax_category_id = tax_category_id
            transaction.chart_account_id = chart_account_id
            transaction.business_use_percentage = business_percentage

            # Calculate deductible amount
            if tax_category and business_percentage > 0:
                business_amount = transaction.amount_decimal * (business_percentage / Decimal("100"))
                deductible_amount = tax_category.calculate_deductible_amount(business_amount)
                transaction.deductible_amount = deductible_amount

                # Set Schedule C line
                if tax_category.tax_form == "Schedule C":
                    transaction.schedule_c_line = tax_category.tax_line

            # Check if substantiation is required
            transaction.requires_substantiation = self._requires_substantiation(transaction, tax_category)

            # Create or update business expense tracking
            if business_percentage > 0:
                self._create_or_update_business_tracking(
                    transaction, user_id, business_percentage, business_purpose
                )

            # Create audit record
            self._create_audit_record(
                transaction=transaction,
                user_id=user_id,
                action_type="tax_categorize",
                old_tax_category_id=old_tax_category_id,
                new_tax_category_id=tax_category_id,
                old_chart_account_id=old_chart_account_id,
                new_chart_account_id=chart_account_id,
                automated=not override_automated
            )

            self.session.commit()

            return {
                "success": True,
                "transaction_id": transaction_id,
                "tax_category": tax_category.category_name if tax_category else None,
                "chart_account": chart_account.account_name if chart_account else None,
                "deductible_amount": float(transaction.deductible_amount) if transaction.deductible_amount else 0,
                "requires_substantiation": transaction.requires_substantiation
            }

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error categorizing transaction {transaction_id}: {e}")
            raise

    def auto_detect_tax_category(self, transaction: Transaction, user_id: str) -> Dict[str, Optional[str]]:
        """Auto-detect tax category and chart account for a transaction."""

        # Start with existing category mapping if available
        if transaction.category_id:
            mapping = self.session.query(CategoryMapping).filter(
                and_(
                    CategoryMapping.user_id == user_id,
                    CategoryMapping.source_category_id == transaction.category_id,
                    CategoryMapping.is_active == True,
                    CategoryMapping.effective_date <= date.today(),
                    or_(
                        CategoryMapping.expiration_date.is_(None),
                        CategoryMapping.expiration_date >= date.today()
                    )
                )
            ).order_by(desc(CategoryMapping.confidence_score)).first()

            if mapping:
                return {
                    "tax_category_id": str(mapping.tax_category_id),
                    "chart_account_id": str(mapping.chart_account_id),
                    "confidence": float(mapping.confidence_score),
                    "source": "category_mapping"
                }

        # Keyword-based detection
        search_text = f"{transaction.name} {transaction.merchant_name or ''} {transaction.description or ''}".lower()

        # Query tax categories with keywords
        tax_categories = self.session.query(TaxCategory).filter(
            and_(
                TaxCategory.is_active == True,
                TaxCategory.effective_date <= date.today(),
                or_(
                    TaxCategory.expiration_date.is_(None),
                    TaxCategory.expiration_date >= date.today()
                )
            )
        ).all()

        best_match = None
        best_score = 0

        for tax_category in tax_categories:
            score = self._calculate_keyword_match_score(search_text, tax_category)
            if score > best_score:
                best_score = score
                best_match = tax_category

        if best_match and best_score > 0.3:  # Minimum confidence threshold
            # Find corresponding chart account
            chart_account = self.session.query(ChartOfAccount).filter(
                and_(
                    ChartOfAccount.user_id == user_id,
                    ChartOfAccount.tax_category == best_match.category_name,
                    ChartOfAccount.is_active == True
                )
            ).first()

            return {
                "tax_category_id": str(best_match.id),
                "chart_account_id": str(chart_account.id) if chart_account else None,
                "confidence": best_score,
                "source": "keyword_matching"
            }

        return {
            "tax_category_id": None,
            "chart_account_id": None,
            "confidence": 0.0,
            "source": "no_match"
        }

    def get_tax_summary(self, user_id: str, tax_year: int) -> Dict[str, Any]:
        """Get tax summary for a specific year."""

        # Get all deductible transactions for the year
        transactions = self.session.query(Transaction).filter(
            and_(
                Transaction.tax_year == tax_year,
                Transaction.is_tax_deductible == True,
                Transaction.deductible_amount.isnot(None)
            )
        ).join(Transaction.account).filter(
            Transaction.account.has(user_id=user_id)
        ).all()

        # Group by tax category
        summary_by_category = {}
        total_deductions = Decimal("0")

        for transaction in transactions:
            if transaction.tax_category:
                category_code = transaction.tax_category.category_code
                category_name = transaction.tax_category.category_name

                if category_code not in summary_by_category:
                    summary_by_category[category_code] = {
                        "category_name": category_name,
                        "tax_form": transaction.tax_category.tax_form,
                        "tax_line": transaction.tax_category.tax_line,
                        "total_amount": Decimal("0"),
                        "transaction_count": 0,
                        "requires_substantiation": 0
                    }

                summary_by_category[category_code]["total_amount"] += transaction.deductible_amount
                summary_by_category[category_code]["transaction_count"] += 1
                total_deductions += transaction.deductible_amount

                if transaction.requires_substantiation and not transaction.substantiation_complete:
                    summary_by_category[category_code]["requires_substantiation"] += 1

        # Convert Decimal to float for JSON serialization
        for category in summary_by_category.values():
            category["total_amount"] = float(category["total_amount"])

        return {
            "tax_year": tax_year,
            "total_deductions": float(total_deductions),
            "categories": summary_by_category,
            "transaction_count": len(transactions)
        }

    def bulk_categorize_for_tax(
        self,
        transaction_ids: List[str],
        user_id: str,
        tax_category_id: Optional[str] = None,
        chart_account_id: Optional[str] = None,
        business_percentage: Decimal = Decimal("100.00")
    ) -> Dict[str, Any]:
        """Bulk categorize multiple transactions."""

        results = []
        errors = []

        for transaction_id in transaction_ids:
            try:
                result = self.categorize_for_tax(
                    transaction_id=transaction_id,
                    user_id=user_id,
                    tax_category_id=tax_category_id,
                    chart_account_id=chart_account_id,
                    business_percentage=business_percentage,
                    override_automated=True
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    "transaction_id": transaction_id,
                    "error": str(e)
                })

        return {
            "success_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors
        }

    def get_schedule_c_export(self, user_id: str, tax_year: int) -> Dict[str, Any]:
        """Export Schedule C data for tax filing."""

        summary = self.get_tax_summary(user_id, tax_year)

        # Map to Schedule C line items
        schedule_c_lines = {}

        for category_code, data in summary["categories"].items():
            if data["tax_form"] == "Schedule C":
                line_number = data["tax_line"].replace("Line ", "").replace("a", "").replace("b", "")

                if line_number in schedule_c_lines:
                    schedule_c_lines[line_number]["amount"] += data["total_amount"]
                else:
                    schedule_c_lines[line_number] = {
                        "line_description": data["category_name"],
                        "amount": data["total_amount"],
                        "transaction_count": data["transaction_count"]
                    }

        return {
            "tax_year": tax_year,
            "schedule_c_lines": schedule_c_lines,
            "total_expenses": sum(line["amount"] for line in schedule_c_lines.values())
        }

    def _calculate_keyword_match_score(self, search_text: str, tax_category: TaxCategory) -> float:
        """Calculate keyword match score for a tax category."""

        if not tax_category.keywords:
            return 0.0

        keywords = tax_category.keywords
        exclusions = tax_category.exclusions or []

        # Check for exclusions first
        for exclusion in exclusions:
            if exclusion.lower() in search_text:
                return 0.0

        # Calculate keyword matches
        matches = 0
        total_keywords = len(keywords)

        for keyword in keywords:
            if keyword.lower() in search_text:
                matches += 1

        return matches / total_keywords if total_keywords > 0 else 0.0

    def _requires_substantiation(self, transaction: Transaction, tax_category: Optional[TaxCategory]) -> bool:
        """Determine if transaction requires substantiation."""

        if not tax_category:
            return False

        # IRS substantiation requirements
        if transaction.amount_decimal >= Decimal("75.00"):
            return True

        if tax_category.documentation_required:
            return True

        # Specific categories that always require substantiation
        substantiation_categories = ["Travel", "Meals", "Entertainment", "Car and truck expenses"]
        if tax_category.category_name in substantiation_categories:
            return True

        return False

    def _create_or_update_business_tracking(
        self,
        transaction: Transaction,
        user_id: str,
        business_percentage: Decimal,
        business_purpose: Optional[str]
    ) -> None:
        """Create or update business expense tracking record."""

        tracking = self.session.query(BusinessExpenseTracking).filter_by(
            transaction_id=transaction.id
        ).first()

        if tracking:
            tracking.business_percentage = business_percentage
            if business_purpose:
                tracking.business_purpose = business_purpose
        else:
            tracking = BusinessExpenseTracking(
                transaction_id=transaction.id,
                user_id=user_id,
                business_percentage=business_percentage,
                business_purpose=business_purpose,
                receipt_required=self._requires_substantiation(transaction, transaction.tax_category)
            )
            self.session.add(tracking)

    def _create_audit_record(
        self,
        transaction: Transaction,
        user_id: str,
        action_type: str,
        **kwargs
    ) -> None:
        """Create audit record for categorization change."""

        audit = CategorizationAudit(
            transaction_id=transaction.id,
            user_id=user_id,
            action_type=action_type,
            **kwargs
        )
        self.session.add(audit)