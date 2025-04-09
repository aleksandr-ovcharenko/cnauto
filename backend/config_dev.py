import os


class DevConfig:
    basedir = os.path.abspath(os.path.dirname(__file__))
    DEBUG = True
    SECRET_KEY = 'dev-secret-key'  # В разработке можно захардкодить
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'cars.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
