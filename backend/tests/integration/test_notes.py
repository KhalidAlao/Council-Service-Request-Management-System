"""
Integration tests for internal notes endpoints.
POST /requests/{id}/notes, GET /requests/{id}/notes
"""

import pytest
from app.models import RequestNote


class TestNotesEndpoint:
    """Test the notes endpoints with real HTTP requests."""

    # ===== POST Tests =====

    def test_admin_can_post_note_on_any_request(self, client, admin_headers, sample_request):
        """Admin: Can post a note on any request."""
        response = client.post(
            f'/api/v1/requests/{sample_request.request_id}/notes',
            headers=admin_headers,
            json={'body': 'Admin note on generic request'}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['body'] == 'Admin note on generic request'

    def test_assigned_officer_can_post_note(self, client, officer_headers, assigned_request):
        """Assigned officer: Can post a note on their assigned request."""
        response = client.post(
            f'/api/v1/requests/{assigned_request.request_id}/notes',
            headers=officer_headers,
            json={'body': 'Officer note on assigned request'}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['body'] == 'Officer note on assigned request'

    def test_uninvolved_officer_cannot_post_note_on_assigned_request(self, client, second_officer_headers, assigned_request):
        """Uninvolved officer: Cannot post note on a request assigned to someone else."""
        response = client.post(
            f'/api/v1/requests/{assigned_request.request_id}/notes',
            headers=second_officer_headers,
            json={'body': 'Uninvolved officer trying to post'}
        )
        assert response.status_code == 403
        assert 'Only the assigned officer can add notes' in response.get_json()['error']

    def test_any_officer_can_post_note_on_unassigned_request(self, client, officer_headers, unassigned_request):
        """Any officer: Can post a note on an unassigned request (triage phase)."""
        response = client.post(
            f'/api/v1/requests/{unassigned_request.request_id}/notes',
            headers=officer_headers,
            json={'body': 'Triage note on unassigned request'}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['body'] == 'Triage note on unassigned request'

    def test_resident_cannot_post_note(self, client, resident_headers, resident_request):
        """Resident: Cannot post a note even on their own request."""
        response = client.post(
            f'/api/v1/requests/{resident_request.request_id}/notes',
            headers=resident_headers,
            json={'body': 'Resident trying to post note'}
        )
        assert response.status_code == 403
        assert 'Insufficient permissions' in response.get_json()['error']

    def test_post_note_empty_body_returns_400(self, client, admin_headers, sample_request):
        """Empty or whitespace-only body should return 400."""
        response = client.post(
            f'/api/v1/requests/{sample_request.request_id}/notes',
            headers=admin_headers,
            json={'body': '   '}
        )
        assert response.status_code == 400
        assert 'Note body cannot be empty' in str(response.get_json())

    # ===== GET Tests =====

    def test_admin_can_view_notes_on_any_request(self, client, admin_headers, sample_request):
        """Admin: Can view notes on any request."""
        # Create a note
        client.post(
            f'/api/v1/requests/{sample_request.request_id}/notes',
            headers=admin_headers,
            json={'body': 'View test note'}
        )
        response = client.get(
            f'/api/v1/requests/{sample_request.request_id}/notes',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        # data is a list, not a dict with a 'data' key
        assert len(data) >= 1
        assert data[0]['body'] == 'View test note'

    def test_assigned_officer_can_view_notes(self, client, officer_headers, assigned_request, admin_headers):
        """Assigned officer: Can view notes on their assigned request."""
        # Create a note using admin_headers
        client.post(
            f'/api/v1/requests/{assigned_request.request_id}/notes',
            headers=admin_headers,
            json={'body': 'Note for assigned officer to view'}
        )
        response = client.get(
            f'/api/v1/requests/{assigned_request.request_id}/notes',
            headers=officer_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1

    def test_uninvolved_officer_can_view_notes_on_any_request(self, client, second_officer_headers, assigned_request, admin_headers):
        """Uninvolved officer: Can view notes (permissive read)."""
        # Create a note using admin_headers
        client.post(
            f'/api/v1/requests/{assigned_request.request_id}/notes',
            headers=admin_headers,
            json={'body': 'Note for uninvolved officer to view'}
        )
        response = client.get(
            f'/api/v1/requests/{assigned_request.request_id}/notes',
            headers=second_officer_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1

    def test_resident_cannot_view_notes(self, client, resident_headers, resident_request, admin_headers):
        """Resident: Cannot view notes even on their own request."""
        # Create a note using admin_headers
        client.post(
            f'/api/v1/requests/{resident_request.request_id}/notes',
            headers=admin_headers,
            json={'body': 'Resident should not see this'}
        )
        response = client.get(
            f'/api/v1/requests/{resident_request.request_id}/notes',
            headers=resident_headers
        )
        assert response.status_code == 403
        assert 'Insufficient permissions' in response.get_json()['error']

    def test_get_notes_request_not_found_returns_404(self, client, admin_headers):
        """Non-existent request should return 404."""
        response = client.get(
            '/api/v1/requests/99999/notes',
            headers=admin_headers
        )
        assert response.status_code == 404
        assert 'Request not found' in response.get_json()['error']