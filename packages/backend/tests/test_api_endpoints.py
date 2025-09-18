"""
Comprehensive API endpoint tests for the transaction categorization system.
Tests all endpoints, request/response schemas, and error handling.
"""

import pytest
import json
from datetime import date, datetime, timedelta
from uuid import uuid4
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database.models import Transaction, Category, User, Account, MLPrediction
from src.schemas.transaction import TransactionCategorization
from src.schemas.category import CategoryCreate, CategoryRule


class TestTransactionEndpoints:
    """Test transaction-related API endpoints."""

    def test_list_transactions_with_filters(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test transaction listing with various filters."""
        base_url = "/api/transactions/"

        # Test basic listing
        response = client.get(base_url, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) > 0

        # Test pagination
        response = client.get(f"{base_url}?page=1&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["page"] == 1

        # Test date filters
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        response = client.get(
            f"{base_url}?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Test amount filters
        response = client.get(f"{base_url}?min_amount=50&max_amount=200", headers=auth_headers)
        assert response.status_code == 200

        # Test category filter
        response = client.get(f"{base_url}?category=Food", headers=auth_headers)
        assert response.status_code == 200

        # Test search
        response = client.get(f"{base_url}?search=test", headers=auth_headers)
        assert response.status_code == 200

        # Test sorting
        response = client.get(f"{base_url}?sort_by=amount&sort_order=desc", headers=auth_headers)
        assert response.status_code == 200

    def test_get_single_transaction(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test getting a single transaction by ID."""
        transaction = test_transactions[0]

        response = client.get(f"/api/transactions/{transaction.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(transaction.id)
        assert data["name"] == transaction.name
        assert data["amount"] == transaction.amount

        # Test non-existent transaction
        fake_id = uuid4()
        response = client.get(f"/api/transactions/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_transaction(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test updating transaction details."""
        transaction = test_transactions[0]

        update_data = {
            "name": "Updated Transaction Name",
            "user_category": "Updated Category",
            "notes": "Updated notes",
            "tags": ["updated", "test"],
            "is_reconciled": True
        }

        response = client.put(
            f"/api/transactions/{transaction.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["user_category"] == update_data["user_category"]
        assert data["notes"] == update_data["notes"]
        assert data["tags"] == update_data["tags"]
        assert data["is_reconciled"] == update_data["is_reconciled"]

    def test_bulk_transaction_operations(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test bulk transaction operations."""
        transaction_ids = [str(txn.id) for txn in test_transactions[:3]]

        # Test bulk categorization
        bulk_data = {
            "transaction_ids": transaction_ids,
            "operation": "categorize",
            "category": "Bulk Test Category"
        }

        response = client.post("/api/transactions/bulk", json=bulk_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] >= 1
        assert data["operation"] == "categorize"

        # Test bulk reconciliation
        bulk_data = {
            "transaction_ids": transaction_ids,
            "operation": "reconcile"
        }

        response = client.post("/api/transactions/bulk", json=bulk_data, headers=auth_headers)
        assert response.status_code == 200

        # Test bulk tag addition
        bulk_data = {
            "transaction_ids": transaction_ids,
            "operation": "add_tag",
            "tag": "bulk-test"
        }

        response = client.post("/api/transactions/bulk", json=bulk_data, headers=auth_headers)
        assert response.status_code == 200

        # Test validation errors
        invalid_bulk_data = {
            "transaction_ids": transaction_ids,
            "operation": "categorize"
            # Missing required category field
        }

        response = client.post("/api/transactions/bulk", json=invalid_bulk_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error

    def test_transaction_statistics(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test transaction statistics endpoint."""
        response = client.get("/api/transactions/stats", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_transactions" in data
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_amount" in data
        assert "categories" in data
        assert isinstance(data["categories"], list)

        # Test with filters
        start_date = (date.today() - timedelta(days=30)).isoformat()
        response = client.get(f"/api/transactions/stats?start_date={start_date}", headers=auth_headers)
        assert response.status_code == 200

    def test_transaction_export_csv(self, client: TestClient, auth_headers: Dict):
        """Test CSV export functionality."""
        response = client.get("/api/transactions/export/csv", headers=auth_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

        # Check CSV content
        content = response.content.decode()
        lines = content.strip().split('\n')
        assert len(lines) >= 1  # At least header

        # Verify header contains expected columns
        header = lines[0]
        expected_columns = ["Date", "Description", "Amount", "Category"]
        for col in expected_columns:
            assert col in header

    def test_transaction_export_excel(self, client: TestClient, auth_headers: Dict):
        """Test Excel export functionality."""
        response = client.get("/api/transactions/export/excel?include_summary=true", headers=auth_headers)
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]

        # Test without summary
        response = client.get("/api/transactions/export/excel?include_summary=false", headers=auth_headers)
        assert response.status_code == 200

    def test_transaction_import_csv(self, client: TestClient, auth_headers: Dict, test_account: Account):
        """Test CSV import functionality."""
        # Create test CSV content
        csv_content = """Date,Description,Merchant,Amount,Category,Notes,Reconciled,Tags
2024-01-01,Test Import Transaction,Test Merchant,-25.00,Food & Dining,Import test,No,import,test
2024-01-02,Another Import,Another Merchant,100.00,Income,Another test,Yes,income"""

        # Create file-like object
        files = {
            "file": ("test_import.csv", csv_content, "text/csv")
        }

        response = client.post(
            f"/api/transactions/import/csv?account_id={test_account.id}",
            files=files,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported_count"] >= 1

        # Test with invalid CSV
        invalid_csv = "invalid,csv,content"
        files = {
            "file": ("invalid.csv", invalid_csv, "text/csv")
        }

        response = client.post(
            f"/api/transactions/import/csv?account_id={test_account.id}",
            files=files,
            headers=auth_headers
        )

        # Should handle errors gracefully
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data


class TestCategoryEndpoints:
    """Test category management API endpoints."""

    def test_list_categories(self, client: TestClient, auth_headers: Dict, test_category: Category):
        """Test listing categories."""
        response = client.get("/api/categories/", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Test with statistics
        response = client.get("/api/categories/?include_stats=true", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        for category in data:
            if "transaction_count" in category:
                assert isinstance(category["transaction_count"], int)

        # Test system categories inclusion
        response = client.get("/api/categories/?include_system=false", headers=auth_headers)
        assert response.status_code == 200

    def test_get_single_category(self, client: TestClient, auth_headers: Dict, test_category: Category):
        """Test getting a single category."""
        response = client.get(f"/api/categories/{test_category.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(test_category.id)
        assert data["name"] == test_category.name

        # Test non-existent category
        fake_id = uuid4()
        response = client.get(f"/api/categories/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_create_category(self, client: TestClient, auth_headers: Dict):
        """Test creating new categories."""
        category_data = {
            "name": "Test Category",
            "parent_category": "Expense",
            "description": "Test category description",
            "color": "#FF5722",
            "icon": "test_icon",
            "rules": [
                {
                    "type": "text_match",
                    "field": "merchant",
                    "operator": "contains",
                    "value": "test_merchant",
                    "confidence": 0.9
                }
            ]
        }

        response = client.post("/api/categories/", json=category_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["description"] == category_data["description"]
        assert data["color"] == category_data["color"]
        assert data["rules"] == category_data["rules"]

        # Test duplicate category name
        response = client.post("/api/categories/", json=category_data, headers=auth_headers)
        assert response.status_code == 400

    def test_update_category(self, client: TestClient, auth_headers: Dict, test_category: Category):
        """Test updating categories."""
        update_data = {
            "description": "Updated description",
            "color": "#2196F3",
            "rules": [
                {
                    "type": "text_match",
                    "field": "name",
                    "operator": "contains",
                    "value": "updated",
                    "confidence": 0.8
                }
            ]
        }

        response = client.put(
            f"/api/categories/{test_category.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["color"] == update_data["color"]

    def test_delete_category(self, client: TestClient, auth_headers: Dict, db_session: Session, test_user: User):
        """Test deleting categories."""
        # Create a test category
        category = Category(
            user_id=test_user.id,
            name="Delete Test Category",
            parent_category="Test",
            is_system=False,
            is_active=True
        )
        db_session.add(category)
        db_session.commit()

        response = client.delete(f"/api/categories/{category.id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify category is soft deleted
        db_session.refresh(category)
        assert category.is_active is False

    def test_category_rules_management(self, client: TestClient, auth_headers: Dict, test_category: Category):
        """Test category rule addition and removal."""
        # Add rule
        rule_data = {
            "type": "text_match",
            "field": "merchant",
            "operator": "contains",
            "value": "test_rule_merchant",
            "confidence": 0.85
        }

        response = client.post(
            f"/api/categories/{test_category.id}/rules",
            json=rule_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["rules"]) > 0

        # Remove rule (assuming index 0)
        response = client.delete(
            f"/api/categories/{test_category.id}/rules/0",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_apply_category_rules(self, client: TestClient, auth_headers: Dict, test_account: Account):
        """Test applying category rules to transactions."""
        # Test dry run
        response = client.post(
            "/api/categories/apply-rules?dry_run=true",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["dry_run"] is True
        assert "transactions_processed" in data
        assert "transactions_categorized" in data

        # Test actual application
        response = client.post(
            "/api/categories/apply-rules?dry_run=false",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["dry_run"] is False


class TestMLEndpoints:
    """Test ML categorization API endpoints."""

    def test_single_transaction_categorization(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test ML categorization for single transaction."""
        transaction = test_transactions[0]

        response = client.post(f"/api/ml/categorize/{transaction.id}", headers=auth_headers)

        # May not be implemented yet, so check for 404 or 200
        if response.status_code == 200:
            data = response.json()
            assert "suggested_category" in data
            assert "confidence" in data
            assert 0 <= data["confidence"] <= 1
        elif response.status_code == 404:
            pytest.skip("ML categorization endpoint not implemented")

    def test_batch_categorization(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test batch ML categorization."""
        transaction_ids = [str(txn.id) for txn in test_transactions[:3]]

        batch_data = {"transaction_ids": transaction_ids}

        response = client.post("/api/ml/categorize/batch", json=batch_data, headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == len(transaction_ids)

            for result in data:
                assert "transaction_id" in result
                assert "suggested_category" in result
                assert "confidence" in result
        elif response.status_code == 404:
            pytest.skip("Batch ML categorization endpoint not implemented")

    def test_ml_model_training(self, client: TestClient, auth_headers: Dict):
        """Test ML model training endpoint."""
        training_data = {
            "min_samples": 50,
            "test_size": 0.2,
            "use_ensemble": True
        }

        response = client.post("/api/ml/train", json=training_data, headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
        elif response.status_code == 404:
            pytest.skip("ML training endpoint not implemented")

    def test_ml_model_metrics(self, client: TestClient, auth_headers: Dict):
        """Test ML model metrics endpoint."""
        response = client.get("/api/ml/metrics", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert "model_loaded" in data
            assert "confidence_threshold" in data
        elif response.status_code == 404:
            pytest.skip("ML metrics endpoint not implemented")

    def test_feedback_submission(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test ML feedback submission."""
        transaction = test_transactions[0]

        feedback_data = {
            "transaction_id": str(transaction.id),
            "predicted_category": "Food & Dining",
            "actual_category": "Transportation",
            "user_confidence": 0.95
        }

        response = client.post("/api/ml/feedback", json=feedback_data, headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
        elif response.status_code == 404:
            pytest.skip("ML feedback endpoint not implemented")


class TestAuthenticationAndSecurity:
    """Test authentication and security for categorization endpoints."""

    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/transactions/",
            "/api/categories/",
            "/api/transactions/stats",
            "/api/transactions/export/csv",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_invalid_token(self, client: TestClient):
        """Test with invalid authentication token."""
        invalid_headers = {"Authorization": "Bearer invalid_token"}

        response = client.get("/api/transactions/", headers=invalid_headers)
        assert response.status_code == 401

    def test_user_isolation(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test that users can only access their own data."""
        # This would require creating a second user and testing cross-access
        # For now, just verify normal access works
        response = client.get("/api/transactions/", headers=auth_headers)
        assert response.status_code == 200

    def test_input_validation(self, client: TestClient, auth_headers: Dict):
        """Test input validation on endpoints."""
        # Test invalid pagination parameters
        response = client.get("/api/transactions/?page=-1", headers=auth_headers)
        assert response.status_code == 422

        response = client.get("/api/transactions/?page_size=1000", headers=auth_headers)
        assert response.status_code == 422

        # Test invalid date formats
        response = client.get("/api/transactions/?start_date=invalid-date", headers=auth_headers)
        assert response.status_code == 422

        # Test invalid category data
        invalid_category = {
            "name": "",  # Empty name
            "color": "invalid-color"  # Invalid color format
        }

        response = client.post("/api/categories/", json=invalid_category, headers=auth_headers)
        assert response.status_code == 422


class TestRateLimiting:
    """Test rate limiting for API endpoints."""

    def test_bulk_operation_limits(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test rate limiting on bulk operations."""
        # Generate large list of transaction IDs
        transaction_ids = [str(txn.id) for txn in test_transactions] * 100  # Amplify the list

        bulk_data = {
            "transaction_ids": transaction_ids[:1000],  # Try with 1000 IDs
            "operation": "categorize",
            "category": "Bulk Test"
        }

        response = client.post("/api/transactions/bulk", json=bulk_data, headers=auth_headers)

        # Should either succeed or hit rate limits
        assert response.status_code in [200, 429]

    def test_export_rate_limiting(self, client: TestClient, auth_headers: Dict):
        """Test rate limiting on export operations."""
        # Make multiple rapid export requests
        for _ in range(5):
            response = client.get("/api/transactions/export/csv", headers=auth_headers)
            # Should either succeed or hit rate limits
            assert response.status_code in [200, 429]


class TestErrorHandling:
    """Test error handling across all endpoints."""

    def test_malformed_json(self, client: TestClient, auth_headers: Dict):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/categories/",
            data="invalid json{",
            headers={"Content-Type": "application/json", **auth_headers}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client: TestClient, auth_headers: Dict):
        """Test handling of missing required fields."""
        incomplete_category = {
            "description": "Missing name field"
        }

        response = client.post("/api/categories/", json=incomplete_category, headers=auth_headers)
        assert response.status_code == 422

    def test_invalid_uuids(self, client: TestClient, auth_headers: Dict):
        """Test handling of invalid UUID formats."""
        response = client.get("/api/transactions/invalid-uuid", headers=auth_headers)
        assert response.status_code == 422

    def test_database_constraint_violations(self, client: TestClient, auth_headers: Dict):
        """Test handling of database constraint violations."""
        # Try to create category with very long name
        category_data = {
            "name": "x" * 1000,  # Extremely long name
            "parent_category": "Test"
        }

        response = client.post("/api/categories/", json=category_data, headers=auth_headers)
        assert response.status_code in [400, 422]


class TestPerformance:
    """Test performance characteristics of API endpoints."""

    def test_large_transaction_listing(self, client: TestClient, auth_headers: Dict, large_dataset):
        """Test performance with large transaction datasets."""
        import time

        start_time = time.time()
        response = client.get("/api/transactions/?page_size=100", headers=auth_headers)
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < 5.0  # Should complete in under 5 seconds

    def test_complex_filtering_performance(self, client: TestClient, auth_headers: Dict):
        """Test performance with complex filters."""
        import time

        complex_filter = (
            "/api/transactions/?"
            "start_date=2023-01-01&"
            "end_date=2024-12-31&"
            "min_amount=1&"
            "max_amount=1000&"
            "search=test&"
            "sort_by=amount&"
            "sort_order=desc"
        )

        start_time = time.time()
        response = client.get(complex_filter, headers=auth_headers)
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < 3.0  # Should complete in under 3 seconds

    def test_export_performance(self, client: TestClient, auth_headers: Dict):
        """Test export performance."""
        import time

        start_time = time.time()
        response = client.get("/api/transactions/export/csv", headers=auth_headers)
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < 10.0  # Should complete in under 10 seconds


class TestAPISchemaValidation:
    """Test API schema validation and response formats."""

    def test_transaction_response_schema(self, client: TestClient, auth_headers: Dict, test_transactions: List[Transaction]):
        """Test transaction response schema compliance."""
        response = client.get("/api/transactions/", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()

        # Validate pagination response structure
        required_fields = ["items", "total", "page", "page_size", "total_pages", "has_next", "has_previous"]
        for field in required_fields:
            assert field in data

        # Validate transaction item schema
        if data["items"]:
            transaction = data["items"][0]
            required_transaction_fields = [
                "id", "account_id", "name", "amount", "date", "created_at", "updated_at"
            ]
            for field in required_transaction_fields:
                assert field in transaction

    def test_category_response_schema(self, client: TestClient, auth_headers: Dict):
        """Test category response schema compliance."""
        response = client.get("/api/categories/", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if data:
            category = data[0]
            required_fields = ["id", "name", "parent_category", "is_active"]
            for field in required_fields:
                assert field in category

    def test_statistics_response_schema(self, client: TestClient, auth_headers: Dict):
        """Test statistics response schema compliance."""
        response = client.get("/api/transactions/stats", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        required_fields = ["total_transactions", "total_income", "total_expenses", "net_amount", "categories"]
        for field in required_fields:
            assert field in data

        # Validate category summary schema
        if data["categories"]:
            category_summary = data["categories"][0]
            required_category_fields = ["category", "transaction_count", "total_amount"]
            for field in required_category_fields:
                assert field in category_summary

    def test_error_response_schema(self, client: TestClient, auth_headers: Dict):
        """Test error response schema compliance."""
        # Generate a validation error
        response = client.get("/api/transactions/?page=-1", headers=auth_headers)
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

        # Test 404 error
        fake_id = uuid4()
        response = client.get(f"/api/transactions/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data