"""
Service request routes: submission, tracking, listing, status changes, assignment.
"""

from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

from app.extensions import db
from app.models import ServiceRequest, Department
from app.schemas.request_schemas import (
    RequestSubmitSchema,
    RequestResponseSchema
    
)
from app.utils.reference_generator import generate_reference_number
from app.constants import CATEGORY_TO_DEPARTMENT
from app.utils.auth_decorators import role_required

from app.utils.status_helpers import (
    ROLE_ALLOWED_STATUSES,
    validate_transition,
    log_change,
    get_request_or_404
)

requests_bp = Blueprint('requests', __name__, url_prefix='/api/v1')


def create_request_with_reference(data, user_id=None):
    """Create a request with retry logic for unique reference number."""
    max_attempts = 3
    
    for attempt in range(max_attempts):
        reference_number = generate_reference_number()
        
        try:
            dept_name = CATEGORY_TO_DEPARTMENT.get(data['category'])
            department_id = None
            if dept_name:
                department = Department.query.filter_by(name=dept_name).first()
                if department:
                    department_id = department.department_id
            
            request_obj = ServiceRequest(
                reference_number=reference_number,
                title=data['title'],
                description=data['description'],
                location=data['location'],
                category=data['category'],
                priority='MEDIUM',
                status='SUBMITTED',
                submitted_by_user_id=user_id,
                guest_name=data.get('guest_name') if not user_id else None,
                guest_email=data.get('guest_email') if not user_id else None,
                guest_phone=data.get('guest_phone') if not user_id else None,
                department_id=department_id,
            )
            
            db.session.add(request_obj)
            db.session.commit()
            return request_obj
            
        except IntegrityError as e:
            db.session.rollback()
            if attempt == max_attempts - 1:
                raise RuntimeError("Failed to generate unique reference number after 3 attempts") from e
            continue


