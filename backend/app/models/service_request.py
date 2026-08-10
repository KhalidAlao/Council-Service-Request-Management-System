"""
ServiceRequest model — the core ticket for council service requests.
"""

from app.extensions import db


class ServiceRequest(db.Model):
    """Core service request ticket."""
    
    __tablename__ = 'service_requests'
    
    # Primary key
    request_id = db.Column(db.Integer, primary_key=True)
    
    
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.Text, nullable=False)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Enums (SQLAlchemy will create CHECK constraints in SQLite, native ENUM in PostgreSQL)
    category = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='SUBMITTED')
    
    # --- Foreign Keys ---
    
    # FK to User (who submitted this request)
    # NULL for guest submissions (guest_name/email/phone populated instead)
    submitted_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # FK to User (which officer is assigned to this request)
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    
    # FK to Department (which council team is responsible)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'), nullable=True)
    
    # Self-referencing FK (points to another request that this is a duplicate of)
    duplicate_of_request_id = db.Column(db.Integer, db.ForeignKey('service_requests.request_id'), nullable=True)
    
    # --- Guest Submission Fields ---
    # Populated ONLY when submitted_by_user_id IS NULL
    guest_name = db.Column(db.String(255), nullable=True)
    guest_email = db.Column(db.String(255), nullable=True)
    guest_phone = db.Column(db.String(20), nullable=True)
    
    # Timestamps
    date_submitted = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)
    
    # --- Relationships ---
    
    # foreign_keys argument required because there are TWO FKs to User
    submitter = db.relationship('User', foreign_keys=[submitted_by_user_id], back_populates='submitted_requests')
    assigned_officer = db.relationship('User', foreign_keys=[assigned_officer_id], back_populates='assigned_requests')
    
    # Department relationship
    department = db.relationship('Department', back_populates='requests')
    
    # Self-referential relationship for duplicates
    # remote_side tells SQLAlchemy which side is the "parent"
    duplicate_of = db.relationship('ServiceRequest', remote_side=[request_id], back_populates='duplicates')
    duplicates = db.relationship('ServiceRequest', back_populates='duplicate_of')
    
    # Relationships to notes and audit log
    notes = db.relationship('RequestNote', back_populates='request', cascade='all, delete-orphan')
    audit_entries = db.relationship('AuditLog', back_populates='request', cascade='all, delete-orphan')
    
    # --- Table-level constraints ---
    __table_args__ = (
        # Prevent a request from pointing to itself as a duplicate
        db.CheckConstraint('request_id != duplicate_of_request_id', name='check_not_self_duplicate'),
    )
    
    def __repr__(self):
        return f'<ServiceRequest {self.request_id}: {self.reference_number} ({self.status})>'