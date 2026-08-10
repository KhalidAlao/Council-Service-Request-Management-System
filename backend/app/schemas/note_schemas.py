"""
Note schemas for internal request notes.
"""

from marshmallow import Schema, fields, validates, ValidationError


class NoteCreateSchema(Schema):
    """Schema for creating a new internal note."""
    body = fields.Str(required=True)
    
    @validates('body')
    def validate_body(self, value, **kwargs):  
        """Validate that body is non-empty after stripping whitespace."""
        if not value or not value.strip():
            raise ValidationError("Note body cannot be empty or only whitespace")
        return value


class NoteResponseSchema(Schema):
    """Schema for serializing internal notes."""
    note_id = fields.Int()
    body = fields.Str()
    created_at = fields.DateTime()
    author = fields.Nested('UserBasicSchema', only=('user_id', 'full_name'), attribute='author')