"""
Integration tests for admin user management endpoints.
All endpoints are admin-only.
"""

import pytest
from app.extensions import db  
from app.models import Department


class TestAdminUsers:
    """Test admin user management endpoints."""

    def test_admin_can_list_users(self, client, admin_headers):
        """Admin: Can list all users."""
        response = client.get(
            '/api/v1/admin/users',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['pagination']['total_items'] >= 1
        assert 'data' in data

    def test_admin_can_filter_users_by_role(self, client, admin_headers):
        """Admin: Can filter users by role."""
        response = client.get(
            '/api/v1/admin/users?role=ADMIN',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        for user in data['data']:
            assert user['role'] == 'ADMIN'

    def test_admin_can_filter_users_by_is_active(self, client, admin_headers, resident_user):
        """Admin: Can filter users by active status."""
        # Use resident_user fixture directly
        client.patch(
            f'/api/v1/admin/users/{resident_user.user_id}/deactivate',
            headers=admin_headers,
            json={}
        )
        response = client.get(
            '/api/v1/admin/users?is_active=false',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        for user in data['data']:
            assert user['is_active'] is False

    def test_admin_can_create_support_officer(self, client, admin_headers, department):
        """Admin: Can create a new support officer."""
        response = client.post(
            '/api/v1/admin/users',
            headers=admin_headers,
            json={
                'full_name': 'New Officer',
                'email': 'new.officer@test.com',
                'password': 'securepass123',
                'role': 'SUPPORT_OFFICER',
                'department_id': department.department_id
            }
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['full_name'] == 'New Officer'
        assert data['role'] == 'SUPPORT_OFFICER'
        assert data['department_id'] == department.department_id

    def test_admin_can_create_admin(self, client, admin_headers):
        """Admin: Can create a new admin."""
        response = client.post(
            '/api/v1/admin/users',
            headers=admin_headers,
            json={
                'full_name': 'New Admin',
                'email': 'new.admin@test.com',
                'password': 'securepass123',
                'role': 'ADMIN'
            }
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['full_name'] == 'New Admin'
        assert data['role'] == 'ADMIN'
        assert data['department_id'] is None

    def test_create_user_duplicate_email_returns_400(self, client, admin_headers):
        """Duplicate email should return 400."""
        # Use 8+ character password
        client.post(
            '/api/v1/admin/users',
            headers=admin_headers,
            json={
                'full_name': 'First User',
                'email': 'duplicate@test.com',
                'password': 'securepass123',
                'role': 'SUPPORT_OFFICER',
                'department_id': 1
            }
        )
        response = client.post(
            '/api/v1/admin/users',
            headers=admin_headers,
            json={
                'full_name': 'Second User',
                'email': 'duplicate@test.com',
                'password': 'securepass123',
                'role': 'SUPPORT_OFFICER',
                'department_id': 1
            }
        )
        assert response.status_code == 400
        assert 'Email already in use' in response.get_json()['error']

    def test_create_admin_with_department_returns_400(self, client, admin_headers):
        """Creating an ADMIN with department_id should return 400."""
        response = client.post(
            '/api/v1/admin/users',
            headers=admin_headers,
            json={
                'full_name': 'Invalid Admin',
                'email': 'invalid.admin@test.com',
                'password': 'securepass123',
                'role': 'ADMIN',
                'department_id': 1
            }
        )
        assert response.status_code == 400
        assert 'department_id must not be provided for ADMIN role' in str(response.get_json())

    def test_create_officer_without_department_returns_400(self, client, admin_headers):
        """Creating an officer without department_id should return 400."""
        response = client.post(
            '/api/v1/admin/users',
            headers=admin_headers,
            json={
                'full_name': 'Invalid Officer',
                'email': 'invalid.officer@test.com',
                'password': 'securepass123',
                'role': 'SUPPORT_OFFICER'
            }
        )
        assert response.status_code == 400
        assert 'department_id is required for SUPPORT_OFFICER role' in str(response.get_json())

    def test_admin_can_change_user_role(self, client, admin_headers, resident_user, department):
        """Admin: Can change a user's role."""
        response = client.patch(
            f'/api/v1/admin/users/{resident_user.user_id}/role',
            headers=admin_headers,
            json={
                'role': 'SUPPORT_OFFICER',
                'department_id': department.department_id
            }
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['role'] == 'SUPPORT_OFFICER'
        assert data['user']['department_id'] == department.department_id

    def test_admin_cannot_change_own_role(self, client, admin_headers, admin_user):
        """Admin cannot change their own role (self-protection)."""
        response = client.patch(
            f'/api/v1/admin/users/{admin_user.user_id}/role',
            headers=admin_headers,
            json={'role': 'RESIDENT'}
        )
        assert response.status_code == 400
        assert 'You cannot change your own role' in response.get_json()['error']

    def test_admin_can_change_user_department(self, client, admin_headers, officer_user, department):
        """Admin: Can change an officer's department."""
        # Use db from app.extensions
        dept2 = Department(name='Waste Management')
        db.session.add(dept2)
        db.session.commit()

        response = client.patch(
            f'/api/v1/admin/users/{officer_user.user_id}/department',
            headers=admin_headers,
            json={'department_id': dept2.department_id}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['department_id'] == dept2.department_id
        assert data['user']['department_name'] == 'Waste Management'

    def test_cannot_change_department_for_non_officer(self, client, admin_headers, admin_user):
        """Cannot change department for a non-officer user."""
        response = client.patch(
            f'/api/v1/admin/users/{admin_user.user_id}/department',
            headers=admin_headers,
            json={'department_id': 1}
        )
        assert response.status_code == 400
        assert 'Only support officers can have a department' in response.get_json()['error']

    def test_admin_can_deactivate_user(self, client, admin_headers, resident_user):
        """Admin: Can deactivate a user."""
        response = client.patch(
            f'/api/v1/admin/users/{resident_user.user_id}/deactivate',
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['is_active'] is False
        assert 'deactivated' in data['message'].lower()

    def test_admin_cannot_deactivate_self(self, client, admin_headers, admin_user):
        """Admin cannot deactivate themselves."""
        response = client.patch(
            f'/api/v1/admin/users/{admin_user.user_id}/deactivate',
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 400
        assert 'You cannot deactivate your own account' in response.get_json()['error']

    def test_deactivate_user_not_found_returns_404(self, client, admin_headers):
        """Deactivating non-existent user returns 404."""
        response = client.patch(
            '/api/v1/admin/users/99999/deactivate',
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 404
        assert 'User not found' in response.get_json()['error']