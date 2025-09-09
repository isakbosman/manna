"""
Category schemas for API request/response validation.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID


class CategoryRule(BaseModel):
    """Category matching rule."""
    type: Literal["text", "amount", "pattern"] = Field(..., description="Rule type")
    field: Literal["name", "merchant", "amount"] = Field(..., description="Field to match")
    operator: Literal["contains", "equals", "starts_with", "greater_than", "less_than"] = Field(
        ..., description="Comparison operator"
    )
    value: Any = Field(..., description="Value to match against")
    case_sensitive: bool = Field(False, description="Case sensitive matching")
    
    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v, info):
        field = info.data.get("field")
        if field == "amount" and v not in ["equals", "greater_than", "less_than"]:
            raise ValueError("Amount field only supports equals, greater_than, less_than operators")
        if field in ["name", "merchant"] and v in ["greater_than", "less_than"]:
            raise ValueError("Text fields do not support greater_than or less_than operators")
        return v


class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    parent_category: Optional[str] = Field(None, max_length=100, description="Parent category")
    description: Optional[str] = Field(None, description="Category description")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name or emoji")


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    rules: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Matching rules for auto-categorization"
    )


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    rules: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Category response schema."""
    id: UUID
    user_id: Optional[UUID] = None
    is_system: bool
    is_active: bool
    rules: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CategoryWithStats(CategoryResponse):
    """Category with usage statistics."""
    transaction_count: int = Field(0, description="Number of transactions using this category")
    total_amount: Optional[float] = Field(None, description="Total amount in this category")
    last_used: Optional[datetime] = Field(None, description="Last time category was used")
    
    model_config = ConfigDict(from_attributes=True)


class CategoryTree(BaseModel):
    """Hierarchical category structure."""
    id: UUID
    name: str
    parent_category: Optional[str] = None
    children: List['CategoryTree'] = []
    transaction_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


CategoryTree.update_forward_refs()


class CategoryBulkOperation(BaseModel):
    """Bulk category operation request."""
    category_ids: List[UUID] = Field(..., description="Category IDs to operate on")
    operation: Literal["activate", "deactivate", "delete"] = Field(
        ..., description="Operation to perform"
    )
    reassign_to: Optional[UUID] = Field(
        None, description="Category to reassign transactions to (for delete)"
    )