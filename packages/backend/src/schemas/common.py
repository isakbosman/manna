"""
Common Pydantic schemas used across the application.
"""

from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=50, ge=1, le=200, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.per_page


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    
    @field_validator("pages", mode="before")
    @classmethod
    def calculate_pages(cls, v, info):
        """Calculate total pages from total and per_page."""
        total = info.data.get("total", 0)
        per_page = info.data.get("per_page", 1)
        return (total + per_page - 1) // per_page if per_page > 0 else 0
    
    model_config = ConfigDict(from_attributes=True)


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status")
    timestamp: datetime = Field(description="Current timestamp")
    environment: str = Field(description="Current environment")
    version: str = Field(description="API version")
    database: bool = Field(description="Database connection status")
    redis: bool = Field(description="Redis connection status")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "environment": "development",
                "version": "1.0.0",
                "database": True,
                "redis": True
            }
        }
    )


class ErrorDetail(BaseModel):
    """Error detail information."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "invalid_format"
                    }
                ],
                "request_id": "req_abc123",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    )


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = Field(default=True, description="Success indicator")
    message: str = Field(description="Success message")
    details: Optional[Any] = Field(None, description="Response details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "details": None,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    )