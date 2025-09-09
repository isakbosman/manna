"""
Authentication API Tests
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
from src.utils.security import verify_password, create_access_token


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    @pytest.mark.unit
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
            },
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data
    
    @pytest.mark.unit
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "anotheruser",
                "password": "SecurePass123!",
                "first_name": "Another",
                "last_name": "User",
            },
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.unit
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    def test_login_inactive_user(self, client, db_session, test_user):
        """Test login with inactive user"""
        test_user.is_active = False
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "inactive" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user information"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    @pytest.mark.unit
    def test_get_current_user_no_auth(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.unit
    def test_refresh_token(self, client, test_user):
        """Test token refresh"""
        # First login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.unit
    def test_logout(self, client, auth_headers):
        """Test logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Successfully logged out"
    
    @pytest.mark.unit
    def test_password_reset_request(self, client, test_user):
        """Test password reset request"""
        response = client.post(
            "/api/v1/auth/password-reset",
            json={"email": test_user.email},
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "sent" in response.json()["message"].lower()
    
    @pytest.mark.unit
    def test_expired_token(self, client, test_user):
        """Test accessing protected endpoint with expired token"""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": test_user.email, "user_id": str(test_user.id)},
            expires_delta=timedelta(seconds=-1),
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    def test_invalid_token_format(self, client):
        """Test accessing protected endpoint with invalid token format"""
        headers = {"Authorization": "Bearer invalid_token_format"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.security
    def test_password_hashing(self, db_session, test_user):
        """Test that passwords are properly hashed"""
        assert test_user.hashed_password != "testpassword123"
        assert verify_password("testpassword123", test_user.hashed_password)
        assert not verify_password("wrongpassword", test_user.hashed_password)
    
    @pytest.mark.security
    def test_token_contains_required_claims(self, client, test_user):
        """Test that JWT tokens contain required claims"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        
        token = response.json()["access_token"]
        
        # Decode token to verify claims (in real test, use jwt.decode)
        import jwt
        from src.config import settings
        
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert "sub" in payload
        assert "user_id" in payload
        assert "exp" in payload
    
    @pytest.mark.performance
    def test_login_performance(self, client, test_user, performance_timer):
        """Test login endpoint performance"""
        performance_timer.start()
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        
        performance_timer.stop()
        
        assert response.status_code == status.HTTP_200_OK
        assert performance_timer.elapsed_ms < 200  # Should complete within 200ms
    
    @pytest.mark.integration
    def test_full_auth_flow(self, client):
        """Test complete authentication flow"""
        # 1. Register new user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "flowtest@example.com",
                "username": "flowtest",
                "password": "FlowTest123!",
                "first_name": "Flow",
                "last_name": "Test",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "flowtest@example.com",
                "password": "FlowTest123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        access_token = login_response.json()["access_token"]
        
        # 3. Access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["email"] == "flowtest@example.com"
        
        # 4. Logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == status.HTTP_200_OK