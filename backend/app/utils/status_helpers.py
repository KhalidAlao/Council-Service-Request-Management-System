"""
Status transition helpers for service requests.
"""

from flask import jsonify
from app.models import ServiceRequest, AuditLog
from app.extensions import db


# Role → Allowed statuses mapping
ROLE_ALLOWED_STATUSES = {
    'SUPPORT_OFFICER': {
        'UNDER_REVIEW', 'IN_PROGRESS', 'DUPLICATE', 'REJECTED'
    },
    'ADMIN': {
        'RESOLVED', 'CLOSED'
    }
}

# State transition map: current_status → allowed next statuses
STATUS_TRANSITIONS = {
    'SUBMITTED': {'UNDER_REVIEW', 'DUPLICATE', 'REJECTED'},
    'UNDER_REVIEW': {'IN_PROGRESS', 'DUPLICATE', 'REJECTED'},
    'IN_PROGRESS': {'RESOLVED'},
    'RESOLVED': {'CLOSED'},
    'DUPLICATE': set(),      # Terminal — no further transitions
    'REJECTED': set(),        # Terminal — no further transitions
    'CLOSED': set()           # Terminal — no further transitions
}


def validate_transition(current_status, target_status):
    """
    Validate if a status transition is allowed by the state machine.
    
    Args:
        current_status: Current status of the request
        target_status: Desired new status
    
    Returns:
        tuple: (is_valid, error_message)
            is_valid: True if transition is allowed
            error_message: Error message if invalid, None if valid
    """
    allowed = STATUS_TRANSITIONS.get(current_status, set())
    
    if target_status not in allowed:
        return False, f"Invalid status transition from '{current_status}' to '{target_status}'"
    
    return True, None


def log_change(request_id, changed_by_user_id, field_name, old_value, new_value):
    """
    Write an audit log entry for a field change.
    
    Args:
        request_id: ID of the service request
        changed_by_user_id: ID of the user making the change
        field_name: Name of the field being changed
        old_value: Previous value (will be converted to string)
        new_value: New value (will be converted to string)
    """
    audit_entry = AuditLog(
        request_id=request_id,
        changed_by_user_id=changed_by_user_id,
        field_changed=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None
    )
    db.session.add(audit_entry)


def get_request_or_404(request_id):
    """
    Fetch a request by ID or return a 404 response.
    
    Args:
        request_id: ID of the service request
    
    Returns:
        tuple: (request_obj, response)
            request_obj: The request object if found, None if not
            response: JSON response if error, None if success
    """
    request_obj = ServiceRequest.query.get(request_id)
    if not request_obj:
        return None, jsonify({'error': 'Request not found'}), 404
    return request_obj, None, None