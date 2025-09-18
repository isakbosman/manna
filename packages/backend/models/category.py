"""Category model for transaction categorization."""

from sqlalchemy import (
    Column, String, Boolean, Integer, Text, ForeignKey, Index,
    CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, UUIDMixin, TimestampMixin


class Category(Base, UUIDMixin, TimestampMixin):
    """Hierarchical category system for transaction classification."""
    
    __tablename__ = "categories"
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Category hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Classification
    category_type = Column(String(20), default="expense")  # income, expense, transfer
    is_business_category = Column(Boolean, default=False)
    is_tax_deductible = Column(Boolean, default=False)
    is_system_category = Column(Boolean, default=False)  # Built-in categories
    
    # Display and organization
    icon = Column(String(50))  # Icon identifier
    color = Column(String(7))  # Hex color code
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Budget settings
    is_budgetable = Column(Boolean, default=True)
    default_budget_percentage = Column(Integer)  # Percentage of total budget
    
    # Metadata
    extra_data = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User")
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    transactions = relationship("Transaction", back_populates="category")
    ml_predictions = relationship("MLPrediction", back_populates="category")
    categorization_rules = relationship("CategorizationRule", back_populates="category")
    budget_items = relationship("BudgetItem", back_populates="category")
    
    # Constraints and indexes
    __table_args__ = (
        Index("idx_categories_user_active", "user_id", "is_active"),
        Index("idx_categories_parent", "parent_id"),
        Index("idx_categories_type", "category_type", "is_active"),
        Index("idx_categories_system", "is_system_category", "is_active"),
        CheckConstraint(
            "category_type IN ('income', 'expense', 'transfer')",
            name="ck_category_type"
        ),
        UniqueConstraint("user_id", "parent_id", "name", name="uq_category_hierarchy"),
    )
    
    @property
    def full_name(self) -> str:
        """Return full category path (Parent > Child)."""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def is_root_category(self) -> bool:
        """Check if this is a root category (no parent)."""
        return self.parent_id is None
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.full_name}', type='{self.category_type}')>"