"""
Admin routes: user management, role changes, deactivation.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash
from sqlalchemy import desc

from app.extensions import db
from app.models import User, Role, Department
from app.schemas.user_schemas import (
    UserCreateSchema,
    UserRoleUpdateSchema,
    UserDepartmentUpdateSchema,
    UserAdminResponseSchema
)
from app.utils.auth_decorators import role_required
from app.utils.status_helpers import get_request_or_404

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required('ADMIN')
def list_users():
    """
    List all users with filtering and pagination.
    
    Query Parameters:
        role: Filter by role name
        department_id: Filter by department ID
        is_active: Filter by active status (true/false)
        page: int (default 1)
        limit: int (default 20, max 100)
    """
    # Start with base query
    query = User.query
    
    # --- Dynamic filters ---
    
    # Role filter (join with Role table)
    if role := request.args.get('role'):
        query = query.join(User.role).filter(Role.name == role)
    
    # Department ID filter
    if department_id := request.args.get('department_id', type=int):
        query = query.filter_by(department_id=department_id)
    
    # Active status filter (handles "true" and "false" strings)
    if is_active := request.args.get('is_active'):
        is_active_bool = is_active.lower() == 'true'
        query = query.filter_by(is_active=is_active_bool)
    
    # Sort by most recent first
    query = query.order_by(desc(User.created_at))
    
    # --- Pagination ---
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 20, type=int)
    per_page = min(per_page, 100)
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # --- Serialize response ---
    response_schema = UserAdminResponseSchema(many=True)
    
    return jsonify({
        'data': response_schema.dump(paginated.items),
        'pagination': {
            'page': paginated.page,
            'limit': paginated.per_page,
            'total_items': paginated.total,
            'total_pages': paginated.pages
        }
    }), 200


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def create_user():
    """
    Create a new staff user (SUPPORT_OFFICER or ADMIN).
    
    Request Body:
        {
            "full_name": "string",
            "email": "string",
            "password": "string (min 8 chars)",
            "role": "SUPPORT_OFFICER | ADMIN",
            "department_id": int (required for SUPPORT_OFFICER)
        }
    """
    schema = UserCreateSchema()
    
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    
    # Check if email is already in use
    existing = User.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'error': 'Email already in use'}), 400
    
    # Get the role
    role = Role.query.filter_by(name=data['role']).first()
    if not role:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Hash the password
    password_hash = generate_password_hash(data['password'], method='pbkdf2:sha256')
    
    # Create the user
    user = User(
        full_name=data['full_name'],
        email=data['email'],
        phone=data.get('phone'),
        password_hash=password_hash,
        role_id=role.role_id,
        department_id=data.get('department_id'),
        is_active=True
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Serialize and return
    response_schema = UserAdminResponseSchema()
    result = response_schema.dump(user)
    return jsonify(result), 201

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@role_required('ADMIN')
def get_user(user_id):
    """
    Get a single user by ID.
    """
    user = user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    response_schema = UserAdminResponseSchema()
    result = response_schema.dump(user)
    return jsonify(result), 200

@admin_bp.route('/users/<int:user_id>/role', methods=['PATCH'])
@jwt_required()
@role_required('ADMIN')
def update_user_role(user_id):
    """
    Update a user's role.
    
    Request Body:
        {
            "role": "RESIDENT | SUPPORT_OFFICER | ADMIN",
            "department_id": int (required if changing to SUPPORT_OFFICER)
        }
    """
    current_user_id = int(get_jwt_identity())
    
    # Self-protection: cannot change your own role
    if user_id == current_user_id:
        return jsonify({'error': 'You cannot change your own role'}), 400
    
    # Fetch the user
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Validate request
    schema = UserRoleUpdateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    
    # Get the target role
    target_role = Role.query.filter_by(name=data['role']).first()
    if not target_role:
        return jsonify({'error': 'Invalid role'}), 400
    
    old_role_name = user.role.name if user.role else None
    
    # Handle department logic
    if data['role'] == 'SUPPORT_OFFICER':
        # Required: department_id must be provided and must exist
        dept_id = data.get('department_id')
        if not dept_id:
            return jsonify({'error': 'department_id is required for SUPPORT_OFFICER role'}), 400
        
        department = db.session.get(Department, dept_id)
        if not department:
            return jsonify({'error': 'Department not found'}), 400
        
        user.department_id = dept_id
    else:
        # RESIDENT or ADMIN: clear department_id
        user.department_id = None
    
    # Update the role
    old_role_id = user.role_id
    user.role_id = target_role.role_id
    
    db.session.commit()
    
    # Serialize and return
    response_schema = UserAdminResponseSchema()
    result = response_schema.dump(user)
    return jsonify({
        'message': f"User role changed from '{old_role_name}' to '{data['role']}'",
        'user': result
    }), 200


@admin_bp.route('/users/<int:user_id>/department', methods=['PATCH'])
@jwt_required()
@role_required('ADMIN')
def update_user_department(user_id):
    """
    Update a user's department (officers only).
    
    Request Body:
        {
            "department_id": int
        }
    """
    # Fetch the user
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Role guard: only SUPPORT_OFFICER can have a department
    if not user.role or user.role.name != 'SUPPORT_OFFICER':
        return jsonify({'error': 'Only support officers can have a department'}), 400
    
    # Validate request
    schema = UserDepartmentUpdateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    
    # Validate department exists
    department = db.session.get(Department, data['department_id'])
    if not department:
        return jsonify({'error': 'Department not found'}), 404
    
    old_dept_id = user.department_id
    old_dept_name = user.department.name if user.department else None
    
    # Update department
    user.department_id = data['department_id']
    db.session.commit()
    
    # Serialize and return
    response_schema = UserAdminResponseSchema()
    result = response_schema.dump(user)
    return jsonify({
        'message': f"Department changed from '{old_dept_name}' to '{department.name}'",
        'user': result
    }), 200


@admin_bp.route('/users/<int:user_id>/deactivate', methods=['PATCH'])
@jwt_required()
@role_required('ADMIN')
def deactivate_user(user_id):
    """
    Deactivate a user (soft delete).
    
    Request Body: (empty)
    """
    current_user_id = int(get_jwt_identity())
    
    # Self-protection: cannot deactivate yourself
    if user_id == current_user_id:
        return jsonify({'error': 'You cannot deactivate your own account'}), 400
    
    # Fetch the user
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already deactivated
    if not user.is_active:
        return jsonify({'error': 'User is already deactivated'}), 400
    
    # Deactivate
    user.is_active = False
    db.session.commit()
    
    # Serialize and return
    response_schema = UserAdminResponseSchema()
    result = response_schema.dump(user)
    return jsonify({
        'message': f"User '{user.email}' has been deactivated",
        'user': result
    }), 200
    
@admin_bp.route('/departments', methods=['GET'])
@jwt_required()
@role_required('ADMIN')
def list_departments():
    """List all departments for admin UI dropdown."""
    departments = Department.query.order_by(Department.name).all()
    return jsonify([{
        'department_id': d.department_id,
        'name': d.name
    } for d in departments]), 200