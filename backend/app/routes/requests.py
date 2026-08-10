from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import ServiceRequest, Department
from app.schemas.request_schemas import RequestSubmitSchema, RequestResponseSchema
from app.utils.reference_generator import generate_reference_number
from app.constants import CATEGORY_TO_DEPARTMENT


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