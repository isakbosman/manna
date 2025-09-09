"""
Machine Learning schemas for API request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


class MLTrainingRequest(BaseModel):
    """Request for training ML model."""
    start_date: Optional[date] = Field(None, description="Start date for training data")
    end_date: Optional[date] = Field(None, description="End date for training data")
    test_size: float = Field(0.2, ge=0.1, le=0.5, description="Test set size")
    min_samples: int = Field(100, ge=10, description="Minimum samples required")
    categories: Optional[List[str]] = Field(None, description="Specific categories to train on")


class MLTrainingResponse(BaseModel):
    """Response from model training."""
    success: bool
    accuracy: float = Field(..., ge=0, le=1)
    training_samples: int
    test_samples: int
    categories_learned: int
    training_completed_at: datetime
    model_version: str
    metrics: Optional[Dict[str, Any]] = None


class MLFeedback(BaseModel):
    """User feedback on categorization."""
    transaction_id: UUID
    suggested_category: str
    correct_category: str
    was_correct: bool
    confidence: Optional[float] = Field(None, ge=0, le=1)
    
    @validator("was_correct")
    def validate_correctness(cls, v, values):
        if v and values.get("suggested_category") != values.get("correct_category"):
            raise ValueError("Cannot be correct if categories don't match")
        return v


class BatchCategorizationRequest(BaseModel):
    """Request for batch categorization."""
    transaction_ids: List[UUID] = Field(..., min_items=1, max_items=1000)
    auto_apply: bool = Field(False, description="Automatically apply high-confidence categories")
    min_confidence: float = Field(0.8, ge=0, le=1, description="Minimum confidence for auto-apply")
    use_ml: bool = Field(True, description="Use ML model")
    use_rules: bool = Field(True, description="Use rule-based categorization")


class BatchCategorizationResponse(BaseModel):
    """Response from batch categorization."""
    categorizations: List['TransactionCategorization']
    total_processed: int
    auto_applied: int
    average_confidence: float = Field(..., ge=0, le=1)
    processing_time_ms: Optional[int] = None


class MLMetrics(BaseModel):
    """ML model performance metrics."""
    model_loaded: bool
    model_version: str
    last_trained: Optional[datetime] = None
    total_transactions: int
    categorized_by_ml: int
    categorized_by_user: int
    uncategorized: int
    accuracy: Optional[float] = Field(None, ge=0, le=1)
    confidence_threshold: float = Field(..., ge=0, le=1)
    categories_supported: List[str]
    category_distribution: Dict[str, int]
    feedback_samples: int


class ModelConfiguration(BaseModel):
    """ML model configuration."""
    confidence_threshold: Optional[float] = Field(None, ge=0, le=1)
    auto_categorize: Optional[bool] = None
    retrain_frequency_days: Optional[int] = Field(None, ge=1)
    min_samples_per_category: Optional[int] = Field(None, ge=1)
    use_ensemble: Optional[bool] = None


class CategoryPrediction(BaseModel):
    """Single category prediction."""
    category: str
    confidence: float = Field(..., ge=0, le=1)
    rule_based: bool = False
    model_name: Optional[str] = None


class TransactionFeatures(BaseModel):
    """Extracted features from a transaction."""
    text_features: List[str]
    amount_features: Dict[str, float]
    temporal_features: Dict[str, Any]
    merchant_features: Optional[Dict[str, Any]] = None


# Import after definition to avoid circular import
from ..schemas.transaction import TransactionCategorization

# Update forward references
BatchCategorizationResponse.update_forward_refs()