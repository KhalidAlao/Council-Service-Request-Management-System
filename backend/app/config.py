"""
Configuration — environment-specific settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # ===== Database Configuration =====
    # Defensive fix: Render may provide postgres://, but SQLAlchemy requires postgresql://
    db_url = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ===== JWT Configuration =====
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    
    # Where to look for the JWT token
    JWT_TOKEN_LOCATION = ['headers']
    
    # Header configuration
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Token expiration times
    JWT_ACCESS_TOKEN_EXPIRES = 900          # 15 minutes (in seconds)
    JWT_REFRESH_TOKEN_EXPIRES = 604800      # 7 days (in seconds)
    
    # Required: The claim to use for identity
    JWT_IDENTITY_CLAIM = 'sub'              # Standard claim for user identity
    
    # Additional security settings
    JWT_ALGORITHM = 'HS256'
    JWT_DECODE_ALGORITHMS = ['HS256']
    

class TestConfig(Config):
    """Test configuration — in-memory database, no persistence."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Use a fixed secret for deterministic tokens in tests
    JWT_SECRET_KEY = 'test-jwt-secret-key-that-is-at-least-32-bytes-long'