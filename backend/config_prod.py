import os


class ProdConfig:
    basedir = os.path.abspath(os.path.dirname(__file__))
    DEBUG = os.getenv('FLASK_ENV') != 'production'
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
