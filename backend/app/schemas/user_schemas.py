"""
User schemas for basic serialization, creation, and admin responses.
"""

from marshmallow import Schema, fields, validates_schema, ValidationError
from marshmallow.validate import OneOf, Length

from app.constants import ROLE_NAMES


# ===== Basic Schema (for nested relationships) =====

class UserBasicSchema(Schema):
    """Basic user information for nested responses (e.g., in request details)."""
    user_id = fields.Int()
    full_name = fields.Str()
    email = fields.Email()


# ===== Admin Schemas =====

# Only staff roles can be created via admin endpoint
VALID_CREATE_ROLES = ['SUPPORT_OFFICER', 'ADMIN']


class UserCreateSchema(Schema):
    """Schema for creating a new staff user (admin-only)."""
    
    full_name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone = fields.Str(required=False, allow_none=True)
    password = fields.Str(
        required=True,
        validate=Length(min=8, error="Password must be at least 8 characters long")
    )
    role = fields.Str(
        required=True,
        validate=OneOf(VALID_CREATE_ROLES, error="Role must be SUPPORT_OFFICER or ADMIN")
    )
    department_id = fields.Int(required=False, allow_none=True)
    
    @validates_schema
    def validate_role_department(self, data, **kwargs):
        """Enforce department_id requirements based on role."""
        role = data.get('role')
        department_id = data.get('department_id')
        
        if role == 'SUPPORT_OFFICER' and not department_id:
            raise ValidationError(
                "department_id is required for SUPPORT_OFFICER role",
                field_name='department_id'
            )
        
        if role == 'ADMIN' and department_id:
            raise ValidationError(
                "department_id must not be provided for ADMIN role",
                field_name='department_id'
            )


class UserRoleUpdateSchema(Schema):
    """Schema for updating a user's role."""
    
    role = fields.Str(
        required=True,
        validate=OneOf(ROLE_NAMES, error="Invalid role")
    )
    department_id = fields.Int(required=False, allow_none=True)
    
    @validates_schema
    def validate_role_department(self, data, **kwargs):
        """Enforce department_id requirements when moving to SUPPORT_OFFICER."""
        role = data.get('role')
        department_id = data.get('department_id')
        
        if role == 'SUPPORT_OFFICER' and not department_id:
            raise ValidationError(
                "department_id is required when setting role to SUPPORT_OFFICER",
                field_name='department_id'
            )


class UserDepartmentUpdateSchema(Schema):
    """Schema for updating a user's department (officers only)."""
    
    department_id = fields.Int(
        required=True,
        error_messages={"required": "department_id is required"}
    )


class UserAdminResponseSchema(Schema):
    """Schema for admin user listing and detail responses."""
    
    user_id = fields.Int()
    full_name = fields.Str()
    email = fields.Email()
    role = fields.Str(attribute='role.name')
    department_id = fields.Int(allow_none=True)
    department_name = fields.Str(attribute='department.name', allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime()