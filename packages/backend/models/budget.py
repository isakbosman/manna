"""Budget models for financial planning and tracking."""

from sqlalchemy import (
    Column, String, Boolean, Numeric, DateTime, Text, ForeignKey, Index,
    CheckConstraint, Integer, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from decimal import Decimal
from .base import Base, UUIDMixin, TimestampMixin


class Budget(Base, UUIDMixin, TimestampMixin):
    """Budget plans for financial management."""
    
    __tablename__ = "budgets"
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Budget identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Budget period
    budget_type = Column(String(20), default="monthly")  # monthly, quarterly, annual, custom
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Budget classification
    is_business_budget = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False)  # Template for creating new budgets
    
    # Overall budget targets
    total_income_target = Column(Numeric(15, 2), default=0)
    total_expense_target = Column(Numeric(15, 2), default=0)
    savings_target = Column(Numeric(15, 2), default=0)
    
    # Status and tracking
    status = Column(String(20), default="draft")  # draft, active, completed, archived
    last_reviewed = Column(DateTime(timezone=True))
    
    # Alerts and notifications
    alert_threshold = Column(Numeric(3, 2), default=0.8)  # Alert at 80% of budget
    enable_alerts = Column(Boolean, default=True)
    
    # Metadata
    tags = Column(JSONB, default=list)
    extra_data = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    budget_items = relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        Index("idx_budgets_user_active", "user_id", "is_active"),
        Index("idx_budgets_period", "period_start", "period_end"),
        Index("idx_budgets_type", "budget_type", "is_active"),
        Index("idx_budgets_business", "is_business_budget", "user_id"),
        Index("idx_budgets_status", "status", "is_active"),
        CheckConstraint(
            "budget_type IN ('monthly', 'quarterly', 'annual', 'custom')",
            name="ck_budget_type"
        ),
        CheckConstraint(
            "status IN ('draft', 'active', 'completed', 'archived')",
            name="ck_budget_status"
        ),
        CheckConstraint(
            "period_end > period_start",
            name="ck_valid_budget_period"
        ),
        CheckConstraint(
            "alert_threshold > 0 AND alert_threshold <= 1",
            name="ck_alert_threshold_range"
        ),
        UniqueConstraint("user_id", "name", "period_start", name="uq_user_budget_period"),
    )
    
    @property
    def total_income_decimal(self) -> Decimal:
        """Return total income target as Decimal."""
        return Decimal(str(self.total_income_target)) if self.total_income_target else Decimal("0.00")
    
    @property
    def total_expense_decimal(self) -> Decimal:
        """Return total expense target as Decimal."""
        return Decimal(str(self.total_expense_target)) if self.total_expense_target else Decimal("0.00")
    
    @property
    def net_target(self) -> Decimal:
        """Calculate net budget target (income - expenses)."""
        return self.total_income_decimal - self.total_expense_decimal
    
    @property
    def is_current(self) -> bool:
        """Check if budget covers the current period."""
        from datetime import datetime
        now = datetime.utcnow()
        return self.period_start <= now <= self.period_end
    
    def __repr__(self):
        return f"<Budget(id={self.id}, name='{self.name}', type='{self.budget_type}')>"


class BudgetItem(Base, UUIDMixin, TimestampMixin):
    """Individual line items within a budget."""
    
    __tablename__ = "budget_items"
    
    # Links
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    
    # Item details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Budget amounts
    budgeted_amount = Column(Numeric(15, 2), nullable=False)
    actual_amount = Column(Numeric(15, 2), default=0)
    
    # Item classification
    item_type = Column(String(20), default="expense")  # income, expense, savings, transfer
    is_fixed = Column(Boolean, default=False)  # Fixed vs variable expense
    is_essential = Column(Boolean, default=True)  # Essential vs discretionary
    
    # Tracking and alerts
    alert_threshold = Column(Numeric(3, 2))  # Override budget-level threshold
    last_updated = Column(DateTime(timezone=True))
    
    # Rollover settings
    allow_rollover = Column(Boolean, default=False)  # Unused budget rolls to next period
    rollover_amount = Column(Numeric(15, 2), default=0)
    
    # Metadata
    notes = Column(Text)
    extra_data = Column(JSONB, default=dict)
    
    # Relationships
    budget = relationship("Budget", back_populates="budget_items")
    category = relationship("Category", back_populates="budget_items")
    
    # Constraints and indexes
    __table_args__ = (
        Index("idx_budget_items_budget", "budget_id"),
        Index("idx_budget_items_category", "category_id"),
        Index("idx_budget_items_type", "item_type", "is_fixed"),
        Index("idx_budget_items_essential", "is_essential"),
        CheckConstraint(
            "item_type IN ('income', 'expense', 'savings', 'transfer')",
            name="ck_budget_item_type"
        ),
        CheckConstraint(
            "budgeted_amount >= 0",
            name="ck_budgeted_amount_positive"
        ),
        CheckConstraint(
            "alert_threshold IS NULL OR (alert_threshold > 0 AND alert_threshold <= 1)",
            name="ck_item_alert_threshold_range"
        ),
        UniqueConstraint("budget_id", "category_id", name="uq_budget_category"),
    )
    
    @property
    def budgeted_decimal(self) -> Decimal:
        """Return budgeted amount as Decimal."""
        return Decimal(str(self.budgeted_amount)) if self.budgeted_amount else Decimal("0.00")
    
    @property
    def actual_decimal(self) -> Decimal:
        """Return actual amount as Decimal."""
        return Decimal(str(self.actual_amount)) if self.actual_amount else Decimal("0.00")
    
    @property
    def variance(self) -> Decimal:
        """Calculate variance (actual - budgeted)."""
        return self.actual_decimal - self.budgeted_decimal
    
    @property
    def variance_percentage(self) -> Decimal:
        """Calculate variance as percentage of budget."""
        if self.budgeted_decimal == 0:
            return Decimal("0.00")
        return (self.variance / self.budgeted_decimal) * 100
    
    @property
    def is_over_budget(self) -> bool:
        """Check if actual spending exceeds budget."""
        return self.actual_decimal > self.budgeted_decimal
    
    @property
    def utilization_percentage(self) -> Decimal:
        """Calculate budget utilization percentage."""
        if self.budgeted_decimal == 0:
            return Decimal("0.00")
        return (self.actual_decimal / self.budgeted_decimal) * 100
    
    @property
    def remaining_budget(self) -> Decimal:
        """Calculate remaining budget amount."""
        return max(Decimal("0.00"), self.budgeted_decimal - self.actual_decimal)
    
    def update_actual_amount(self, new_amount: Decimal) -> None:
        """Update actual amount and last updated timestamp."""
        self.actual_amount = new_amount
        from datetime import datetime
        self.last_updated = datetime.utcnow()
    
    def __repr__(self):
        return (f"<BudgetItem(id={self.id}, name='{self.name}', "
                f"budgeted={self.budgeted_decimal}, actual={self.actual_decimal})>")