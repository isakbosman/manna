"""
Secure database connection and session management.

Implements secure database connections with proper authentication,
connection pooling, SSL configuration, and monitoring.
"""

import logging
import time
import contextlib
from typing import Generator, Optional, Dict, Any
from sqlalchemy import create_engine, MetaData, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy.pool import StaticPool

from ..config import settings
from .secrets import get_secure_database_url, secrets_manager

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class SecureDatabase:
    """
    Secure database manager with connection pooling and monitoring.

    Provides secure database connections with proper authentication,
    SSL configuration, connection validation, and performance monitoring.
    """

    def __init__(self):
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self.metadata: Optional[MetaData] = None
        self.Base = None
        self._connection_stats: Dict[str, Any] = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "last_connection_time": None,
            "average_connection_time": 0.0
        }

    def initialize(self) -> None:
        """Initialize secure database connection."""
        try:
            self._create_engine()
            self._create_session_factory()
            self._setup_base()
            self._setup_event_listeners()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    def _create_engine(self) -> None:
        """Create secure database engine with proper configuration."""
        try:
            # Get secure database URL with credentials from secrets
            database_url = get_secure_database_url()

            # Validate database URL format
            if not database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
                raise DatabaseError("Only PostgreSQL databases are supported")

            # Configure engine options based on environment
            engine_kwargs = {
                "echo": settings.database_echo,
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_pre_ping": True,  # Verify connections before using
                "pool_recycle": 3600,   # Recycle connections after 1 hour
                "connect_args": self._get_connect_args()
            }

            # Use static pool for testing to avoid connection issues
            if settings.environment == "testing":
                engine_kwargs["poolclass"] = StaticPool
                engine_kwargs["pool_size"] = 1
                engine_kwargs["max_overflow"] = 0

            self.engine = create_engine(database_url, **engine_kwargs)

            # Test connection
            self._test_connection()

        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise DatabaseError(f"Engine creation failed: {e}")

    def _get_connect_args(self) -> Dict[str, Any]:
        """Get connection arguments based on environment."""
        connect_args = {
            "application_name": f"manna_{settings.environment}",
            "connect_timeout": 30,
        }

        # SSL configuration for production
        if settings.environment == "production":
            connect_args.update({
                "sslmode": "require",
                "sslcert": secrets_manager.get_secret("db_ssl_cert_path"),
                "sslkey": secrets_manager.get_secret("db_ssl_key_path"),
                "sslrootcert": secrets_manager.get_secret("db_ssl_ca_path"),
            })
            # Remove None values
            connect_args = {k: v for k, v in connect_args.items() if v is not None}

        return connect_args

    def _test_connection(self) -> None:
        """Test database connection and validate credentials."""
        try:
            start_time = time.time()
            with self.engine.connect() as conn:
                # Test basic query
                result = conn.execute("SELECT 1 as test")
                row = result.fetchone()
                if not row or row[0] != 1:
                    raise DatabaseError("Database connection test failed")

                # Test permissions
                conn.execute("SELECT current_user, session_user")

            connection_time = time.time() - start_time
            self._connection_stats["last_connection_time"] = connection_time
            logger.info(f"Database connection test successful ({connection_time:.3f}s)")

        except Exception as e:
            self._connection_stats["failed_connections"] += 1
            logger.error(f"Database connection test failed: {e}")
            raise DatabaseError(f"Connection test failed: {e}")

    def _create_session_factory(self) -> None:
        """Create secure session factory."""
        if not self.engine:
            raise DatabaseError("Engine not initialized")

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False  # Keep objects usable after commit
        )

    def _setup_base(self) -> None:
        """Set up SQLAlchemy base class."""
        self.metadata = MetaData()
        self.Base = declarative_base(metadata=self.metadata)

    def _setup_event_listeners(self) -> None:
        """Set up database event listeners for monitoring and security."""
        if not self.engine:
            return

        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Handle new database connections."""
            self._connection_stats["total_connections"] += 1
            self._connection_stats["active_connections"] += 1

            # Set connection-level security settings
            with dbapi_connection.cursor() as cursor:
                # Set statement timeout (30 seconds)
                cursor.execute("SET statement_timeout = '30s'")
                # Set timezone
                cursor.execute("SET timezone = 'UTC'")
                # Disable autocommit for explicit transaction control
                cursor.execute("SET autocommit = false")

        @event.listens_for(self.engine, "close")
        def on_close(dbapi_connection, connection_record):
            """Handle connection closures."""
            self._connection_stats["active_connections"] = max(
                0, self._connection_stats["active_connections"] - 1
            )

        @event.listens_for(self.engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Handle connection invalidation."""
            logger.warning(f"Database connection invalidated: {exception}")
            self._connection_stats["failed_connections"] += 1

    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with proper cleanup.

        Yields:
            SQLAlchemy session

        Raises:
            DatabaseError: If session creation fails
        """
        if not self.SessionLocal:
            raise DatabaseError("Database not initialized")

        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    @contextlib.contextmanager
    def get_transaction(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic transaction management.

        Yields:
            SQLAlchemy session with transaction
        """
        with self.get_session() as session:
            try:
                session.begin()
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def check_health(self) -> Dict[str, Any]:
        """
        Check database health and return status information.

        Returns:
            Dictionary with health status and metrics
        """
        health_info = {
            "status": "unknown",
            "connection_test": False,
            "stats": self._connection_stats.copy(),
            "engine_info": {},
            "errors": []
        }

        try:
            # Test basic connectivity
            start_time = time.time()
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1, current_timestamp, version()")
                row = result.fetchone()
                if row:
                    health_info["connection_test"] = True
                    health_info["server_version"] = row[2]
                    health_info["server_time"] = row[1]

            health_info["response_time"] = time.time() - start_time

            # Engine information
            if self.engine:
                pool = self.engine.pool
                health_info["engine_info"] = {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                }

            health_info["status"] = "healthy"

        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["errors"].append(str(e))
            logger.error(f"Database health check failed: {e}")

        return health_info

    def create_tables(self) -> None:
        """Create all database tables."""
        if not self.engine or not self.Base:
            raise DatabaseError("Database not initialized")

        try:
            self.Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise DatabaseError(f"Table creation failed: {e}")

    def validate_connection(self) -> bool:
        """
        Validate database connection and credentials.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection validation failed: {e}")
            return False

    def close(self) -> None:
        """Close database connections and cleanup resources."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database instance
db_manager = SecureDatabase()


def init_database() -> None:
    """Initialize the global database instance."""
    db_manager.initialize()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.

    Yields:
        SQLAlchemy session
    """
    yield from db_manager.get_session()


def get_db_transaction() -> Generator[Session, None, None]:
    """
    Get database session with transaction management.

    Yields:
        SQLAlchemy session with transaction
    """
    with db_manager.get_transaction() as session:
        yield session


def check_db_health() -> Dict[str, Any]:
    """Check database health status."""
    return db_manager.check_health()


def create_tables() -> None:
    """Create all database tables."""
    db_manager.create_tables()


def get_engine() -> Engine:
    """Get the database engine."""
    if not db_manager.engine:
        raise DatabaseError("Database not initialized")
    return db_manager.engine


def get_base():
    """Get the SQLAlchemy base class."""
    if not db_manager.Base:
        raise DatabaseError("Database not initialized")
    return db_manager.Base


# For backward compatibility
engine = property(lambda: get_engine())
SessionLocal = property(lambda: db_manager.SessionLocal)
Base = property(lambda: get_base())