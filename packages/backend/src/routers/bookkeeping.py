"""
Bookkeeping API endpoints for journal entries, reconciliation, and financial closing.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..database import get_db
from ..database.bookkeeping_models import (
    JournalEntry,
    JournalEntryLine,
    AccountingPeriod,
    BookkeepingRule,
    ReconciliationRecord,
    ReconciliationItem,
    TransactionPattern
)
from ..database.models import User, Transaction, Account
from ..dependencies.auth import get_current_active_user
from ..schemas.bookkeeping import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    AccountingPeriodResponse,
    ReconciliationStart,
    ReconciliationResponse,
    BookkeepingHealthResponse,
    PendingTasksResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def get_bookkeeping_health(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> BookkeepingHealthResponse:
    """Get bookkeeping health status and indicators."""
    try:
        # Get current accounting period
        current_period = db.query(AccountingPeriod).filter(
            AccountingPeriod.user_id == current_user.id,
            AccountingPeriod.start_date <= date.today(),
            AccountingPeriod.end_date >= date.today()
        ).first()

        # Count unposted journal entries
        unposted_entries = db.query(func.count(JournalEntry.id)).filter(
            JournalEntry.user_id == current_user.id,
            JournalEntry.is_posted == False
        ).scalar() or 0

        # Count unreconciled accounts
        unreconciled_accounts = db.query(func.count(func.distinct(Account.id))).filter(
            Account.user_id == current_user.id,
            Account.is_active == True,
            ~Account.id.in_(
                db.query(ReconciliationRecord.account_id).filter(
                    ReconciliationRecord.status == "reconciled",
                    ReconciliationRecord.reconciliation_date >= date.today() - timedelta(days=30)
                )
            )
        ).scalar() or 0

        # Calculate accuracy score (simplified)
        total_transactions = db.query(func.count(Transaction.id)).join(Account).filter(
            Account.user_id == current_user.id
        ).scalar() or 1

        categorized_transactions = db.query(func.count(Transaction.id)).join(Account).filter(
            Account.user_id == current_user.id,
            or_(
                Transaction.user_category_override.isnot(None),
                Transaction.subcategory.isnot(None)
            )
        ).scalar() or 0

        accuracy_score = (categorized_transactions / total_transactions) * 100 if total_transactions > 0 else 0

        # Determine overall status
        if unposted_entries > 10 or unreconciled_accounts > 3:
            status = "behind"
        elif unposted_entries > 5 or unreconciled_accounts > 1:
            status = "warning"
        else:
            status = "current"

        return BookkeepingHealthResponse(
            status=status,
            current_period=current_period.period_name if current_period else None,
            unposted_entries=unposted_entries,
            unreconciled_accounts=unreconciled_accounts,
            accuracy_score=round(accuracy_score, 1),
            last_reconciliation_date=None  # TODO: Get from reconciliation records
        )

    except Exception as e:
        logger.error(f"Failed to get bookkeeping health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bookkeeping health")


@router.get("/pending-tasks")
async def get_pending_tasks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PendingTasksResponse:
    """Get list of pending bookkeeping tasks."""
    try:
        tasks = []

        # Check for uncategorized transactions
        uncategorized = db.query(func.count(Transaction.id)).join(Account).filter(
            Account.user_id == current_user.id,
            Transaction.user_category_override.is_(None),
            Transaction.subcategory.is_(None)
        ).scalar() or 0

        if uncategorized > 0:
            tasks.append({
                "type": "categorization",
                "title": "Review Categorization",
                "description": f"{uncategorized} transactions need categorization",
                "priority": "high" if uncategorized > 20 else "medium",
                "count": uncategorized
            })

        # Check for accounts needing reconciliation
        accounts_to_reconcile = db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.is_active == True,
            Account.account_type.in_(["depository", "credit"])
        ).all()

        for account in accounts_to_reconcile:
            last_recon = db.query(ReconciliationRecord).filter(
                ReconciliationRecord.account_id == account.id,
                ReconciliationRecord.status == "reconciled"
            ).order_by(ReconciliationRecord.reconciliation_date.desc()).first()

            if not last_recon or (date.today() - last_recon.reconciliation_date).days > 30:
                tasks.append({
                    "type": "reconciliation",
                    "title": f"Reconcile {account.name}",
                    "description": "Account needs monthly reconciliation",
                    "priority": "high" if not last_recon else "medium",
                    "account_id": str(account.id)
                })

        # Check for period closing
        current_month_start = date.today().replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        period_exists = db.query(AccountingPeriod).filter(
            AccountingPeriod.user_id == current_user.id,
            AccountingPeriod.start_date == last_month_start,
            AccountingPeriod.is_closed == True
        ).first()

        if not period_exists and date.today().day > 5:  # After 5th of month
            tasks.append({
                "type": "period_closing",
                "title": f"Close {last_month_end.strftime('%B %Y')}",
                "description": "Previous month ready for closing",
                "priority": "high",
                "period_date": last_month_end.isoformat()
            })

        return PendingTasksResponse(
            total_count=len(tasks),
            tasks=tasks
        )

    except Exception as e:
        logger.error(f"Failed to get pending tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending tasks")


@router.post("/journal-entries")
async def create_journal_entry(
    entry_data: JournalEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> JournalEntryResponse:
    """Create a new journal entry."""
    try:
        # Validate that debits equal credits
        total_debits = sum(line.debit_amount or 0 for line in entry_data.lines)
        total_credits = sum(line.credit_amount or 0 for line in entry_data.lines)

        if abs(total_debits - total_credits) > 0.01:  # Allow for small rounding differences
            raise HTTPException(
                status_code=400,
                detail=f"Journal entry must balance. Debits: {total_debits}, Credits: {total_credits}"
            )

        # Generate entry number
        last_entry = db.query(JournalEntry).filter(
            JournalEntry.user_id == current_user.id
        ).order_by(JournalEntry.entry_number.desc()).first()

        if last_entry and last_entry.entry_number:
            # Extract number and increment
            last_num = int(last_entry.entry_number.split('-')[-1])
            entry_number = f"JE-{date.today().strftime('%Y%m')}-{last_num + 1:04d}"
        else:
            entry_number = f"JE-{date.today().strftime('%Y%m')}-0001"

        # Create journal entry
        journal_entry = JournalEntry(
            user_id=current_user.id,
            entry_number=entry_number,
            entry_date=entry_data.entry_date or date.today(),
            description=entry_data.description,
            reference=entry_data.reference,
            journal_type=entry_data.journal_type or "general",
            total_debits=total_debits,
            total_credits=total_credits,
            is_balanced=True,
            source_type=entry_data.source_type or "manual"
        )

        db.add(journal_entry)
        db.flush()  # Get the ID

        # Create journal entry lines
        for idx, line_data in enumerate(entry_data.lines, 1):
            line = JournalEntryLine(
                journal_entry_id=journal_entry.id,
                chart_account_id=line_data.chart_account_id,
                debit_amount=line_data.debit_amount or Decimal("0.00"),
                credit_amount=line_data.credit_amount or Decimal("0.00"),
                description=line_data.description,
                transaction_id=line_data.transaction_id,
                line_number=idx,
                tax_category_id=line_data.tax_category_id
            )
            db.add(line)

        db.commit()
        db.refresh(journal_entry)

        return JournalEntryResponse(
            id=journal_entry.id,
            entry_number=journal_entry.entry_number,
            entry_date=journal_entry.entry_date,
            description=journal_entry.description,
            total_debits=journal_entry.total_debits,
            total_credits=journal_entry.total_credits,
            is_posted=journal_entry.is_posted,
            lines_count=len(entry_data.lines)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create journal entry: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create journal entry")


@router.get("/journal-entries")
async def list_journal_entries(
    period_id: Optional[UUID] = Query(None),
    is_posted: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[JournalEntryResponse]:
    """List journal entries with optional filters."""
    try:
        query = db.query(JournalEntry).filter(
            JournalEntry.user_id == current_user.id
        )

        if period_id:
            query = query.filter(JournalEntry.period_id == period_id)

        if is_posted is not None:
            query = query.filter(JournalEntry.is_posted == is_posted)

        entries = query.order_by(JournalEntry.entry_date.desc()).limit(limit).offset(offset).all()

        return [
            JournalEntryResponse(
                id=entry.id,
                entry_number=entry.entry_number,
                entry_date=entry.entry_date,
                description=entry.description,
                total_debits=entry.total_debits,
                total_credits=entry.total_credits,
                is_posted=entry.is_posted,
                lines_count=len(entry.lines)
            )
            for entry in entries
        ]

    except Exception as e:
        logger.error(f"Failed to list journal entries: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve journal entries")


@router.post("/journal-entries/{entry_id}/post")
async def post_journal_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> JournalEntryResponse:
    """Post a journal entry to the general ledger."""
    try:
        entry = db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id
        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        if entry.is_posted:
            raise HTTPException(status_code=400, detail="Journal entry already posted")

        # Validate balance
        if not entry.validate_balance():
            raise HTTPException(status_code=400, detail="Journal entry does not balance")

        # Mark as posted
        entry.is_posted = True
        entry.posting_date = datetime.utcnow()

        # TODO: Update chart of accounts balances

        db.commit()
        db.refresh(entry)

        return JournalEntryResponse(
            id=entry.id,
            entry_number=entry.entry_number,
            entry_date=entry.entry_date,
            description=entry.description,
            total_debits=entry.total_debits,
            total_credits=entry.total_credits,
            is_posted=entry.is_posted,
            lines_count=len(entry.lines)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to post journal entry: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to post journal entry")


@router.post("/reconciliation/start")
async def start_reconciliation(
    reconciliation_data: ReconciliationStart,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ReconciliationResponse:
    """Start a new bank reconciliation process."""
    try:
        # Verify account ownership
        account = db.query(Account).filter(
            Account.id == reconciliation_data.account_id,
            Account.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Check for existing pending reconciliation
        pending = db.query(ReconciliationRecord).filter(
            ReconciliationRecord.account_id == reconciliation_data.account_id,
            ReconciliationRecord.status == "pending"
        ).first()

        if pending:
            raise HTTPException(status_code=400, detail="A reconciliation is already in progress for this account")

        # Calculate book balance
        book_balance = account.current_balance or Decimal("0.00")

        # Create reconciliation record
        reconciliation = ReconciliationRecord(
            account_id=reconciliation_data.account_id,
            reconciliation_date=reconciliation_data.reconciliation_date or date.today(),
            statement_balance=reconciliation_data.statement_balance,
            book_balance=book_balance,
            status="pending",
            reconciled_by=current_user.id,
            discrepancy_amount=abs(reconciliation_data.statement_balance - book_balance)
        )

        db.add(reconciliation)
        db.commit()
        db.refresh(reconciliation)

        return ReconciliationResponse(
            id=reconciliation.id,
            account_id=reconciliation.account_id,
            account_name=account.name,
            reconciliation_date=reconciliation.reconciliation_date,
            statement_balance=reconciliation.statement_balance,
            book_balance=reconciliation.book_balance,
            discrepancy_amount=reconciliation.discrepancy_amount,
            status=reconciliation.status,
            matched_count=0,
            unmatched_count=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start reconciliation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start reconciliation")


@router.get("/accounting-periods")
async def list_accounting_periods(
    year: Optional[int] = Query(None),
    is_closed: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[AccountingPeriodResponse]:
    """List accounting periods."""
    try:
        query = db.query(AccountingPeriod).filter(
            AccountingPeriod.user_id == current_user.id
        )

        if year:
            query = query.filter(
                func.extract('year', AccountingPeriod.start_date) == year
            )

        if is_closed is not None:
            query = query.filter(AccountingPeriod.is_closed == is_closed)

        periods = query.order_by(AccountingPeriod.start_date.desc()).all()

        return [
            AccountingPeriodResponse(
                id=period.id,
                period_name=period.period_name,
                period_type=period.period_type,
                start_date=period.start_date,
                end_date=period.end_date,
                is_closed=period.is_closed,
                closing_date=period.closing_date
            )
            for period in periods
        ]

    except Exception as e:
        logger.error(f"Failed to list accounting periods: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve accounting periods")


@router.post("/periods/close")
async def close_accounting_period(
    period_id: UUID = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AccountingPeriodResponse:
    """Close an accounting period."""
    try:
        period = db.query(AccountingPeriod).filter(
            AccountingPeriod.id == period_id,
            AccountingPeriod.user_id == current_user.id
        ).first()

        if not period:
            raise HTTPException(status_code=404, detail="Accounting period not found")

        if period.is_closed:
            raise HTTPException(status_code=400, detail="Period is already closed")

        # TODO: Validate all requirements for closing
        # - All transactions categorized
        # - All accounts reconciled
        # - All journal entries posted

        # Close the period
        period.is_closed = True
        period.closing_date = datetime.utcnow()

        # TODO: Create closing journal entries

        db.commit()
        db.refresh(period)

        return AccountingPeriodResponse(
            id=period.id,
            period_name=period.period_name,
            period_type=period.period_type,
            start_date=period.start_date,
            end_date=period.end_date,
            is_closed=period.is_closed,
            closing_date=period.closing_date
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close accounting period: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to close accounting period")