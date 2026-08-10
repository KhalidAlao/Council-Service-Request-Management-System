"""
Internal note routes for service requests.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import ValidationError

from app.extensions import db
from app.models import ServiceRequest, RequestNote
from app.schemas.note_schemas import NoteCreateSchema, NoteResponseSchema
from app.utils.auth_decorators import role_required

notes_bp = Blueprint('notes', __name__, url_prefix='/api/v1/requests')


@notes_bp.route('/<int:request_id>/notes', methods=['POST'])
@jwt_required()
@role_required('SUPPORT_OFFICER', 'ADMIN')
def add_note(request_id):
    """
    Add an internal note to a service request.
    
    Permission rules:
        - Admin: Always allowed.
        - Support Officer: Allowed only if assigned to this request, or if
          the request is currently unassigned (assigned_officer_id is None).
        - Resident: Blocked by @role_required.
    """
    # 1. Fetch the request
    request_obj = ServiceRequest.query.get(request_id)
    if not request_obj:
        return jsonify({'error': 'Request not found'}), 404
    
    # 2. Get current user
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    user_role = claims.get('role')
    
    # 3. Permission check for Support Officers
    if user_role == 'SUPPORT_OFFICER':
        # If the request is assigned and the current officer is not the assignee
        if (request_obj.assigned_officer_id is not None and 
            request_obj.assigned_officer_id != current_user_id):
            return jsonify({
                'error': 'Only the assigned officer can add notes to this request'
            }), 403
        # If assigned_officer_id is None, any officer can add (triage phase)
    
    # 4. Parse and validate request body
    schema = NoteCreateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    
    # 5. Create the note (strip whitespace)
    note = RequestNote(
        request_id=request_obj.request_id,
        author_id=current_user_id,
        body=data['body'].strip()
    )
    
    db.session.add(note)
    db.session.commit()
    
    # 6. Serialize and return
    response_schema = NoteResponseSchema()
    result = response_schema.dump(note)
    return jsonify(result), 201


@notes_bp.route('/<int:request_id>/notes', methods=['GET'])
@jwt_required()
@role_required('SUPPORT_OFFICER', 'ADMIN')
def get_notes(request_id):
    """
    Get all internal notes for a service request.
    
    Permission rules:
        - Any Support Officer or Admin can view notes on any request
          (more permissive than POST for situational awareness).
        - Resident: Blocked by @role_required (returns 404 for consistency
          with other resident-facing security decisions).
    """
    # 1. Fetch the request
    request_obj = ServiceRequest.query.get(request_id)
    if not request_obj:
        return jsonify({'error': 'Request not found'}), 404
    
    # 2. Fetch notes (oldest first)
    notes = RequestNote.query.filter_by(request_id=request_id)\
        .order_by(RequestNote.created_at.asc()).all()
    
    # 3. Serialize and return
    response_schema = NoteResponseSchema(many=True)
    result = response_schema.dump(notes)
    return jsonify(result), 200