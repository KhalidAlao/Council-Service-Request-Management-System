"""
Department schemas for serialisation.
"""

from marshmallow import Schema, fields


class DepartmentBasicSchema(Schema):
    """Basic department information for nested responses."""
    department_id = fields.Int()
    name = fields.Str()