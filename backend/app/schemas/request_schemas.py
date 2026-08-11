"""
Request schemas for validation and serialisation.
"""

from marshmallow import Schema, fields, validates_schema, ValidationError
from marshmallow.validate import OneOf
from marshmallow import RAISE

from app.constants import VALID_CATEGORIES

from app.schemas.user_schemas import UserBasicSchema  # noqa: F401
from app.schemas.department_schemas import DepartmentBasicSchema  # noqa: F401


class RequestSubmitSchema(Schema):
    """Schema for submitting a new service request."""
    
    class Meta:
        unknown = RAISE
    
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    location = fields.Str(required=True)
    category = fields.Str(
        required=True,
        validate=OneOf(VALID_CATEGORIES, error="Invalid category")
    )
    
    guest_name = fields.Str(required=False)
    guest_email = fields.Email(required=False)
    guest_phone = fields.Str(required=False)
    
    @validates_schema
    def validate_guest_fields(self, data, **kwargs):
        user_id = self.context.get('user_id')
        
        if user_id:
            if any([data.get('guest_name'), data.get('guest_email'), data.get('guest_phone')]):
                raise ValidationError(
                    "Guest fields are not allowed for authenticated users"
                )
        else:
            if not all([data.get('guest_name'), data.get('guest_email'), data.get('guest_phone')]):
                raise ValidationError(
                    "Guest name, email, and phone are required for unauthenticated submissions"
                )


class RequestResponseSchema(Schema):
    """Schema for serializing a service request in API responses."""
    
    request_id = fields.Int()
    reference_number = fields.Str()
    title = fields.Str()
    description = fields.Str()
    location = fields.Str()
    category = fields.Str()
    priority = fields.Str()
    status = fields.Str()
    date_submitted = fields.DateTime()
    last_updated = fields.DateTime()
    duplicate_of_request_id = fields.Int(allow_none=True) 
    rejection_reason = fields.Str(allow_none=True)
    
    
    submitted_by = fields.Nested(
        'UserBasicSchema',
        only=('user_id', 'full_name', 'email'),
        allow_none=True,
        attribute='submitter'  
    )
    
    
    assigned_officer = fields.Nested(
        'UserBasicSchema',
        only=('user_id', 'full_name'),
        allow_none=True
    )
    
    department = fields.Nested(
        'DepartmentBasicSchema',
        only=('department_id', 'name'),
        allow_none=True
    )
    
class RequestTrackSchema(Schema):
    """Schema for public tracking response (no PII)."""
    reference_number = fields.Str()
    status = fields.Str()
    title = fields.Str()
    location = fields.Str()
    category = fields.Str()
    date_submitted = fields.DateTime()
    last_updated = fields.DateTime()


class AuditLogEntrySchema(Schema):
    """Schema for audit log entries."""
    field_changed = fields.Str()
    old_value = fields.Str(allow_none=True)
    new_value = fields.Str(allow_none=True)
    changed_at = fields.DateTime()
    changed_by = fields.Nested('UserBasicSchema', only=('user_id', 'full_name'))