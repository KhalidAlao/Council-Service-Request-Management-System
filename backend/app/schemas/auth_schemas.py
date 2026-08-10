"""
Authentication schemas for login and token refresh.
"""

from marshmallow import Schema, fields


class LoginSchema(Schema):
    """Schema for login request."""
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class TokenResponseSchema(Schema):
    """Schema for successful login/token refresh response."""
    access_token = fields.Str()
    refresh_token = fields.Str()
    token_type = fields.Str()
    expires_in = fields.Int()
    user = fields.Dict(keys=fields.Str(), values=fields.Raw())