"""
Integration tests for request submission and listing endpoints.
POST /requests, GET /requests, GET /requests/{id}
"""

import pytest
from app.models import ServiceRequest
from app.extensions import db

class TestRequestSubmission:
    """Tests for POST /requests (guest and authenticated)."""

    def test_guest_can_submit_request(self, client, department):
        """Guest: Submit request with guest_name/email/phone should succeed."""
        response = client.post(
            '/api/v1/requests',
            json={
                'title': 'Guest Test Request',
                'description': 'This is a test submission from a guest',
                'location': 'Guest Street 123',
                'category': 'ROADS',
                'guest_name': 'Test Guest',
                'guest_email': 'guest@test.com',
                'guest_phone': '021 555 1234'
            }
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == 'Guest Test Request'
        assert data['status'] == 'SUBMITTED'
        assert data['priority'] == 'MEDIUM'
        assert data['submitted_by'] is None
        
        assert data['department'] is not None
        assert data['department']['department_id'] == department.department_id


    def test_guest_submission_missing_guest_fields_returns_400(self, client):
        """Guest: Missing guest_name/email/phone should return 400."""
        response = client.post(
            '/api/v1/requests',
            json={
                'title': 'Guest Test Request',
                'description': 'Missing guest fields',
                'location': 'Guest Street 123',
                'category': 'ROADS'
            }
        )
        assert response.status_code == 400
        error = response.get_json()
        assert '_schema' in error['error']
        assert 'Guest name, email, and phone are required for unauthenticated submissions' in error['error']['_schema']

    def test_authenticated_user_can_submit_request(self, client, admin_headers, admin_user, department):
        """Authenticated user: Submit request should succeed without guest fields."""
        response = client.post(
            '/api/v1/requests',
            headers=admin_headers,
            json={
                'title': 'Auth Test Request',
                'description': 'This is a test submission from an authenticated user',
                'location': 'Auth Street 456',
                'category': 'WASTE'
            }
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == 'Auth Test Request'
        assert data['status'] == 'SUBMITTED'
        assert data['submitted_by']['user_id'] == admin_user.user_id
        assert data['submitted_by']['email'] == admin_user.email

        # Verify in DB
        request_obj = db.session.get(ServiceRequest, data['request_id'])
        assert request_obj.submitted_by_user_id == admin_user.user_id
        assert request_obj.guest_name is None

    def test_authenticated_user_cannot_use_guest_fields(self, client, admin_headers):
        """Authenticated user: Guest fields should be rejected."""
        response = client.post(
            '/api/v1/requests',
            headers=admin_headers,
            json={
                'title': 'Auth Test Request',
                'description': 'Should reject guest fields',
                'location': 'Auth Street 456',
                'category': 'WASTE',
                'guest_name': 'Fake Guest',
                'guest_email': 'fake@test.com',
                'guest_phone': '021 555 9999'
            }
        )
        assert response.status_code == 400
        assert 'Guest fields are not allowed for authenticated users' in str(response.get_json())

    def test_invalid_category_returns_400(self, client):
        """Guest: Invalid category should return 400."""
        response = client.post(
            '/api/v1/requests',
            json={
                'title': 'Invalid Category Test',
                'description': 'This has an invalid category',
                'location': 'Test Street',
                'category': 'INVALID',
                'guest_name': 'Test Guest',
                'guest_email': 'guest@test.com',
                'guest_phone': '021 555 1234'
            }
        )
        assert response.status_code == 400
        assert 'Invalid category' in str(response.get_json())

    def test_priority_is_always_medium(self, client):
        """Guest: priority should always default to MEDIUM (not client-supplied)."""
        response = client.post(
            '/api/v1/requests',
            json={
                'title': 'Priority Test',
                'description': 'Checking priority default',
                'location': 'Priority Street',
                'category': 'ROADS',
                'guest_name': 'Test Guest',
                'guest_email': 'guest@test.com',
                'guest_phone': '021 555 1234'
            }
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['priority'] == 'MEDIUM'  # Not HIGH


class TestRequestListing:
    """Tests for GET /requests (list, filter, pagination)."""

    def test_admin_sees_all_requests(self, client, admin_headers, sample_request, assigned_request):
        """Admin: Should see all requests."""
        response = client.get(
            '/api/v1/requests',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['pagination']['total_items'] >= 2
        # Should include both requests
        request_ids = [r['request_id'] for r in data['data']]
        assert sample_request.request_id in request_ids
        assert assigned_request.request_id in request_ids

    def test_officer_sees_all_requests(self, client, officer_headers, sample_request, assigned_request):
        """Officer: Should see all requests (same as admin)."""
        response = client.get(
            '/api/v1/requests',
            headers=officer_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['pagination']['total_items'] >= 2
        request_ids = [r['request_id'] for r in data['data']]
        assert sample_request.request_id in request_ids
        assert assigned_request.request_id in request_ids

    def test_resident_sees_only_own_requests(self, client, resident_headers, resident_request, sample_request):
        """Resident: Should only see their own requests."""
        response = client.get(
            '/api/v1/requests',
            headers=resident_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        # Should see resident_request (their own)
        request_ids = [r['request_id'] for r in data['data']]
        assert resident_request.request_id in request_ids
        # Should NOT see sample_request (admin's)
        assert sample_request.request_id not in request_ids

    def test_list_filter_by_status(self, client, admin_headers, officer_headers, sample_request):
        """Filter requests by status."""
        # Use officer_headers (officer can set UNDER_REVIEW)
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        assert response.status_code == 200

        # Filter by status
        response = client.get(
            '/api/v1/requests?status=UNDER_REVIEW',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        for r in data['data']:
            assert r['status'] == 'UNDER_REVIEW'

    def test_list_filter_by_category(self, client, admin_headers, sample_request):
        """Filter requests by category."""
        # sample_request is ROADS
        response = client.get(
            '/api/v1/requests?category=ROADS',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        for r in data['data']:
            assert r['category'] == 'ROADS'

    def test_list_pagination(self, client, admin_headers):
        """Test pagination with page and limit."""
        # Create multiple requests
        for i in range(5):
            client.post(
                '/api/v1/requests',
                headers=admin_headers,
                json={
                    'title': f'Pagination Test {i}',
                    'description': 'Pagination test',
                    'location': 'Page Street',
                    'category': 'ROADS'
                }
            )

        response = client.get(
            '/api/v1/requests?page=1&limit=3',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 3
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 3
        assert data['pagination']['total_items'] >= 5


class TestSingleRequest:
    """Tests for GET /requests/{id}."""

    def test_admin_can_view_any_request(self, client, admin_headers, sample_request):
        """Admin: Can view any request."""
        response = client.get(
            f'/api/v1/requests/{sample_request.request_id}',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['request_id'] == sample_request.request_id
        assert data['title'] == sample_request.title

    def test_officer_can_view_any_request(self, client, officer_headers, sample_request):
        """Officer: Can view any request."""
        response = client.get(
            f'/api/v1/requests/{sample_request.request_id}',
            headers=officer_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['request_id'] == sample_request.request_id

    def test_resident_can_view_own_request(self, client, resident_headers, resident_request):
        """Resident: Can view their own request."""
        response = client.get(
            f'/api/v1/requests/{resident_request.request_id}',
            headers=resident_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['request_id'] == resident_request.request_id
        assert data['submitted_by']['user_id'] == resident_request.submitted_by_user_id

    def test_resident_cannot_view_others_request(self, client, resident_headers, sample_request):
        """Resident: Cannot view another user's request (404)."""
        response = client.get(
            f'/api/v1/requests/{sample_request.request_id}',
            headers=resident_headers
        )
        assert response.status_code == 404
        assert 'Request not found' in response.get_json()['error']

    def test_invalid_request_id_returns_404(self, client, admin_headers):
        """Invalid request ID should return 404."""
        response = client.get(
            '/api/v1/requests/99999',
            headers=admin_headers
        )
        assert response.status_code == 404
        assert 'Request not found' in response.get_json()['error']

    def test_no_auth_forbidden(self, client, sample_request):
        """No token should return 401 or 403."""
        response = client.get(
            f'/api/v1/requests/{sample_request.request_id}'
        )
        assert response.status_code in [401, 403]