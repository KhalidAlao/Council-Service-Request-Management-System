"""
Extensions — shared across the Flask app.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Create the SQLAlchemy instance
db = SQLAlchemy()

# Create the Migrate instance 
migrate = Migrate()