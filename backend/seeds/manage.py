from flask_migrate import upgrade

from app import app
from seeds.seed_users import seed_users

with app.app_context():
    upgrade()
    seed_users()
    print("✅ Миграции и сиды успешно применены")
