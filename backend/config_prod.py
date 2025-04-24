import os


class ProdConfig:
    basedir = os.path.abspath(os.path.dirname(__file__))
    DEBUG = os.getenv('FLASK_ENV') != 'production'
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SERVER_NAME = os.getenv("SERVER_NAME", "localhost:5000")  # или твой проддомен
    PREFERRED_URL_SCHEME = "https"
    CLOUDINARY_FOLDER = "cn-auto/prod"
