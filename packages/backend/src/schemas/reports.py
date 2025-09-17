"""Report schemas for API responses."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Types of financial reports."""
    PROFIT_LOSS = "profit_loss"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    TAX_SUMMARY = "tax_summary"
    OWNER_PACKAGE = "owner_package"
    GENERAL_LEDGER = "general_ledger"
    TRIAL_BALANCE = "trial_balance"


class ReportPeriod(str, Enum):
    """Standard report periods."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ReportRequest(BaseModel):
    """Request to generate a report."""
    report_type: ReportType
    period: ReportPeriod = ReportPeriod.MONTHLY
    year: int
    month: Optional[int] = None
    quarter: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_business: bool = True
    include_charts: bool = True


class ProfitLossReport(BaseModel):
    """P&L statement report."""
    period: str
    revenue: Dict[str, float]
    expenses: Dict[str, float]
    summary: Dict[str, float]


class BalanceSheetReport(BaseModel):
    """Balance sheet report."""
    as_of_date: str
    assets: Dict[str, Any]
    liabilities: Dict[str, Any]
    equity: Dict[str, float]


class CashFlowReport(BaseModel):
    """Cash flow statement report."""
    period: str
    operating: Dict[str, float]
    investing: Dict[str, float]
    financing: Dict[str, float]
    summary: Dict[str, float]


class TaxSummaryReport(BaseModel):
    """Tax summary report."""
    year: int
    business_income: float
    business_expenses: float
    net_business_income: float
    deductions: Dict[str, float]
    estimated_tax: Dict[str, float]


class KPIMetrics(BaseModel):
    """Key performance indicators."""
    revenue_per_month: float
    expense_per_month: float
    profit_margin: float
    expense_ratio: float
    burn_rate: float
    effective_hourly_rate: Optional[float] = None
    cash_runway_months: Optional[float] = None


class OwnerPackageReport(BaseModel):
    """Comprehensive owner package."""
    generated_date: str
    period: Dict[str, Any]
    reports: Dict[str, Any]
    kpis: Dict[str, float]
    insights: List[str]


class ReportResponse(BaseModel):
    """Response containing generated report."""
    report_id: Optional[str] = None
    report_type: ReportType
    generated_at: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]
    file_url: Optional[str] = None
    file_format: str = "json"