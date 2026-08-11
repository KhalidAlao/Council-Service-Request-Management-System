"""
Application factory — creates and configures the Flask app.
"""

import os
from flask import Flask, send_from_directory, redirect
from app.extensions import db, migrate, jwt
from app.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Import models so Alembic can discover them
    from app import models  # registers all models with db.metadata

    # Register blueprints
    from app.routes.requests import requests_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.notes import notes_bp

    app.register_blueprint(requests_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notes_bp)

    # ---------- Serve frontend static files ----------
    # The frontend directory is a sibling of the backend directory.
    # __file__ is backend/app/__init__.py → go up three levels to the project root,
    # then join with 'frontend'.
    frontend_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'frontend'
    )
    # The public folder contains index.html and other static assets
    frontend_public = os.path.join(frontend_root, 'public')

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        # If the path starts with 'api/', it should be handled by blueprints;
        # this guard is mostly redundant but keeps things safe.
        if path.startswith('api/'):
            return redirect('/')

        # Try to serve a static file from the frontend root (e.g., /src/app.js)
        file_path = os.path.join(frontend_root, path)
        if path and os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(frontend_root, path)

        # Otherwise, serve the SPA entry point (index.html)
        return send_from_directory(frontend_public, 'index.html')

    return app