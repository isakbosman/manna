"""Report model for generated financial reports."""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Index,
    CheckConstraint, Integer
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, UUIDMixin, TimestampMixin


class Report(Base, UUIDMixin, TimestampMixin):
    """Generated financial reports and owner packages."""
    
    __tablename__ = "reports"
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Report identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False)  # profit_loss, balance_sheet, cash_flow, owner_package, etc.
    
    # Reporting period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    fiscal_year = Column(Integer, index=True)
    fiscal_quarter = Column(Integer)  # 1-4 for quarterly reports
    
    # Report classification
    is_business_report = Column(Boolean, default=False, nullable=False)
    is_tax_report = Column(Boolean, default=False, nullable=False)
    is_preliminary = Column(Boolean, default=True, nullable=False)  # Draft vs final
    
    # Generation details
    generation_status = Column(String(20), default="pending")  # pending, generating, completed, failed
    generated_at = Column(DateTime(timezone=True))
    generation_duration_ms = Column(Integer)
    
    # Report data
    report_data = Column(JSONB, nullable=False)  # The actual report content
    summary_metrics = Column(JSONB, default=dict)  # Key metrics for quick access
    chart_data = Column(JSONB, default=dict)  # Data for charts/visualizations
    
    # File storage
    file_path = Column(String(500))  # Path to generated file (PDF, Excel, etc.)
    file_format = Column(String(20), default="json")  # json, pdf, excel, csv
    file_size_bytes = Column(Integer)
    
    # Report configuration
    template_id = Column(String(100))  # Template used for generation
    filters = Column(JSONB, default=dict)  # Filters applied during generation
    groupings = Column(JSONB, default=list)  # How data was grouped
    
    # Sharing and access
    is_shared = Column(Boolean, default=False)
    share_token = Column(String(255), unique=True)  # For secure sharing
    share_expires_at = Column(DateTime(timezone=True))
    access_level = Column(String(20), default="private")  # private, shared, public
    
    # Version control
    version = Column(Integer, default=1, nullable=False)
    parent_report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"))
    is_archived = Column(Boolean, default=False)
    
    # Error handling
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Metadata
    tags = Column(JSONB, default=list)
    extra_data = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    parent_report = relationship("Report", remote_side=[id])
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_reports_user_type", "user_id", "report_type"),
        Index("idx_reports_period", "period_start", "period_end"),
        Index("idx_reports_status", "generation_status", "generated_at"),
        Index("idx_reports_fiscal", "fiscal_year", "fiscal_quarter"),
        Index("idx_reports_business", "is_business_report", "user_id"),
        Index("idx_reports_shared", "is_shared", "share_expires_at"),
        Index("idx_reports_version", "parent_report_id", "version"),
        CheckConstraint(
            "report_type IN ('profit_loss', 'balance_sheet', 'cash_flow', 'owner_package', 'tax_summary', 'budget_vs_actual', 'expense_analysis', 'income_analysis', 'custom')",
            name="ck_report_type"
        ),
        CheckConstraint(
            "generation_status IN ('pending', 'generating', 'completed', 'failed', 'cancelled')",
            name="ck_generation_status"
        ),
        CheckConstraint(
            "file_format IN ('json', 'pdf', 'excel', 'csv', 'html')",
            name="ck_file_format"
        ),
        CheckConstraint(
            "access_level IN ('private', 'shared', 'public')",
            name="ck_access_level"
        ),
        CheckConstraint(
            "fiscal_quarter >= 1 AND fiscal_quarter <= 4",
            name="ck_fiscal_quarter"
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_valid_period"
        ),
        CheckConstraint(
            "version > 0",
            name="ck_positive_version"
        ),
    )
    
    @property
    def is_current_month(self) -> bool:
        """Check if report is for the current month."""
        from datetime import datetime
        now = datetime.utcnow()
        return (self.period_start.month == now.month and 
                self.period_start.year == now.year)
    
    @property
    def is_current_year(self) -> bool:
        """Check if report is for the current fiscal year."""
        return self.fiscal_year == datetime.utcnow().year
    
    @property
    def period_length_days(self) -> int:
        """Calculate length of reporting period in days."""
        return (self.period_end - self.period_start).days
    
    @property
    def is_monthly_report(self) -> bool:
        """Check if this is a monthly report."""
        return self.period_length_days <= 31
    
    @property
    def is_quarterly_report(self) -> bool:
        """Check if this is a quarterly report."""
        return 85 <= self.period_length_days <= 95  # ~3 months
    
    @property
    def is_annual_report(self) -> bool:
        """Check if this is an annual report."""
        return self.period_length_days >= 350  # ~1 year
    
    @property
    def is_ready(self) -> bool:
        """Check if report is ready for viewing."""
        return self.generation_status == "completed" and not self.is_archived
    
    @property
    def needs_regeneration(self) -> bool:
        """Check if report needs to be regenerated."""
        from datetime import datetime, timedelta
        
        # If report failed, needs regeneration
        if self.generation_status == "failed":
            return True
        
        # If preliminary and older than 1 day, might need refresh
        if self.is_preliminary and self.generated_at:
            return datetime.utcnow() - self.generated_at > timedelta(days=1)
        
        return False
    
    def generate_share_token(self) -> str:
        """Generate a secure token for sharing."""
        import secrets
        self.share_token = secrets.token_urlsafe(32)
        return self.share_token
    
    def mark_generating(self) -> None:
        """Mark report as currently being generated."""
        self.generation_status = "generating"
        from datetime import datetime
        self.generated_at = datetime.utcnow()
    
    def mark_completed(self, duration_ms: int = None) -> None:
        """Mark report as successfully generated."""
        self.generation_status = "completed"
        self.is_preliminary = False
        if duration_ms:
            self.generation_duration_ms = duration_ms
        
        from datetime import datetime
        if not self.generated_at:
            self.generated_at = datetime.utcnow()
    
    def mark_failed(self, error_code: str, error_message: str) -> None:
        """Mark report generation as failed."""
        self.generation_status = "failed"
        self.error_code = error_code
        self.error_message = error_message
    
    def __repr__(self):
        return (f"<Report(id={self.id}, name='{self.name}', "
                f"type='{self.report_type}', status='{self.generation_status}')>")