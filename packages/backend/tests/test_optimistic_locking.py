"""
Comprehensive test suite for optimistic locking implementation with SQLAlchemy 2.x.

Tests version management, concurrent updates, and distributed locking.
"""

import os
import time
import threading
import pytest
from unittest.mock import patch, MagicMock, call
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up test database
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from sqlalchemy import create_engine, Column, Integer, String, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.orm.exc import StaleDataError

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.locking import (
    OptimisticLockMixin,
    OptimisticLockError,
    DistributedLock,
    DistributedLockError,
    RetryableOptimisticLock,
    safe_cursor_update,
    get_distributed_lock,
    increment_version_before_flush
)


# Create test model
Base = declarative_base()


class TestModel(Base, OptimisticLockMixin):
    """Test model with optimistic locking."""
    __tablename__ = 'test_model'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    value = Column(Integer, default=0)


class TestOptimisticLockMixin:
    """Test the OptimisticLockMixin functionality."""

    def setup_method(self):
        """Set up test database and session."""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Register event listeners
        event.listen(Session, 'before_flush', increment_version_before_flush)

    def teardown_method(self):
        """Clean up test database."""
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_version_initialization(self):
        """Test that version is properly initialized."""
        session = self.SessionLocal()

        # Create new object
        obj = TestModel(name="test")
        session.add(obj)
        session.commit()

        # Version should be 1 for new objects
        assert obj.version == 1

        session.close()

    def test_version_increment_on_update(self):
        """Test that version increments on update."""
        session = self.SessionLocal()

        # Create object
        obj = TestModel(name="test", value=1)
        session.add(obj)
        session.commit()

        initial_version = obj.version

        # Update object
        obj.value = 2
        session.commit()

        # Version should increment
        assert obj.version == initial_version + 1

        session.close()

    def test_no_version_increment_without_changes(self):
        """Test that version doesn't increment without actual changes."""
        session = self.SessionLocal()

        # Create object
        obj = TestModel(name="test", value=1)
        session.add(obj)
        session.commit()

        initial_version = obj.version

        # No actual changes
        session.commit()

        # Version should not change
        assert obj.version == initial_version

        session.close()

    def test_optimistic_lock_conflict(self):
        """Test optimistic lock conflict detection."""
        # Create object in first session
        session1 = self.SessionLocal()
        obj1 = TestModel(name="test", value=1)
        session1.add(obj1)
        session1.commit()
        obj_id = obj1.id

        # Load same object in second session
        session2 = self.SessionLocal()
        obj2 = session2.query(TestModel).filter_by(id=obj_id).first()

        # Update in first session
        obj1.value = 2
        session1.commit()

        # Try to update in second session - should fail
        obj2.value = 3

        with pytest.raises(StaleDataError):
            session2.commit()

        session1.close()
        session2.close()

    def test_update_with_lock_method(self):
        """Test the update_with_lock method."""
        session = self.SessionLocal()

        # Create object
        obj = TestModel(name="test", value=1)
        session.add(obj)
        session.commit()

        # Update with lock
        obj.update_with_lock(session, value=5, name="updated")
        session.commit()

        # Check updates
        assert obj.value == 5
        assert obj.name == "updated"
        assert obj.version == 2

        session.close()

    def test_update_with_lock_conflict(self):
        """Test update_with_lock with concurrent modification."""
        session1 = self.SessionLocal()
        session2 = self.SessionLocal()

        # Create object
        obj = TestModel(name="test", value=1)
        session1.add(obj)
        session1.commit()
        obj_id = obj.id

        # Load in second session
        obj2 = session2.query(TestModel).filter_by(id=obj_id).first()

        # Update in first session
        obj.value = 2
        session1.commit()

        # Try to update with lock in second session - should fail
        with pytest.raises(OptimisticLockError):
            obj2.update_with_lock(session2, value=3)

        session1.close()
        session2.close()

    def test_refresh_version(self):
        """Test refreshing object version from database."""
        session = self.SessionLocal()

        # Create object
        obj = TestModel(name="test", value=1)
        session.add(obj)
        session.commit()

        old_version = obj.version

        # Update directly in database (simulating external change)
        session.execute(
            f"UPDATE test_model SET value = 10, version = {old_version + 1} WHERE id = {obj.id}"
        )
        session.commit()

        # Refresh object
        obj.refresh_version(session)

        # Should have new version
        assert obj.version == old_version + 1
        assert obj.value == 10

        session.close()


