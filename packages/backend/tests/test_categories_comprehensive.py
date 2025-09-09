"""
Comprehensive tests for category management endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from src.database.models import User, Category


class TestCategoryEndpoints:
    """Comprehensive test suite for category endpoints."""

    def test_list_categories_empty(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test listing categories when user has none."""
        response = client.get("/api/v1/categories/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 0
        assert data["categories"] == []
        assert data["page"] == 1
        assert data["per_page"] == 20

    def test_list_categories_with_data(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db_session: Session
    ):
        """Test listing categories with sample data."""
        # Create test categories
        categories = [
            Category(
                user_id=test_user.id,
                name="Groceries",
                type="expense",
                color="#4CAF50",
                icon="shopping_cart",
                description="Food and grocery expenses"
            ),
            Category(
                user_id=test_user.id,
                name="Salary",
                type="income",
                color="#2196F3",
                icon="account_balance_wallet",
                description="Monthly salary income"
            ),
            Category(
                user_id=test_user.id,
                name="Transportation",
                type="expense",
                color="#FF9800",
                icon="directions_car",
                description="Car and public transport expenses"
            )
        ]
        
        for category in categories:
            db_session.add(category)
        db_session.commit()
        
        response = client.get("/api/v1/categories/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3
        assert len(data["categories"]) == 3
        
        # Verify category data structure
        category = data["categories"][0]
        assert "id" in category
        assert "name" in category
        assert "type" in category
        assert "color" in category
        assert "icon" in category

    def test_list_categories_pagination(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test category pagination."""
        # Create 15 test categories
        for i in range(15):
            category = Category(
                user_id=test_user.id,
                name=f"Category {i}",
                type="expense" if i % 2 == 0 else "income",
                color=f"#{i:06x}",
                icon="category",
                description=f"Test category {i}"
            )
            db_session.add(category)
        
        db_session.commit()
        
        # Test first page
        response = client.get("/api/v1/categories/?per_page=10", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 15
        assert len(data["categories"]) == 10
        assert data["page"] == 1
        assert data["per_page"] == 10
        
        # Test second page
        response = client.get("/api/v1/categories/?page=2&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 15
        assert len(data["categories"]) == 5
        assert data["page"] == 2

    def test_list_categories_filtering(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test category filtering by type."""
        categories = [
            Category(
                user_id=test_user.id,
                name="Food",
                type="expense",
                color="#FF5722",
                icon="restaurant"
            ),
            Category(
                user_id=test_user.id,
                name="Freelance",
                type="income",
                color="#4CAF50",
                icon="work"
            ),
            Category(
                user_id=test_user.id,
                name="Rent",
                type="expense",
                color="#9C27B0",
                icon="home"
            )
        ]
        
        for category in categories:
            db_session.add(category)
        db_session.commit()
        
        # Test filtering by expense type
        response = client.get("/api/v1/categories/?category_type=expense", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for category in data["categories"]:
            assert category["type"] == "expense"
        
        # Test filtering by income type
        response = client.get("/api/v1/categories/?category_type=income", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["categories"][0]["type"] == "income"

    def test_create_category_success(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db_session: Session
    ):
        """Test successful category creation."""
        category_data = {
            "name": "Entertainment",
            "type": "expense",
            "color": "#E91E63",
            "icon": "movie",
            "description": "Movies, games, and entertainment expenses"
        }
        
        response = client.post(
            "/api/v1/categories/",
            json=category_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Entertainment"
        assert data["type"] == "expense"
        assert data["color"] == "#E91E63"
        assert data["icon"] == "movie"
        assert data["description"] == "Movies, games, and entertainment expenses"
        assert "id" in data
        assert data["user_id"] == str(test_user.id)
        
        # Verify category was created in database
        category = db_session.query(Category).filter(Category.name == "Entertainment").first()
        assert category is not None
        assert category.user_id == test_user.id

    def test_create_category_validation_errors(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Test category creation validation errors."""
        # Missing required fields
        response = client.post(
            "/api/v1/categories/",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Invalid type
        category_data = {
            "name": "Invalid Type",
            "type": "invalid_type",
            "color": "#000000",
            "icon": "test"
        }
        
        response = client.post(
            "/api/v1/categories/",
            json=category_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Invalid color format
        category_data = {
            "name": "Invalid Color",
            "type": "expense",
            "color": "not-a-color",
            "icon": "test"
        }
        
        response = client.post(
            "/api/v1/categories/",
            json=category_data,
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_duplicate_category_name(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db_session: Session
    ):
        """Test creating category with duplicate name."""
        # Create first category
        category = Category(
            user_id=test_user.id,
            name="Duplicate Test",
            type="expense",
            color="#FF0000",
            icon="test"
        )
        db_session.add(category)
        db_session.commit()
        
        # Try to create duplicate
        category_data = {
            "name": "Duplicate Test",
            "type": "income",
            "color": "#00FF00",
            "icon": "test2"
        }
        
        response = client.post(
            "/api/v1/categories/",
            json=category_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_get_category_success(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db_session: Session
    ):
        """Test getting a specific category."""
        category = Category(
            user_id=test_user.id,
            name="Get Test Category",
            type="expense",
            color="#123456",
            icon="test_icon",
            description="Test description"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        response = client.get(f"/api/v1/categories/{category.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(category.id)
        assert data["name"] == "Get Test Category"
        assert data["type"] == "expense"
        assert data["color"] == "#123456"
        assert data["icon"] == "test_icon"
        assert data["description"] == "Test description"

    def test_get_category_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent category."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/categories/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_category_success(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db_session: Session
    ):
        """Test successful category update."""
        category = Category(
            user_id=test_user.id,
            name="Update Test",
            type="expense",
            color="#000000",
            icon="old_icon",
            description="Old description"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        update_data = {
            "name": "Updated Category",
            "color": "#FFFFFF",
            "icon": "new_icon",
            "description": "New description"
        }
        
        response = client.put(
            f"/api/v1/categories/{category.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Category"
        assert data["color"] == "#FFFFFF"
        assert data["icon"] == "new_icon"
        assert data["description"] == "New description"
        assert data["type"] == "expense"  # Should remain unchanged
        
        # Verify changes in database
        db_session.refresh(category)
        assert category.name == "Updated Category"
        assert category.color == "#FFFFFF"
        assert category.icon == "new_icon"
        assert category.description == "New description"

    def test_update_category_partial(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db_session: Session
    ):
        """Test partial category update."""
        category = Category(
            user_id=test_user.id,
            name="Partial Update",
            type="expense",
            color="#000000",
            icon="icon",
            description="Description"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        # Update only name and color
        update_data = {
            "name": "Partially Updated",
            "color": "#111111"
        }
        
        response = client.put(
            f"/api/v1/categories/{category.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Partially Updated"
        assert data["color"] == "#111111"
        assert data["icon"] == "icon"  # Should remain unchanged
        assert data["description"] == "Description"  # Should remain unchanged

    def test_update_category_duplicate_name(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db_session: Session
    ):
        """Test updating category with duplicate name."""
        # Create two categories
        category1 = Category(
            user_id=test_user.id,
            name="Category 1",
            type="expense",
            color="#000000",
            icon="icon1"
        )
        category2 = Category(
            user_id=test_user.id,
            name="Category 2",
            type="expense",
            color="#111111",
            icon="icon2"
        )
        db_session.add_all([category1, category2])
        db_session.commit()
        db_session.refresh(category1)
        db_session.refresh(category2)
        
        # Try to update category2 with category1's name
        update_data = {"name": "Category 1"}
        
        response = client.put(
            f"/api/v1/categories/{category2.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_delete_category_success(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db_session: Session
    ):
        """Test successful category deletion."""
        category = Category(
            user_id=test_user.id,
            name="Delete Test",
            type="expense",
            color="#000000",
            icon="delete_icon"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        
        response = client.delete(f"/api/v1/categories/{category.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "successfully deleted" in data["message"]
        
        # Verify category was deleted
        deleted_category = db_session.query(Category).filter(Category.id == category.id).first()
        assert deleted_category is None

    def test_delete_category_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent category."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/categories/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_category_statistics(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test getting category usage statistics."""
        from src.database.models import Account, Transaction
        from datetime import date
        
        # Create category and account
        category = Category(
            user_id=test_user.id,
            name="Stats Test",
            type="expense",
            color="#000000",
            icon="stats"
        )
        account = Account(
            user_id=test_user.id,
            plaid_account_id="stats_account",
            name="Stats Account",
            type="depository",
            subtype="checking"
        )
        db_session.add_all([category, account])
        db_session.commit()
        db_session.refresh(category)
        db_session.refresh(account)
        
        # Create transactions in this category
        transactions = [
            Transaction(
                account_id=account.id,
                plaid_transaction_id="stats_txn_1",
                amount_cents=-1000,  # $10.00
                date=date.today(),
                name="Stats Transaction 1",
                category_id=category.id,
                pending=False
            ),
            Transaction(
                account_id=account.id,
                plaid_transaction_id="stats_txn_2",
                amount_cents=-2000,  # $20.00
                date=date.today(),
                name="Stats Transaction 2",
                category_id=category.id,
                pending=False
            )
        ]
        
        for txn in transactions:
            db_session.add(txn)
        db_session.commit()
        
        response = client.get(f"/api/v1/categories/{category.id}/statistics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["category_id"] == str(category.id)
        assert data["transaction_count"] == 2
        assert data["total_amount"] == -30.00
        assert data["average_amount"] == -15.00


class TestCategoryValidation:
    """Test category data validation."""
    
    def test_invalid_category_id_format(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test invalid UUID format for category ID."""
        response = client.get("/api/v1/categories/invalid-uuid", headers=auth_headers)
        assert response.status_code == 422
    
    def test_category_name_length_validation(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test category name length validation."""
        # Name too long
        category_data = {
            "name": "x" * 101,  # Assuming max length is 100
            "type": "expense",
            "color": "#000000",
            "icon": "test"
        }
        
        response = client.post(
            "/api/v1/categories/",
            json=category_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_color_format_validation(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test color format validation."""
        invalid_colors = [
            "red",           # Not hex
            "#GG0000",       # Invalid hex characters
            "#00000",        # Too short
            "#0000000",      # Too long
            "000000",        # Missing #
        ]
        
        for color in invalid_colors:
            category_data = {
                "name": "Color Test",
                "type": "expense",
                "color": color,
                "icon": "test"
            }
            
            response = client.post(
                "/api/v1/categories/",
                json=category_data,
                headers=auth_headers
            )
            assert response.status_code == 422


class TestCategorySecurity:
    """Test category endpoint security."""
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/v1/categories/",
            f"/api/v1/categories/{uuid4()}",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_category_isolation(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session
    ):
        """Test that users can only access their own categories."""
        # Create another user with category
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_verified=True
        )
        db_session.add(other_user)
        db_session.flush()
        
        other_category = Category(
            user_id=other_user.id,
            name="Other User Category",
            type="expense",
            color="#000000",
            icon="other"
        )
        db_session.add(other_category)
        db_session.commit()
        
        # List categories should only return current user's categories
        response = client.get("/api/v1/categories/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        for category in data["categories"]:
            assert category["user_id"] == str(test_user.id)
            assert category["name"] != "Other User Category"
            
        # Direct access to other user's category should fail
        response = client.get(f"/api/v1/categories/{other_category.id}", headers=auth_headers)
        assert response.status_code == 404