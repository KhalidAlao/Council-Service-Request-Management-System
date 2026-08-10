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

def validate_target_officer(target_officer_id):
    """
    Validate that the target user exists, is active, and has SUPPORT_OFFICER role.
    
    Args:
        target_officer_id: ID of the user to assign
    
    Returns:
        tuple: (user_obj, error_response, status_code)
            user_obj: The User object if valid, None if not
            error_response: JSON response if error, None if success
            status_code: HTTP status code if error, None if success
    """
    from app.models import User
    
    target_user = User.query.get(target_officer_id)
    
    if not target_user:
        return None, jsonify({'error': 'User not found'}), 404
    
    if not target_user.is_active:
        return None, jsonify({'error': 'User is deactivated'}), 400
    
    if not target_user.role or target_user.role.name != 'SUPPORT_OFFICER':
        return None, jsonify({'error': 'Target user is not a support officer'}), 400
    
    return target_user, None, None


def can_assign_officer(current_user_id, current_user_role, request_obj, target_user_id):
    """
    Check if a user can assign a request to a target officer.
    """
    if current_user_role == 'ADMIN':
        return True, None
    
    if current_user_role == 'SUPPORT_OFFICER':
        # Case 1: Self-assign (only if currently unassigned)
        if target_user_id == current_user_id:
            if request_obj.assigned_officer_id is None:
                return True, None
            elif request_obj.assigned_officer_id == current_user_id:
                # ✅ Clearer message for already assigned to self
                return False, "You are already assigned to this request"
            else:
                return False, "This request is already assigned to someone else"
        
        # Case 2: Handoff (only if currently assigned to this officer)
        if request_obj.assigned_officer_id == current_user_id:
            return True, None
        
        return False, "You can only self-assign unassigned requests or hand off requests assigned to you"
    
    return False, "You do not have permission to assign officers"