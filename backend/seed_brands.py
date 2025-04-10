import csv
import os

from backend.app import app
from backend.models import db, Brand, Country

CSV_FILE = os.path.join(os.path.dirname(__file__), "brands.csv")

def seed_brands():
    with app.app_context():
        with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                country = Country.query.filter_by(name=row["country"]).first()
                if not country:
                    print(f"❌ Страна не найдена: {row['country']}")
                    continue

                brand = Brand.query.filter_by(slug=row["slug"]).first()
                if brand:
                    # Обновим существующий бренд
                    brand.name = row["name"]
                    brand.logo = row["logo"]
                    brand.country = country
                    print(f"🔄 Обновлён бренд: {brand.slug}")
                else:
                    # Создаём новый
                    brand = Brand(
                        name=row["name"],
                        slug=row["slug"],
                        logo=row["logo"],
                        country=country
                    )
                    db.session.add(brand)
                    print(f"➕ Добавлен бренд: {brand.slug}")

        db.session.commit()
        print("✅ Бренды успешно добавлены/обновлены")

if __name__ == "__main__":
    seed_brands()
