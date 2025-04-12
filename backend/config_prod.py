import os


class ProdConfig:
    def __init__(self):
        self.basedir = os.path.abspath(os.path.dirname(__file__))
        self.DEBUG = os.getenv('FLASK_ENV') != 'production'
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret')
        self.SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False