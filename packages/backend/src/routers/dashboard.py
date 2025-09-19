"""
Dashboard API endpoints for aggregated financial data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case

from ..database import get_db
from ..database.models import User, Account, Transaction, Category
from ..dependencies.auth import get_current_active_user
from pydantic import BaseModel
from typing import Any

class ResponseModel(BaseModel):
    data: Any
    message: str = "Success"
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary")
async def get_financial_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel:
    """Get financial summary with assets, liabilities, and net worth."""
    try:
        # Get all user accounts (is_hidden is a property that checks is_active)
        accounts = db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.is_active == True
        ).all()

        # Calculate totals
        total_assets = 0
        total_liabilities = 0
        liquid_assets = 0

        breakdown = {
            "checking": 0,
            "savings": 0,
            "investments": 0,
            "creditCards": 0,
            "loans": 0,
            "other": 0
        }

        for account in accounts:
            balance = float(account.current_balance) if account.current_balance else 0

            if account.account_type in ["depository", "investment"]:
                total_assets += balance
                if account.account_type == "depository":
                    liquid_assets += balance
                    if account.account_subtype == "checking":
                        breakdown["checking"] += balance
                    elif account.account_subtype == "savings":
                        breakdown["savings"] += balance
                else:
                    breakdown["investments"] += balance
            elif account.account_type in ["credit", "loan"]:
                total_liabilities += abs(balance)
                if account.account_type == "credit":
                    breakdown["creditCards"] -= abs(balance)
                else:
                    breakdown["loans"] -= abs(balance)
            else:
                breakdown["other"] += balance

        # Calculate month-over-month changes (mock for now)
        data = {
            "totalAssets": total_assets,
            "totalLiabilities": total_liabilities,
            "netWorth": total_assets - total_liabilities,
            "liquidAssets": liquid_assets,
            "monthlyChange": {
                "assets": 0,
                "liabilities": 0,
                "netWorth": 0
            },
            "breakdown": breakdown
        }

        return ResponseModel(data=data)

    except Exception as e:
        logger.error(f"Failed to get financial summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve financial summary")


@router.get("/transactions/recent")
async def get_recent_transactions(
    limit: int = Query(10, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel:
    """Get recent transactions."""
    try:
        # Get user accounts
        account_ids = db.query(Account.id).filter(
            Account.user_id == current_user.id,
            Account.is_active == True
        ).subquery()

        # Get recent transactions
        transactions = db.query(Transaction).filter(
            Transaction.account_id.in_(account_ids)
        ).order_by(Transaction.date.desc()).limit(limit).all()

        # Format transactions for frontend
        data = []
        for t in transactions:
            account = db.query(Account).filter(Account.id == t.account_id).first()
            data.append({
                "id": str(t.id),
                "date": t.date.isoformat(),
                "description": t.name or t.merchant_name or "Unknown",
                "amount": float(t.amount) if t.amount else 0,
                "category": t.user_category_override or t.subcategory or "Uncategorized",
                "account": account.name if account else "Unknown",
                "merchant": t.merchant_name,
                "type": "debit" if (t.amount or 0) > 0 else "credit"
            })

        return ResponseModel(data=data)

    except Exception as e:
        logger.error(f"Failed to get recent transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transactions")


@router.get("/spending/by-category")
async def get_spending_by_category(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel:
    """Get spending grouped by category."""
    try:
        start_date = date.today() - timedelta(days=days)

        # Get user accounts
        account_ids = db.query(Account.id).filter(
            Account.user_id == current_user.id,
            Account.is_active == True
        ).subquery()

        # Get spending by category - use actual columns not properties
        spending = db.query(
            func.coalesce(Transaction.user_category_override, Transaction.subcategory, 'Uncategorized').label('category'),
            func.sum(Transaction.amount * 100).label("total")
        ).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_date,
            Transaction.amount > 0  # Only expenses
        ).group_by(
            func.coalesce(Transaction.user_category_override, Transaction.subcategory, 'Uncategorized')
        ).all()

        # Calculate total and format data
        total = sum(s.total for s in spending if s.total)
        colors = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899"]

        data = []
        for i, s in enumerate(spending):
            if s.total:
                value = s.total / 100
                data.append({
                    "name": s.category or "Other",
                    "value": value,
                    "color": colors[i % len(colors)],
                    "percentage": (value / (total / 100)) * 100 if total > 0 else 0
                })

        # Sort by value
        data.sort(key=lambda x: x["value"], reverse=True)

        return ResponseModel(data=data)

    except Exception as e:
        logger.error(f"Failed to get spending by category: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve spending data")


@router.get("/trends")
async def get_transaction_trends(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel:
    """Get daily transaction trends."""
    try:
        start_date = date.today() - timedelta(days=days)

        # Get user accounts
        account_ids = db.query(Account.id).filter(
            Account.user_id == current_user.id,
            Account.is_active == True
        ).subquery()

        # Get daily totals
        daily_totals = db.query(
            Transaction.date,
            func.sum(
                case(
                    (Transaction.amount < 0, -Transaction.amount * 100),
                    else_=0
                )
            ).label("income"),
            func.sum(
                case(
                    (Transaction.amount > 0, Transaction.amount * 100),
                    else_=0
                )
            ).label("expenses")
        ).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_date
        ).group_by(Transaction.date).order_by(Transaction.date).all()

        # Format data
        data = []
        for day in daily_totals:
            income = day.income / 100 if day.income else 0
            expenses = -(day.expenses / 100) if day.expenses else 0
            data.append({
                "date": day.date.isoformat(),
                "income": income,
                "expenses": expenses,
                "netFlow": income + expenses
            })

        return ResponseModel(data=data)

    except Exception as e:
        logger.error(f"Failed to get transaction trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends data")


@router.get("/cash-flow")
async def get_cash_flow(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel:
    """Get monthly cash flow data."""
    try:
        # Calculate start date (first day of month X months ago)
        today = date.today()
        start_date = date(today.year, today.month, 1) - timedelta(days=30 * months)

        # Get user accounts
        account_ids = db.query(Account.id).filter(
            Account.user_id == current_user.id,
            Account.is_active == True
        ).subquery()

        # Get monthly totals
        monthly_totals = db.query(
            func.date_trunc('month', Transaction.date).label("month"),
            func.sum(
                case(
                    (Transaction.amount < 0, -Transaction.amount),
                    else_=0
                )
            ).label("income"),
            func.sum(
                case(
                    (Transaction.amount > 0, Transaction.amount),
                    else_=0
                )
            ).label("expenses")
        ).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_date
        ).group_by("month").order_by("month").all()

        # Format data with running balance
        data = []
        running_balance = 0
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for month_data in monthly_totals:
            income = float(month_data.income) if month_data.income else 0
            expenses = -float(month_data.expenses) if month_data.expenses else 0
            net_flow = income + expenses
            running_balance += net_flow

            month_date = month_data.month
            month_name = month_names[month_date.month - 1]

            data.append({
                "month": month_name,
                "income": income,
                "expenses": expenses,
                "netFlow": net_flow,
                "runningBalance": running_balance
            })

        return ResponseModel(data=data)

    except Exception as e:
        logger.error(f"Failed to get cash flow data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cash flow data")


@router.get("/alerts")
async def get_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel:
    """Get financial alerts and notifications."""
    try:
        # For now, return empty array since we don't have alerts implemented
        # In the future, this would check for budget overruns, unusual spending, etc.
        data = []

        return ResponseModel(data=data)

    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/kpis")
async def get_kpis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ResponseModel:
    """Get key performance indicators."""
    try:
        # Get user accounts
        accounts = db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.is_active == True
        ).all()

        # Calculate total balance
        total_balance = sum(
            float(a.current_balance) if a.current_balance else 0
            for a in accounts
        )

        # Get this month's transactions
        start_of_month = date.today().replace(day=1)
        account_ids = [a.id for a in accounts]

        monthly_transactions = db.query(Transaction).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_of_month
        ).all()

        # Calculate income and expenses
        monthly_income = sum(
            float(-t.amount) if t.amount and t.amount < 0 else 0
            for t in monthly_transactions
        )
        monthly_expenses = sum(
            float(t.amount) if t.amount and t.amount > 0 else 0
            for t in monthly_transactions
        )

        # Calculate savings rate
        savings_rate = ((monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0

        data = {
            "totalBalance": total_balance,
            "monthlyIncome": monthly_income,
            "monthlyExpenses": monthly_expenses,
            "savingsRate": savings_rate,
            "accountCount": len(accounts)
        }

        return ResponseModel(data=data)

    except Exception as e:
        logger.error(f"Failed to get KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve KPIs")