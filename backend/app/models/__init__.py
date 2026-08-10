"""
Models package — import all models here so Alembic can discover them.
"""

from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.service_request import ServiceRequest
from app.models.request_note import RequestNote
from app.models.audit_log import AuditLog