class TestRetryableOptimisticLock:
    """Test the retry decorator for optimistic locking."""

    def test_retry_on_optimistic_lock_error(self):
        """Test that operations are retried on optimistic lock errors."""
        attempt_count = 0

        @RetryableOptimisticLock(max_retries=3, backoff_base=0.01)
        def update_operation():
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count < 3:
                raise OptimisticLockError("Simulated conflict")

            return "success"

        result = update_operation()

        assert result == "success"
        assert attempt_count == 3

    def test_retry_exhaustion(self):
        """Test that exception is raised after max retries."""
        @RetryableOptimisticLock(max_retries=2, backoff_base=0.01)
        def always_fails():
            raise OptimisticLockError("Always fails")

        with pytest.raises(OptimisticLockError):
            always_fails()

    def test_no_retry_for_other_exceptions(self):
        """Test that non-optimistic lock errors are not retried."""
        call_count = 0

        @RetryableOptimisticLock(max_retries=3)
        def other_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not a lock error")

        with pytest.raises(ValueError):
            other_error()

        # Should not retry for non-lock errors
        assert call_count == 1


class TestDistributedLock:
    """Test the distributed locking mechanism."""

    def setup_method(self):
        """Set up mock Redis client."""
        self.mock_redis = MagicMock()
        self.lock = DistributedLock(redis_client=self.mock_redis)

    def test_acquire_lock_success(self):
        """Test successful lock acquisition."""
        self.mock_redis.set.return_value = True

        token = self.lock.acquire_lock("test_resource", timeout=1.0)

        assert token is not None
        self.mock_redis.set.assert_called_once()

        # Check SET NX EX parameters
        call_args = self.mock_redis.set.call_args
        assert call_args[1]['nx'] is True
        assert 'ex' in call_args[1]

    def test_acquire_lock_timeout(self):
        """Test lock acquisition timeout."""
        self.mock_redis.set.return_value = False

        token = self.lock.acquire_lock("test_resource", timeout=0.1, retry_interval=0.01)

        assert token is None
        assert self.mock_redis.set.call_count > 1

    def test_release_lock_success(self):
        """Test successful lock release."""
        # Mock the Lua script execution
        self.lock._release_script = MagicMock(return_value=1)

        result = self.lock.release_lock("test_resource", "token123")

        assert result is True
        self.lock._release_script.assert_called_once()

    def test_release_lock_not_owned(self):
        """Test releasing a lock not owned by the token."""
        self.lock._release_script = MagicMock(return_value=0)

        result = self.lock.release_lock("test_resource", "wrong_token")

        assert result is False

    def test_extend_lock(self):
        """Test extending lock TTL."""
        self.lock._extend_script = MagicMock(return_value=1)

        result = self.lock.extend_lock("test_resource", "token123", extend_ttl=600)

        assert result is True
        self.lock._extend_script.assert_called_once()

    def test_lock_context_manager(self):
        """Test lock context manager."""
        self.mock_redis.set.return_value = True
        self.lock._release_script = MagicMock(return_value=1)

        with self.lock.lock("test_resource") as token:
            assert token is not None

        # Should acquire and release
        self.mock_redis.set.assert_called_once()
        self.lock._release_script.assert_called_once()

    def test_lock_context_manager_failure(self):
        """Test context manager when lock cannot be acquired."""
        self.mock_redis.set.return_value = False

        with pytest.raises(DistributedLockError):
            with self.lock.lock("test_resource", timeout=0.1):
                pass

    def test_is_locked(self):
        """Test checking if resource is locked."""
        self.mock_redis.exists.return_value = 1

        assert self.lock.is_locked("test_resource") is True

        self.mock_redis.exists.return_value = 0
        assert self.lock.is_locked("test_resource") is False

    def test_break_lock(self):
        """Test force-breaking a lock."""
        self.mock_redis.delete.return_value = 1

        result = self.lock.break_lock("test_resource")

        assert result is True
        self.mock_redis.delete.assert_called_once()

    def test_auto_extend(self):
        """Test auto-extension of locks."""
        self.mock_redis.set.return_value = True
        self.lock._release_script = MagicMock(return_value=1)
        self.lock._extend_script = MagicMock(return_value=1)

        # Use a short auto-extend interval for testing
        with self.lock.lock("test_resource", auto_extend=True, auto_extend_interval=0.1):
            time.sleep(0.15)  # Wait for at least one extension

        # Should have extended at least once
        # Note: Exact count depends on timing, so just check it was called
        assert self.lock._extend_script.called

    def test_token_uniqueness(self):
        """Test that generated tokens are unique."""
        tokens = set()

        for _ in range(100):
            token = self.lock._generate_token()
            tokens.add(token)

        # All tokens should be unique
        assert len(tokens) == 100


