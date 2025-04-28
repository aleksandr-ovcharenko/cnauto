import csv
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Add the parent directory to the path so we can import from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Brand, Country, db

CSV_FILE = os.path.join(os.path.dirname(__file__), "brands.csv")

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://cnauto:cnauto@localhost:5432/cnauto_db')
engine = create_engine(DATABASE_URL)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def seed_brands():
    session = Session()
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                country = session.query(Country).filter_by(name=row["country"]).first()
                if not country:
                    print(f"❌ Страна не найдена: {row['country']}")
                    continue

                brand = session.query(Brand).filter_by(slug=row["slug"]).first()
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
                    session.add(brand)
                    print(f"➕ Добавлен бренд: {brand.slug}")

            session.commit()
            print("✅ Бренды успешно добавлены/обновлены")
    except Exception as e:
        session.rollback()
        print(f"Error seeding brands: {str(e)}")
    finally:
        Session.remove()

if __name__ == "__main__":
    seed_brands()
