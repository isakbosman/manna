"""Database configuration and connection management."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .base import Base
from . import *  # Import all models

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/manna_db"
)

# Engine configuration
engine_config = {
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

# Create engine
engine = create_engine(DATABASE_URL, **engine_config)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables (use with caution!)."""
    Base.metadata.drop_all(bind=engine)


# Event listeners for enhanced functionality
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        cursor.close()


class DatabaseManager:
    """Database management utilities."""
    
    @staticmethod
    def health_check() -> bool:
        """Check database connection health."""
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    @staticmethod
    def get_table_counts() -> dict:
        """Get record counts for all tables."""
        counts = {}
        with SessionLocal() as session:
            try:
                counts["users"] = session.query(User).count()
                counts["institutions"] = session.query(Institution).count()
                counts["accounts"] = session.query(Account).count()
                counts["transactions"] = session.query(Transaction).count()
                counts["categories"] = session.query(Category).count()
                counts["ml_predictions"] = session.query(MLPrediction).count()
                counts["categorization_rules"] = session.query(CategorizationRule).count()
                counts["reports"] = session.query(Report).count()
                counts["budgets"] = session.query(Budget).count()
                counts["budget_items"] = session.query(BudgetItem).count()
                counts["plaid_items"] = session.query(PlaidItem).count()
                counts["plaid_webhooks"] = session.query(PlaidWebhook).count()
                counts["audit_logs"] = session.query(AuditLog).count()
                counts["user_sessions"] = session.query(UserSession).count()
            except Exception as e:
                counts["error"] = str(e)
        
        return counts
    
    @staticmethod
    def vacuum_analyze():
        """Run database maintenance (PostgreSQL)."""
        if "postgresql" in DATABASE_URL:
            with engine.connect() as conn:
                # Run outside transaction
                conn.execute("COMMIT")
                conn.execute("VACUUM ANALYZE")


# Database context manager
class DatabaseContext:
    """Context manager for database sessions."""
    
    def __enter__(self) -> Session:
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()