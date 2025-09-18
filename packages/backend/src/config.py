"""
Configuration management for Manna Financial Platform.
Uses environment variables with Pydantic for validation.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Settings
    app_name: str = "Manna Financial Platform"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # API Settings
    api_prefix: str = "/api/v1"
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database Settings
    database_url: str = Field(
        default="postgresql://postgres@localhost:5432/manna",
        env="DATABASE_URL"
    )
    database_password: Optional[str] = Field(default=None, env="DATABASE_PASSWORD")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")  # 1 hour default
    
    # Security Settings
    secret_key: str = Field(
        default="development-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    encryption_key: Optional[str] = Field(default=None, env="MANNA_ENCRYPTION_KEY")
    encryption_key_aes256: Optional[str] = Field(default=None, env="MANNA_ENCRYPTION_KEY_AES256")
    jwt_signing_key: Optional[str] = Field(default=None, env="JWT_SIGNING_KEY")
    require_https: bool = Field(default=False, env="REQUIRE_HTTPS")
    secure_cookies: bool = Field(default=False, env="SECURE_COOKIES")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, env="JWT_EXPIRATION_MINUTES")
    jwt_refresh_expiration_days: int = Field(default=7, env="JWT_REFRESH_EXPIRATION_DAYS")
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    
    # Plaid Settings
    plaid_client_id: Optional[str] = Field(default=None, env="PLAID_CLIENT_ID")
    plaid_secret: Optional[str] = Field(default=None, env="PLAID_SECRET")
    plaid_environment: str = Field(default="sandbox", env="PLAID_ENVIRONMENT")
    plaid_products: List[str] = Field(
        default=["transactions", "accounts", "identity"],
        env="PLAID_PRODUCTS"
    )
    plaid_country_codes: List[str] = Field(
        default=["US"],
        env="PLAID_COUNTRY_CODES"
    )
    plaid_webhook_url: Optional[str] = Field(default=None, env="PLAID_WEBHOOK_URL")
    
    # Celery Settings
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        env="CELERY_RESULT_BACKEND"
    )
    
    # ML Settings
    ml_model_path: str = Field(
        default="./models/categorization",
        env="ML_MODEL_PATH"
    )
    ml_confidence_threshold: float = Field(default=0.75, env="ML_CONFIDENCE_THRESHOLD")
    ml_batch_size: int = Field(default=32, env="ML_BATCH_SIZE")
    
    # Logging Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Security Audit Settings
    audit_logging_enabled: bool = Field(default=True, env="AUDIT_LOGGING_ENABLED")
    security_headers_enabled: bool = Field(default=True, env="SECURITY_HEADERS_ENABLED")
    rate_limiting_enabled: bool = Field(default=True, env="RATE_LIMITING_ENABLED")

    # Encryption Settings
    field_encryption_enabled: bool = Field(default=True, env="FIELD_ENCRYPTION_ENABLED")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Pagination Settings
    default_page_size: int = Field(default=50, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=200, env="MAX_PAGE_SIZE")
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment is one of allowed values."""
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("plaid_environment")
    def validate_plaid_environment(cls, v):
        """Validate Plaid environment."""
        allowed = ["sandbox", "development", "production"]
        if v not in allowed:
            raise ValueError(f"Plaid environment must be one of {allowed}")
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        """Ensure secret key is changed in production."""
        if values.get("environment") == "production" and v == "development-secret-key-change-in-production":
            raise ValueError("Secret key must be changed in production!")
        return v

    @validator("database_url")
    def validate_database_url(cls, v, values):
        """Validate database URL security."""
        if values.get("environment") == "production":
            # Check for blank password in production
            if ":@" in v:
                raise ValueError("Database password required in production")
            # Require SSL in production
            if not any(param in v for param in ["sslmode=require", "sslmode=prefer"]):
                import logging
                logging.getLogger(__name__).warning(
                    "SSL not explicitly configured for production database"
                )
        return v

    @validator("require_https")
    def validate_https(cls, v, values):
        """Require HTTPS in production."""
        if values.get("environment") == "production" and not v:
            import logging
            logging.getLogger(__name__).warning(
                "HTTPS not required in production - this is insecure"
            )
        return v
    
    class Config:
        """Pydantic config."""
        env_file = ["../../.env", ".env"]  # Check parent directory first, then current
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file
        
        # Allow parsing of complex types from environment
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            """Parse environment variables for complex types."""
            if field_name in ["allowed_origins", "plaid_products", "plaid_country_codes"]:
                # Parse comma-separated lists
                return [x.strip() for x in raw_val.split(",")]
            # Parse boolean values
            if field_name in ["require_https", "secure_cookies", "audit_logging_enabled",
                              "security_headers_enabled", "rate_limiting_enabled", "field_encryption_enabled"]:
                return raw_val.lower() in ("true", "1", "yes", "on")
            return raw_val


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to avoid recreating settings on every call.
    """
    return Settings()


# Create a global settings instance for easy import
settings = get_settings()