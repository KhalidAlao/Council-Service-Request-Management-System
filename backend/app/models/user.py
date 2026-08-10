"""
User model — single table for all users (Resident, Officer, Admin).
"""

from app.extensions import db


class User(db.Model):
    """System users — residents, officers, and admins."""
    
    __tablename__ = 'users'
    
    # Primary key
    user_id = db.Column(db.Integer, primary_key=True)
    
    # Basic info
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
   
    # All users have accounts with passwords (guests don't get user rows)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Foreign keys
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps — server-side default is more reliable than Python default
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    
    # Relationships — allows some_user.role and some_user.department
    role = db.relationship('Role', back_populates='users')
    department = db.relationship('Department', back_populates='users')
    
    def __repr__(self):
        # Defensively handles possible None role (even though role_id is required)
        role_name = self.role.name if self.role else "No Role"
        return f'<User {self.user_id}: {self.full_name} ({role_name})>'