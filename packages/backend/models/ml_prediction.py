"""ML prediction model for transaction categorization results."""

from sqlalchemy import (
    Column, String, Numeric, DateTime, Text, ForeignKey, Index,
    CheckConstraint, Boolean, Integer
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from decimal import Decimal
from .base import Base, UUIDMixin, TimestampMixin


class MLPrediction(Base, UUIDMixin, TimestampMixin):
    """Machine learning predictions for transaction categorization."""
    
    __tablename__ = "ml_predictions"
    
    # Links
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    
    # Model information
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)  # xgboost, random_forest, neural_net, etc.
    
    # Prediction results
    confidence = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    probability = Column(Numeric(5, 4), nullable=False)  # Probability score
    
    # Alternative predictions
    alternative_predictions = Column(JSONB, default=list)  # Top 3-5 alternatives with scores
    
    # Model features used
    features_used = Column(JSONB, default=dict)  # Feature values that led to prediction
    feature_importance = Column(JSONB, default=dict)  # Feature importance scores
    
    # Prediction metadata
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    processing_time_ms = Column(Integer)  # Time taken for prediction
    
    # Feedback and validation
    is_accepted = Column(Boolean, nullable=True)  # User accepted/rejected prediction
    user_feedback = Column(String(20))  # correct, incorrect, partial, unsure
    feedback_date = Column(DateTime(timezone=True))
    
    # Quality metrics
    is_outlier = Column(Boolean, default=False)  # Prediction deemed unusual
    requires_review = Column(Boolean, default=False)  # Flagged for manual review
    review_reason = Column(String(100))  # Why it needs review
    
    # Relationships
    transaction = relationship("Transaction", back_populates="ml_predictions")
    category = relationship("Category", back_populates="ml_predictions")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_ml_predictions_transaction", "transaction_id"),
        Index("idx_ml_predictions_confidence", "confidence"),
        Index("idx_ml_predictions_model", "model_version", "model_type"),
        Index("idx_ml_predictions_feedback", "user_feedback", "is_accepted"),
        Index("idx_ml_predictions_review", "requires_review", "is_outlier"),
        Index("idx_ml_predictions_date", "prediction_date"),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_confidence_range"
        ),
        CheckConstraint(
            "probability >= 0.0 AND probability <= 1.0",
            name="ck_probability_range"
        ),
        CheckConstraint(
            "user_feedback IN ('correct', 'incorrect', 'partial', 'unsure')",
            name="ck_user_feedback"
        ),
    )
    
    @property
    def confidence_decimal(self) -> Decimal:
        """Return confidence as Decimal for precise calculations."""
        return Decimal(str(self.confidence)) if self.confidence else Decimal("0.0000")
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if prediction has high confidence (>= 0.8)."""
        return self.confidence_decimal >= Decimal("0.8000")
    
    @property
    def is_low_confidence(self) -> bool:
        """Check if prediction has low confidence (< 0.6)."""
        return self.confidence_decimal < Decimal("0.6000")
    
    @property
    def confidence_level(self) -> str:
        """Return human-readable confidence level."""
        conf = self.confidence_decimal
        if conf >= Decimal("0.9"):
            return "very_high"
        elif conf >= Decimal("0.8"):
            return "high"
        elif conf >= Decimal("0.6"):
            return "medium"
        elif conf >= Decimal("0.4"):
            return "low"
        else:
            return "very_low"
    
    def __repr__(self):
        return (f"<MLPrediction(id={self.id}, transaction_id={self.transaction_id}, "
                f"confidence={self.confidence}, category_id={self.category_id})>")