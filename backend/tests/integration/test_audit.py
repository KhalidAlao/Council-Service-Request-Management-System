"""
Integration tests for audit log endpoint.
GET /requests/{id}/audit
"""

import pytest
from app.models import AuditLog


class TestAuditEndpoint:
    """Test the audit log endpoint with real HTTP requests."""

    def test_admin_can_view_audit_on_any_request(self, client, admin_headers, officer_headers, sample_request):
        """Admin: Can view audit log on any request."""
        # Use officer_headers to change status (officer can set UNDER_REVIEW)
        client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        response = client.get(
            f'/api/v1/requests/{sample_request.request_id}/audit',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) >= 1
        assert data['data'][0]['field_changed'] == 'status'

    def test_assigned_officer_can_view_audit(self, client, officer_headers, assigned_request, admin_headers):
        """Assigned officer: Can view audit log on their assigned request."""
        # Officer moves SUBMITTED -> UNDER_REVIEW -> IN_PROGRESS
        # First, change to UNDER_REVIEW
        client.patch(
            f'/api/v1/requests/{assigned_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        # Then change to IN_PROGRESS (still officer)
        client.patch(
            f'/api/v1/requests/{assigned_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'IN_PROGRESS'}
        )
        response = client.get(
            f'/api/v1/requests/{assigned_request.request_id}/audit',
            headers=officer_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) >= 2  # Two status changes

    def test_any_officer_can_view_audit_on_unassigned_request(self, client, second_officer_headers, unassigned_request, officer_headers):
        """Any officer: Can view audit on an unassigned request."""
        # Use officer_headers to change status (officer can set UNDER_REVIEW)
        client.patch(
            f'/api/v1/requests/{unassigned_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        response = client.get(
            f'/api/v1/requests/{unassigned_request.request_id}/audit',
            headers=second_officer_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) >= 1

    def test_uninvolved_officer_cannot_view_audit_on_assigned_request(self, client, second_officer_headers, assigned_request):
        """Uninvolved officer: Cannot view audit on request assigned to someone else."""
        response = client.get(
            f'/api/v1/requests/{assigned_request.request_id}/audit',
            headers=second_officer_headers
        )
        assert response.status_code == 404
        assert 'Request not found' in response.get_json()['error']

    def test_resident_cannot_view_audit(self, client, resident_headers, resident_request):
        """Resident: Cannot view audit on any request."""
        response = client.get(
            f'/api/v1/requests/{resident_request.request_id}/audit',
            headers=resident_headers
        )
        assert response.status_code == 403
        assert 'Insufficient permissions' in response.get_json()['error']

    def test_audit_request_not_found_returns_404(self, client, admin_headers):
        """Non-existent request should return 404."""
        response = client.get(
            '/api/v1/requests/99999/audit',
            headers=admin_headers
        )
        assert response.status_code == 404
        assert 'Request not found' in response.get_json()['error']