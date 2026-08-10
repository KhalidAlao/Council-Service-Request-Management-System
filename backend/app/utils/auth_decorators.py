"""
Authentication decorators for role-based access control.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt


def role_required(*allowed_roles):
    """
    Decorator to restrict access to specific roles.
    Should be used WITH @jwt_required() on the route.
    
    Usage:
        @jwt_required()
        @role_required('ADMIN', 'SUPPORT_OFFICER')
        def staff_only_endpoint():
            ...
    
    Args:
        *allowed_roles: Variable number of role names allowed to access
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # get_jwt() will have valid claims because @jwt_required ran first
            claims = get_jwt()
            user_role = claims.get('role')
            
            # Check if role is in allowed list
            if user_role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator