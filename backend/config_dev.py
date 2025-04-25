import os


class DevConfig:
    basedir = os.path.abspath(os.path.dirname(__file__))
    DEBUG = True
    SECRET_KEY = 'dev-secret-key'  # В разработке можно захардкодить
    SQLALCHEMY_DATABASE_URI = 'postgresql://cnauto:cnauto@localhost:5432/cnauto_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SERVER_NAME = "localhost:5000"
    CLOUDINARY_FOLDER = "cn-auto/dev"
