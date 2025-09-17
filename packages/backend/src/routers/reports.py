"""Reports API endpoints."""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from ..database.base import get_db
from ..dependencies.auth import get_current_user
from ..schemas.user import User
from ..schemas.reports import (
    ReportRequest, ReportResponse, ReportType, ReportPeriod,
    ProfitLossReport, BalanceSheetReport, CashFlowReport,
    TaxSummaryReport, OwnerPackageReport
)
from ..services.report_generator import ReportGeneratorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a financial report."""
    try:
        service = ReportGeneratorService(db)

        # Determine date range
        if request.start_date and request.end_date:
            start_date = request.start_date
            end_date = request.end_date
        elif request.period == ReportPeriod.MONTHLY:
            if not request.month:
                request.month = datetime.now().month
            start_date = datetime(request.year, request.month, 1)
            if request.month == 12:
                end_date = datetime(request.year, 12, 31)
            else:
                end_date = datetime(request.year, request.month + 1, 1) - timedelta(days=1)
        elif request.period == ReportPeriod.QUARTERLY:
            if not request.quarter:
                request.quarter = (datetime.now().month - 1) // 3 + 1
            start_date = datetime(request.year, (request.quarter - 1) * 3 + 1, 1)
            if request.quarter == 4:
                end_date = datetime(request.year, 12, 31)
            else:
                end_date = datetime(request.year, request.quarter * 3 + 1, 1) - timedelta(days=1)
        else:  # YEARLY
            start_date = datetime(request.year, 1, 1)
            end_date = datetime(request.year, 12, 31)

        # Generate report based on type
        if request.report_type == ReportType.PROFIT_LOSS:
            data = service.generate_profit_loss(
                current_user.id,
                start_date,
                end_date,
                request.is_business
            )
        elif request.report_type == ReportType.BALANCE_SHEET:
            data = service.generate_balance_sheet(current_user.id, end_date)
        elif request.report_type == ReportType.CASH_FLOW:
            data = service.generate_cash_flow(current_user.id, start_date, end_date)
        elif request.report_type == ReportType.TAX_SUMMARY:
            data = service.generate_tax_summary(current_user.id, request.year)
        elif request.report_type == ReportType.OWNER_PACKAGE:
            data = service.generate_owner_package(
                current_user.id,
                request.year,
                request.month
            )
        else:
            raise HTTPException(status_code=400, detail="Report type not implemented yet")

        return ReportResponse(
            report_type=request.report_type,
            data=data
        )

    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profit-loss", response_model=ReportResponse)
async def get_profit_loss(
    year: int = Query(..., description="Year for the report"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month for the report"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Quarter for the report"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get P&L statement."""
    service = ReportGeneratorService(db)

    # Determine date range
    if month:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    elif quarter:
        start_date = datetime(year, (quarter - 1) * 3 + 1, 1)
        if quarter == 4:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, quarter * 3 + 1, 1) - timedelta(days=1)
    else:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

    data = service.generate_profit_loss(current_user.id, start_date, end_date)

    return ReportResponse(
        report_type=ReportType.PROFIT_LOSS,
        data=data
    )


@router.get("/balance-sheet", response_model=ReportResponse)
async def get_balance_sheet(
    as_of: Optional[datetime] = Query(None, description="As-of date for the balance sheet"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get balance sheet."""
    service = ReportGeneratorService(db)

    if not as_of:
        as_of = datetime.now()

    data = service.generate_balance_sheet(current_user.id, as_of)

    return ReportResponse(
        report_type=ReportType.BALANCE_SHEET,
        data=data
    )


@router.get("/cash-flow", response_model=ReportResponse)
async def get_cash_flow(
    year: int = Query(..., description="Year for the report"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month for the report"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Quarter for the report"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cash flow statement."""
    service = ReportGeneratorService(db)

    # Determine date range
    if month:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    elif quarter:
        start_date = datetime(year, (quarter - 1) * 3 + 1, 1)
        if quarter == 4:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, quarter * 3 + 1, 1) - timedelta(days=1)
    else:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

    data = service.generate_cash_flow(current_user.id, start_date, end_date)

    return ReportResponse(
        report_type=ReportType.CASH_FLOW,
        data=data
    )


@router.get("/tax-summary", response_model=ReportResponse)
async def get_tax_summary(
    year: int = Query(..., description="Tax year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tax summary for the year."""
    service = ReportGeneratorService(db)

    data = service.generate_tax_summary(current_user.id, year)

    return ReportResponse(
        report_type=ReportType.TAX_SUMMARY,
        data=data
    )


@router.get("/owner-package", response_model=ReportResponse)
async def get_owner_package(
    year: int = Query(..., description="Year for the report"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month for the report"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive owner package."""
    service = ReportGeneratorService(db)

    data = service.generate_owner_package(current_user.id, year, month)

    return ReportResponse(
        report_type=ReportType.OWNER_PACKAGE,
        data=data
    )