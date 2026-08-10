"""
Extensions — shared across the Flask app.
"""


from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager 

# Create the SQLAlchemy instance
db = SQLAlchemy()

# Create the Migrate instance 
migrate = Migrate()

jwt = JWTManager()