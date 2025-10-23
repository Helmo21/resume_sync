"""
Tests for Authentication and JWT token handling.

Tests:
- JWT token creation
- JWT token validation
- Token expiration
- User authentication
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.config import settings
from app.models.user import User


@pytest.mark.unit
class TestJWTTokens:
    """Unit tests for JWT token generation and validation."""

    def test_create_jwt_token_for_user(self, test_user: User):
        """Test creating a valid JWT token for a user."""
        # Arrange
        payload = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        # Act
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_validate_jwt_token(self, test_user: User, test_jwt_token: str):
        """Test decoding and validating a JWT token."""
        # Act
        decoded = jwt.decode(
            test_jwt_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        # Assert
        assert decoded["sub"] == str(test_user.id)
        assert decoded["email"] == test_user.email
        assert "exp" in decoded

    def test_expired_jwt_token_rejected(self, test_user: User):
        """Test that expired tokens are rejected."""
        # Arrange - Create expired token
        payload = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Act & Assert
        with pytest.raises(JWTError):
            jwt.decode(
                expired_token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )

    def test_invalid_jwt_token_rejected(self):
        """Test that invalid tokens are rejected."""
        # Arrange
        invalid_token = "invalid.token.here"

        # Act & Assert
        with pytest.raises(JWTError):
            jwt.decode(
                invalid_token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )

    def test_jwt_token_with_wrong_secret_rejected(self, test_jwt_token: str):
        """Test that tokens signed with wrong secret are rejected."""
        # Act & Assert
        with pytest.raises(JWTError):
            jwt.decode(
                test_jwt_token,
                "wrong-secret-key",
                algorithms=["HS256"]
            )


@pytest.mark.integration
class TestAuthenticationEndpoints:
    """Integration tests for authentication API endpoints."""

    def test_get_current_user_with_valid_token(
        self,
        client,
        test_user: User,
        auth_headers: dict
    ):
        """Test getting current user with valid JWT token."""
        # Act
        response = client.get("/api/auth/me", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)

    def test_get_current_user_without_token(self, client):
        """Test that requests without token are rejected."""
        # Act
        response = client.get("/api/auth/me")

        # Assert
        assert response.status_code == 401

    def test_get_current_user_with_invalid_token(self, client):
        """Test that requests with invalid token are rejected."""
        # Arrange
        headers = {"Authorization": "Bearer invalid.token.here"}

        # Act
        response = client.get("/api/auth/me", headers=headers)

        # Assert
        assert response.status_code == 401
