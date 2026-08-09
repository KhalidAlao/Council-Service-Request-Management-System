"""
Role model — lookup table for user roles.

"""

from app.extensions import db


class Role(db.Model):
    """User roles: RESIDENT, SUPPORT_OFFICER, ADMIN."""
    
    __tablename__ = 'roles'
    
    # Primary key — auto-incrementing integer by default
    role_id = db.Column(db.Integer, primary_key=True)
    
    # Role name — must be unique and cannot be null
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<Role {self.role_id}: {self.name}>'