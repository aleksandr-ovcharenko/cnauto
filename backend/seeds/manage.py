import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask_migrate import upgrade
from backend.app import app
from backend.seeds.seed_users import seed_users
from backend.seeds.seed_currencies import seed_currencies
from backend.seeds.seed_countries import seed_countries
from backend.seeds.seed_categories import seed_categories
from backend.seeds.seed_brands import seed_brands
from backend.seeds.seed_brand_synonyms import seed_brand_synonyms
from backend.seeds.seed_data import seed_types

with app.app_context():
    upgrade()
    seed_users()
    seed_currencies()
    seed_countries()
    seed_categories()
    seed_brands()
    seed_brand_synonyms()
    seed_types()
    print("✅ Миграции и сиды успешно применены")
