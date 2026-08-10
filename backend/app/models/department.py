"""
Department model — lookup table for council departments.
"""

from app.extensions import db


class Department(db.Model):
    """Council departments: Roads, Parks, Waste, etc."""
    
    __tablename__ = 'departments'
    
    department_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(255), nullable=True)
    head_of_department = db.Column(db.String(255), nullable=True)
    
   
    users = db.relationship('User', back_populates='department', lazy='dynamic')
    
    def __repr__(self):
        return f'<Department {self.department_id}: {self.name}>'