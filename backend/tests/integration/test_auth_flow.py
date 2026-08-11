"""
Integration tests for authentication endpoints.
POST /auth/login, POST /auth/refresh
"""

import pytest
from flask_jwt_extended import create_refresh_token


class TestAuthFlow:
    """Test authentication flow."""

    def test_login_valid_credentials_returns_tokens(self, client, admin_user):
        """Valid credentials should return access and refresh tokens."""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'email': admin_user.email,
                'password': 'admin123'
            }
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'Bearer'
        assert data['user']['user_id'] == admin_user.user_id

    def test_login_invalid_password_returns_401(self, client, admin_user):
        """Invalid password should return 401."""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'email': admin_user.email,
                'password': 'wrongpassword'
            }
        )
        assert response.status_code == 401
        assert 'Invalid email or password' in response.get_json()['error']

    def test_login_invalid_email_returns_401(self, client):
        """Non-existent email should return 401."""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'email': 'nonexistent@test.com',
                'password': 'somepass'
            }
        )
        assert response.status_code == 401
        assert 'Invalid email or password' in response.get_json()['error']

    def test_login_deactivated_user_returns_401(self, client, admin_headers, resident_user):
        """Deactivated user should return 401."""
        client.patch(
            f'/api/v1/admin/users/{resident_user.user_id}/deactivate',
            headers=admin_headers,
            json={}
        )
        response = client.post(
            '/api/v1/auth/login',
            json={
                'email': resident_user.email,
                'password': 'resident123'
            }
        )
        assert response.status_code == 401
        assert 'Account is deactivated' in response.get_json()['error']

    def test_refresh_with_valid_token_returns_new_access(self, client, admin_user):
        """Valid refresh token should return a new access token."""
        refresh_token = create_refresh_token(
            identity=str(admin_user.user_id),
            additional_claims={'role': 'ADMIN'}
        )
        response = client.post(
            '/api/v1/auth/refresh',
            headers={'Authorization': f'Bearer {refresh_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert data['token_type'] == 'Bearer'

    def test_refresh_with_invalid_token_returns_422(self, client):
        """Invalid refresh token should return 422 (JWT format error)."""
        response = client.post(
            '/api/v1/auth/refresh',
            headers={'Authorization': 'Bearer invalid.token.here'}
        )
        # Flask-JWT-Extended returns 422 for malformed tokens
        assert response.status_code == 422

    def test_refresh_without_token_returns_401(self, client):
        """Missing refresh token should return 401."""
        response = client.post(
            '/api/v1/auth/refresh'
        )
        assert response.status_code == 401