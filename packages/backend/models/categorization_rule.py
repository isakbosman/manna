"""Categorization rule model for automated transaction categorization."""

from sqlalchemy import (
    Column, String, Boolean, Integer, Text, ForeignKey, Index,
    CheckConstraint, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, UUIDMixin, TimestampMixin


class CategorizationRule(Base, UUIDMixin, TimestampMixin):
    """Rules for automatic transaction categorization."""
    
    __tablename__ = "categorization_rules"
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    
    # Rule identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Rule type and matching
    rule_type = Column(String(50), nullable=False)  # merchant, keyword, amount, regex, compound
    
    # Pattern matching
    pattern = Column(String(1000), nullable=False)  # The pattern to match
    pattern_type = Column(String(20), default="contains")  # contains, exact, regex, starts_with, ends_with
    case_sensitive = Column(Boolean, default=False)
    
    # Matching fields
    match_fields = Column(JSONB, default=list)  # ['merchant_name', 'name', 'description']
    
    # Conditions
    conditions = Column(JSONB, default=dict)  # Additional conditions (amount range, date range, etc.)
    
    # Rule settings
    priority = Column(Integer, default=100, nullable=False)  # Lower number = higher priority
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_rule = Column(Boolean, default=False)  # Built-in system rules
    
    # Actions
    auto_apply = Column(Boolean, default=True)  # Automatically apply rule
    requires_approval = Column(Boolean, default=False)  # Require user approval
    
    # Business classification
    set_business = Column(Boolean, nullable=True)  # Override business classification
    set_tax_deductible = Column(Boolean, nullable=True)  # Override tax deductible
    
    # Usage statistics
    match_count = Column(Integer, default=0)
    last_matched = Column(DateTime(timezone=True))
    accuracy_score = Column(Integer, default=0)  # User feedback score (-100 to 100)
    
    # Metadata
    tags = Column(JSONB, default=list)
    extra_data = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User")
    category = relationship("Category", back_populates="categorization_rules")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_rules_user_active", "user_id", "is_active"),
        Index("idx_rules_priority", "priority", "is_active"),
        Index("idx_rules_type", "rule_type", "is_active"),
        Index("idx_rules_system", "is_system_rule", "is_active"),
        Index("idx_rules_category", "category_id"),
        Index("idx_rules_pattern", "pattern"),  # For pattern searches
        CheckConstraint(
            "rule_type IN ('merchant', 'keyword', 'amount', 'regex', 'compound', 'ml_assisted')",
            name="ck_rule_type"
        ),
        CheckConstraint(
            "pattern_type IN ('contains', 'exact', 'regex', 'starts_with', 'ends_with', 'fuzzy')",
            name="ck_pattern_type"
        ),
        CheckConstraint(
            "priority >= 0 AND priority <= 1000",
            name="ck_priority_range"
        ),
        CheckConstraint(
            "accuracy_score >= -100 AND accuracy_score <= 100",
            name="ck_accuracy_range"
        ),
    )
    
    @property
    def is_high_priority(self) -> bool:
        """Check if rule has high priority (< 50)."""
        return self.priority < 50
    
    @property
    def is_performing_well(self) -> bool:
        """Check if rule has good accuracy (> 70)."""
        return self.accuracy_score > 70
    
    @property
    def needs_review(self) -> bool:
        """Check if rule needs review due to poor performance."""
        return self.accuracy_score < -50 or (self.match_count > 10 and self.accuracy_score < 0)
    
    def increment_match_count(self) -> None:
        """Increment the match count and update last matched timestamp."""
        self.match_count += 1
        from datetime import datetime
        self.last_matched = datetime.utcnow()
    
    def update_accuracy(self, feedback_score: int) -> None:
        """Update accuracy score based on user feedback.
        
        Args:
            feedback_score: Score from user feedback (-10 to 10)
        """
        # Weighted average with existing score
        if self.match_count <= 1:
            self.accuracy_score = feedback_score * 10  # Scale to -100/100
        else:
            # Weight new feedback at 20%, existing at 80%
            self.accuracy_score = int(self.accuracy_score * 0.8 + feedback_score * 10 * 0.2)
        
        # Clamp to valid range
        self.accuracy_score = max(-100, min(100, self.accuracy_score))
    
    def __repr__(self):
        return (f"<CategorizationRule(id={self.id}, name='{self.name}', "
                f"type='{self.rule_type}', priority={self.priority})>")