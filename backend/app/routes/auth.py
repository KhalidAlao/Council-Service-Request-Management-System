"""
Authentication routes: login, refresh token.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from marshmallow import ValidationError
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import User
from app.schemas.auth_schemas import LoginSchema, TokenResponseSchema

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    schema = LoginSchema()
    
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 401
    
    
    additional_claims = {
        'role': user.role.name if user.role else 'RESIDENT'
    }
    
    access_token = create_access_token(
        identity=str(user.user_id),
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=str(user.user_id),
        additional_claims=additional_claims
    )
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 900,
        'user': {
            'user_id': user.user_id,
            'full_name': user.full_name,
            'email': user.email,
            'role': user.role.name if user.role else None
        }
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'RESIDENT')
    
    access_token = create_access_token(
        identity=current_user_id,
        additional_claims={'role': role}
    )
    
    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 900
    }), 200