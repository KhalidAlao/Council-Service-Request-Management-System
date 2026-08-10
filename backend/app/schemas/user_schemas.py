"""
User schemas for serialisation.
"""

from marshmallow import Schema, fields


class UserBasicSchema(Schema):
    """Basic user information for nested responses."""
    user_id = fields.Int()
    full_name = fields.Str()
    email = fields.Email()