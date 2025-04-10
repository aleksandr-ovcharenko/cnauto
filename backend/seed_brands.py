import csv
from backend.models import Brand
from backend.app import app
from backend.models import db
import os

file_path = os.path.join(os.path.dirname(__file__), 'brands.csv')

with app.app_context():
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            brand = Brand.query.filter_by(slug=row['slug']).first()
            if brand:
                brand.category = row['category']
        db.session.commit()