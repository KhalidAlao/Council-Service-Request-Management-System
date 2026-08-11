"""
Integration tests for the status change endpoint (PATCH /requests/{id}/status).
"""

import pytest
from app.models import AuditLog
from app.extensions import db

class TestStatusEndpoint:
    """Test the status change endpoint with real HTTP requests."""

    def test_officer_can_move_submitted_to_under_review(self, client, officer_headers, sample_request):
        """Officer: SUBMITTED -> UNDER_REVIEW should succeed."""
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'UNDER_REVIEW'
        assert data['request_id'] == sample_request.request_id

    def test_admin_cannot_move_submitted_to_under_review(self, client, admin_headers, sample_request):
        """Admin: SUBMITTED -> UNDER_REVIEW should be forbidden (403)."""
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=admin_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        assert response.status_code == 403
        assert 'You are not allowed to set status to' in response.get_json()['error']

    def test_officer_cannot_skip_to_resolved(self, client, officer_headers, sample_request):
        """Officer: SUBMITTED -> RESOLVED should be forbidden by role (403)."""
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'RESOLVED'}
        )
        
        assert response.status_code == 403
        assert 'You are not allowed to set status to' in response.get_json()['error']

    def test_officer_can_set_duplicate_with_valid_id(self, client, officer_headers, sample_request, admin_user):
        """Officer: SUBMITTED -> DUPLICATE with valid duplicate_of_request_id."""
        # Create another request to use as duplicate target
        from app.models import ServiceRequest
        from app.extensions import db
        
        target_request = ServiceRequest(
            reference_number='SR-2026-TARGET',
            title='Target Request',
            description='Original request',
            location='Target Loc',
            category='ROADS',
            priority='MEDIUM',
            status='SUBMITTED',
            submitted_by_user_id=admin_user.user_id
        )
        db.session.add(target_request)
        db.session.commit()

        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={
                'status': 'DUPLICATE',
                'duplicate_of_request_id': target_request.request_id
            }
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'DUPLICATE'
        assert data['duplicate_of_request_id'] == target_request.request_id

    def test_officer_cannot_set_duplicate_without_id(self, client, officer_headers, sample_request):
        """Officer: DUPLICATE without duplicate_of_request_id should error (400)."""
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'DUPLICATE'}
        )
        assert response.status_code == 400
        assert 'duplicate_of_request_id is required' in response.get_json()['error']

    def test_officer_cannot_set_duplicate_to_self(self, client, officer_headers, sample_request):
        """Officer: DUPLICATE with self-reference should error (400)."""
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={
                'status': 'DUPLICATE',
                'duplicate_of_request_id': sample_request.request_id
            }
        )
        assert response.status_code == 400
        assert 'cannot be a duplicate of itself' in response.get_json()['error']

    def test_officer_can_set_rejected_with_reason(self, client, officer_headers, sample_request):
        """Officer: SUBMITTED -> REJECTED with rejection_reason should succeed."""
        reason = "Not within council jurisdiction"
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={
                'status': 'REJECTED',
                'rejection_reason': reason
            }
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'REJECTED'
        assert data['rejection_reason'] == reason

        # Verify persistence in DB
        from app.models import ServiceRequest
        from app.extensions import db
        request_obj = db.session.get(ServiceRequest, sample_request.request_id)
        assert request_obj.rejection_reason == reason

    def test_officer_cannot_set_rejected_without_reason(self, client, officer_headers, sample_request):
        """Officer: REJECTED without rejection_reason should error (400)."""
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'REJECTED'}
        )
        assert response.status_code == 400
        assert 'rejection_reason is required' in response.get_json()['error']

    def test_resident_cannot_change_status(self, client, resident_headers, sample_request):
        """Resident: any status change should be forbidden (403)."""
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=resident_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        assert response.status_code == 403
        assert response.get_json()['error'] == 'Insufficient permissions'

    def test_full_workflow_with_role_switching(self, client, admin_headers, officer_headers, sample_request):
        """Full workflow: SUBMITTED -> UNDER_REVIEW -> IN_PROGRESS -> RESOLVED -> CLOSED."""
        # 1. Officer moves to UNDER_REVIEW
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        assert response.status_code == 200
        assert response.get_json()['status'] == 'UNDER_REVIEW'

        # 2. Officer moves to IN_PROGRESS
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'IN_PROGRESS'}
        )
        assert response.status_code == 200
        assert response.get_json()['status'] == 'IN_PROGRESS'

        # 3. Admin moves to RESOLVED
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=admin_headers,
            json={'status': 'RESOLVED'}
        )
        assert response.status_code == 200
        assert response.get_json()['status'] == 'RESOLVED'

        # 4. Admin moves to CLOSED
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=admin_headers,
            json={'status': 'CLOSED'}
        )
        assert response.status_code == 200
        assert response.get_json()['status'] == 'CLOSED'

        # 5. Verify no further transitions allowed (terminal state)
        # Admin trying REJECTED — role check prevents it, so 403
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=admin_headers,
            json={'status': 'REJECTED'}
        )
        
        assert response.status_code == 403
        assert 'You are not allowed to set status to' in response.get_json()['error']

    def test_audit_log_created_on_status_change(self, client, officer_headers, sample_request):
        """Assert that a status change creates an audit log entry."""
        response = client.patch(
            f'/api/v1/requests/{sample_request.request_id}/status',
            headers=officer_headers,
            json={'status': 'UNDER_REVIEW'}
        )
        assert response.status_code == 200

        # Query audit log
        logs = AuditLog.query.filter_by(
            request_id=sample_request.request_id,
            field_changed='status'
        ).all()
        assert len(logs) >= 1
        latest = logs[-1]
        assert latest.old_value == 'SUBMITTED'
        assert latest.new_value == 'UNDER_REVIEW'
        assert latest.changed_by_user_id is not None