@requests_bp.route('/requests', methods=['POST'])
@jwt_required(optional=True)
def submit_request():
    """Submit a new service request."""
    current_user_id = get_jwt_identity()
    if current_user_id is not None:
        try:
            current_user_id = int(current_user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user identity'}), 400
    
    schema = RequestSubmitSchema()
    schema.context = {'user_id': current_user_id}
    
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    
    try:
        request_obj = create_request_with_reference(data, current_user_id)
        response_schema = RequestResponseSchema()
        result = response_schema.dump(request_obj)
        return jsonify(result), 201
        
    except RuntimeError as e:
        return jsonify({'error': 'Failed to create request', 'message': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An unexpected error occurred'}), 500


@requests_bp.route('/requests', methods=['GET'])
@jwt_required()  
@role_required('RESIDENT', 'SUPPORT_OFFICER', 'ADMIN')
def list_requests():
    """
    List service requests with filtering, pagination, and role-based scoping.
    
    Residents: see only their own requests.
    Officers/Admins: see all requests.
    
    Query Parameters:
        status: SUBMITTED, UNDER_REVIEW, IN_PROGRESS, RESOLVED, CLOSED
        priority: LOW, MEDIUM, HIGH, URGENT
        category: ROADS, WASTE, PARKS, STREET_LIGHTING, BUILDINGS, OTHER
        department_id: int
        assigned_officer_id: int
        date_from: ISO date (YYYY-MM-DD)
        date_to: ISO date (YYYY-MM-DD)
        page: int (default 1)
        limit: int (default 20, max 100)
    """
    # Get current user info
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    user_role = claims.get('role')
    
    # Start with base query
    query = ServiceRequest.query
    
    # --- Role-based scoping ---
    # Residents only see their own requests
    if user_role == 'RESIDENT':
        query = query.filter_by(submitted_by_user_id=current_user_id)
    
    # --- Dynamic filters ---
    # Status filter
    if status := request.args.get('status'):
        query = query.filter_by(status=status)
    
    # Priority filter
    if priority := request.args.get('priority'):
        query = query.filter_by(priority=priority)
    
    # Category filter
    if category := request.args.get('category'):
        query = query.filter_by(category=category)
    
    # Department ID filter
    if department_id := request.args.get('department_id', type=int):
        query = query.filter_by(department_id=department_id)
    
    # Assigned officer ID filter
    if assigned_officer_id := request.args.get('assigned_officer_id', type=int):
        query = query.filter_by(assigned_officer_id=assigned_officer_id)
    
    # Date from filter (parse ISO date)
    if date_from := request.args.get('date_from'):
        try:
            # Parse ISO date (YYYY-MM-DD)
            date_from_parsed = datetime.fromisoformat(date_from)
            query = query.filter(ServiceRequest.date_submitted >= date_from_parsed)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
    
    # Date to filter (parse ISO date)
    if date_to := request.args.get('date_to'):
        try:
            date_to_parsed = datetime.fromisoformat(date_to)
            query = query.filter(ServiceRequest.date_submitted <= date_to_parsed)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
    
    # Sort by most recent first (default)
    query = query.order_by(desc(ServiceRequest.date_submitted))
    
    # --- Pagination ---
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 20, type=int)
    
    # Clamp per_page to max 100
    per_page = min(per_page, 100)
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # --- Serialize response ---
    response_schema = RequestResponseSchema(many=True)
    
    return jsonify({
        'data': response_schema.dump(paginated.items),
        'pagination': {
            'page': paginated.page,
            'limit': paginated.per_page,
            'total_items': paginated.total,
            'total_pages': paginated.pages
        }
    }), 200


@requests_bp.route('/requests/<int:request_id>', methods=['GET'])
@jwt_required()  
@role_required('RESIDENT', 'SUPPORT_OFFICER', 'ADMIN')
def get_request(request_id):
    """
    Get a single service request by ID.
    
    Residents: only see their own requests (404 if not theirs).
    Officers/Admins: see any request.
    """
    # Get current user info
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    user_role = claims.get('role')
    
    # Fetch the request
    request_obj = ServiceRequest.query.get(request_id)
    
    # Return 404 if request doesn't exist
    if not request_obj:
        return jsonify({'error': 'Request not found'}), 404
    
    # Role-based ownership check
    # Residents can only see their own requests
    if user_role == 'RESIDENT':
        if request_obj.submitted_by_user_id != current_user_id:
            return jsonify({'error': 'Request not found'}), 404
    
    # Serialize and return
    response_schema = RequestResponseSchema()
    result = response_schema.dump(request_obj)
    return jsonify(result), 200

@requests_bp.route('/requests/<int:request_id>/status', methods=['PATCH'])
@jwt_required()
@role_required('SUPPORT_OFFICER', 'ADMIN')
def change_request_status(request_id):
    """
    Change the status of a service request.
    
    Permission rules:
        - Officer: can set UNDER_REVIEW, IN_PROGRESS, DUPLICATE, REJECTED
        - Admin: can set RESOLVED, CLOSED
    
    Validation:
        - Status transition must follow the state machine
        - DUPLICATE requires duplicate_of_request_id (must exist, not self)
        - REJECTED requires rejection_reason (non-empty string)
    
    Request Body:
        {
            "status": "UNDER_REVIEW" | "IN_PROGRESS" | "RESOLVED" | "CLOSED" | "DUPLICATE" | "REJECTED",
            "duplicate_of_request_id": int,     # Required for DUPLICATE
            "rejection_reason": string          # Required for REJECTED
        }
    """
    # 1. Fetch the request
    request_obj, error_response, status_code = get_request_or_404(request_id)
    if error_response:
        return error_response, status_code
    
    # Get current user
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    user_role = claims.get('role')
    
    # Parse request body
    data = request.get_json() or {}
    target_status = data.get('status')
    
    # 2. Validate status is provided
    if not target_status:
        return jsonify({'error': 'Status is required'}), 400
    
    # 3. Role permission check
    allowed_statuses = ROLE_ALLOWED_STATUSES.get(user_role, set())
    if target_status not in allowed_statuses:
        return jsonify({
            'error': f"You are not allowed to set status to '{target_status}'"
        }), 403
    
    # 4. State machine validation
    current_status = request_obj.status
    is_valid, error_msg = validate_transition(current_status, target_status)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 5. Conditional required fields
    if target_status == 'DUPLICATE':
        duplicate_of = data.get('duplicate_of_request_id')
        
        if not duplicate_of:
            return jsonify({
                'error': 'duplicate_of_request_id is required for DUPLICATE status'
            }), 400
        
        # Validate duplicate_of exists
        duplicate_request = ServiceRequest.query.get(duplicate_of)
        if not duplicate_request:
            return jsonify({'error': 'duplicate_of_request_id must reference a valid request'}), 400
        
        # Validate not self-referential
        if duplicate_of == request_id:
            return jsonify({'error': 'A request cannot be a duplicate of itself'}), 400
    
    if target_status == 'REJECTED':
        rejection_reason = data.get('rejection_reason')
        
        if not rejection_reason or not rejection_reason.strip():
            return jsonify({
                'error': 'rejection_reason is required for REJECTED status'
            }), 400
    
    # 6. Perform the status change
    old_status = request_obj.status
    request_obj.status = target_status
    
    # Handle DUPLICATE specific fields
    if target_status == 'DUPLICATE':
        request_obj.duplicate_of_request_id = data['duplicate_of_request_id']
    else:
        # Clear duplicate_of if not DUPLICATE (cleanup)
        request_obj.duplicate_of_request_id = None
    
    # 7. Audit log
    log_change(
        request_id=request_obj.request_id,
        changed_by_user_id=current_user_id,
        field_name='status',
        old_value=old_status,
        new_value=target_status
    )
    
    # 8. Commit and return
    db.session.commit()
    
    # Serialize and return
    response_schema = RequestResponseSchema()
    result = response_schema.dump(request_obj)
    return jsonify(result), 200

@requests_bp.route('/requests/<int:request_id>/assign', methods=['PATCH'])
@jwt_required()
@role_required('SUPPORT_OFFICER', 'ADMIN')
def assign_officer(request_id):
    """
    Assign an officer to a service request.
    
    Permission rules:
        - Admin: Can assign any request to any officer
        - Officer: Can self-assign if unassigned
        - Officer: Can hand off if currently assigned to them
    
    Request Body:
        {
            "assigned_officer_id": int
        }
    """
    from app.utils.status_helpers import validate_target_officer, can_assign_officer, log_change
    
    # 1. Fetch the request
    request_obj = ServiceRequest.query.get(request_id)
    if not request_obj:
        return jsonify({'error': 'Request not found'}), 404
    
    # Get current user
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    current_user_role = claims.get('role')
    
    # 2. Parse request body
    data = request.get_json() or {}
    target_officer_id = data.get('assigned_officer_id')
    
    if not target_officer_id:
        return jsonify({'error': 'assigned_officer_id is required'}), 400
    
    # 3. Validate target officer exists, is active, and has SUPPORT_OFFICER role
    target_user, error_response, status_code = validate_target_officer(target_officer_id)
    if error_response:
        return error_response, status_code
    
    # 4. Check if current user can assign
    can_assign, error_msg = can_assign_officer(
        current_user_id,
        current_user_role,
        request_obj,
        target_officer_id
    )
    if not can_assign:
        return jsonify({'error': error_msg}), 403
    
    # 5. Perform the assignment
    old_assigned_officer_id = request_obj.assigned_officer_id
    request_obj.assigned_officer_id = target_officer_id
    
    # 6. Audit log
    log_change(
        request_id=request_obj.request_id,
        changed_by_user_id=current_user_id,
        field_name='assigned_officer_id',
        old_value=old_assigned_officer_id,
        new_value=target_officer_id
    )
    
    # 7. Commit and return
    db.session.commit()
    
    # Serialize and return
    response_schema = RequestResponseSchema()
    result = response_schema.dump(request_obj)
    return jsonify(result), 200