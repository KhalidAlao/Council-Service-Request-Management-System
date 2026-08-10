"""
AuditLog model — immutable history of all changes to service requests.
"""

from app.extensions import db


class AuditLog(db.Model):
    """Audit trail for all service request changes."""
    
    __tablename__ = 'audit_log'
    
    log_id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    request_id = db.Column(db.Integer, db.ForeignKey('service_requests.request_id'), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    
    # What changed
    field_changed = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    
    # Timestamp
    changed_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    
    # Relationships
    request = db.relationship('ServiceRequest', back_populates='audit_entries')
    changed_by = db.relationship('User', back_populates='audit_entries')
    
    def __repr__(self):
        return f'<AuditLog {self.log_id}: Request {self.request_id} - {self.field_changed}>'