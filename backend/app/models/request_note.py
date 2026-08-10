"""
RequestNote model — internal notes for collaboration between officers and admins.
"""

from app.extensions import db


class RequestNote(db.Model):
    """Internal notes attached to a service request."""
    
    __tablename__ = 'request_notes'
    
    note_id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    request_id = db.Column(db.Integer, db.ForeignKey('service_requests.request_id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    
    # Content
    body = db.Column(db.Text, nullable=False)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    
    # Relationships
    request = db.relationship('ServiceRequest', back_populates='notes')
    author = db.relationship('User', back_populates='notes')
    
    def __repr__(self):
        return f'<RequestNote {self.note_id}: Request {self.request_id} by User {self.author_id}>'