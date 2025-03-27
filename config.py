import os


class Config:
    # Get SECRET_KEY from environment variable or use a default (for development only)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'

    # Warning will be shown if this default key is used in production
    if os.environ.get('FLASK_ENV') == 'production' and SECRET_KEY == 'your-secret-key':
        print("WARNING: Using default SECRET_KEY in production is insecure!")

    SQLALCHEMY_DATABASE_URI = 'sqlite:///recipes.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'protected_uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB limit
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    DEFAULT_IMAGE = 'static/images/default.jpg'
