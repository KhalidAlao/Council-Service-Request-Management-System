"""
Application factory — creates and configures the Flask app.
"""

from flask import Flask # type: ignore
from app.extensions import db, migrate, jwt
from app.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)  # This connects Flask-Migrate to your app and db
    jwt.init_app(app) 

    from app import models # registers all models with db.metadata
    
    # Register blueprints
    from app.routes.requests import requests_bp
    from app.routes.auth import auth_bp
    
    app.register_blueprint(requests_bp)
    app.register_blueprint(auth_bp)

    return app