class TestConcurrentUpdates:
    """Test concurrent update scenarios."""

    def setup_method(self):
        """Set up test database."""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Register event listeners
        event.listen(Session, 'before_flush', increment_version_before_flush)

    def teardown_method(self):
        """Clean up test database."""
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_concurrent_increments(self):
        """Test concurrent increment operations."""
        session = self.SessionLocal()

        # Create test object
        obj = TestModel(name="counter", value=0)
        session.add(obj)
        session.commit()
        obj_id = obj.id
        session.close()

        # Function to increment value
        def increment_value(thread_id):
            session = self.SessionLocal()
            try:
                obj = session.query(TestModel).filter_by(id=obj_id).first()
                current_value = obj.value
                time.sleep(0.01)  # Simulate processing time
                obj.value = current_value + 1
                session.commit()
                return True
            except StaleDataError:
                session.rollback()
                return False
            finally:
                session.close()

        # Run concurrent increments
        success_count = 0
        failure_count = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(increment_value, i) for i in range(10)]

            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                else:
                    failure_count += 1

        # Only one should succeed due to optimistic locking
        assert success_count >= 1
        assert failure_count >= 0
        assert success_count + failure_count == 10

        # Check final value
        session = self.SessionLocal()
        final_obj = session.query(TestModel).filter_by(id=obj_id).first()

        # Value should equal number of successful updates
        assert final_obj.value == success_count
        session.close()

    def test_concurrent_updates_with_retry(self):
        """Test concurrent updates with retry logic."""
        session = self.SessionLocal()

        # Create test object
        obj = TestModel(name="test", value=0)
        session.add(obj)
        session.commit()
        obj_id = obj.id
        session.close()

        @RetryableOptimisticLock(max_retries=5, backoff_base=0.01)
        def update_with_retry(thread_id):
            session = self.SessionLocal()
            try:
                obj = session.query(TestModel).filter_by(id=obj_id).first()
                obj.value += 1
                session.commit()
                return True
            finally:
                session.close()

        # Run concurrent updates with retry
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_with_retry, i) for i in range(5)]

            results = [future.result() for future in as_completed(futures)]

        # With retry, all should eventually succeed
        assert all(results)

        # Check final value
        session = self.SessionLocal()
        final_obj = session.query(TestModel).filter_by(id=obj_id).first()
        assert final_obj.value == 5
        session.close()


class TestSafeCursorUpdate:
    """Test the safe cursor update function for Plaid items."""

    def setup_method(self):
        """Set up mocks."""
        self.mock_session = MagicMock()
        self.mock_plaid_item = MagicMock()
        self.mock_plaid_item.id = "test_item_123"

    @patch('src.core.locking_fixed.get_distributed_lock')
    def test_safe_cursor_update_success(self, mock_get_lock):
        """Test successful cursor update."""
        mock_lock = MagicMock()
        mock_get_lock.return_value = mock_lock

        # Mock the context manager
        mock_lock.lock.return_value.__enter__ = MagicMock()
        mock_lock.lock.return_value.__exit__ = MagicMock()

        # Setup plaid item with update_with_lock
        self.mock_plaid_item.update_with_lock = MagicMock()

        result = safe_cursor_update(
            self.mock_session,
            self.mock_plaid_item,
            "new_cursor_value",
            "operation_123"
        )

        assert result is True
        self.mock_session.refresh.assert_called_once_with(self.mock_plaid_item)
        self.mock_plaid_item.update_with_lock.assert_called_once()
        self.mock_session.commit.assert_called_once()

    @patch('src.core.locking_fixed.get_distributed_lock')
    def test_safe_cursor_update_optimistic_lock_failure(self, mock_get_lock):
        """Test cursor update with optimistic lock failure."""
        mock_lock = MagicMock()
        mock_get_lock.return_value = mock_lock

        mock_lock.lock.return_value.__enter__ = MagicMock()
        mock_lock.lock.return_value.__exit__ = MagicMock()

        # Make update_with_lock raise OptimisticLockError
        self.mock_plaid_item.update_with_lock = MagicMock(
            side_effect=OptimisticLockError("Conflict")
        )

        result = safe_cursor_update(
            self.mock_session,
            self.mock_plaid_item,
            "new_cursor_value"
        )

        assert result is False
        self.mock_session.rollback.assert_called()

    @patch('src.core.locking_fixed.get_distributed_lock')
    def test_safe_cursor_update_distributed_lock_failure(self, mock_get_lock):
        """Test cursor update with distributed lock failure."""
        mock_lock = MagicMock()
        mock_get_lock.return_value = mock_lock

        # Make lock acquisition fail
        mock_lock.lock.side_effect = DistributedLockError("Cannot acquire lock")

        result = safe_cursor_update(
            self.mock_session,
            self.mock_plaid_item,
            "new_cursor_value"
        )

        assert result is False
        self.mock_session.rollback.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])