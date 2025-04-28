import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Add the parent directory to the path so we can import from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Country

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://cnauto:cnauto@localhost:5432/cnauto_db')
engine = create_engine(DATABASE_URL)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def seed_countries():
    """Seed countries in the database."""
    session = Session()
    try:
        countries = [
            "Китай",
            "Германия",
            "Япония",
            "Корея",
            "США",
            "Франция",
            "Швеция",
            "Чехия",
            "Англия",
            "Италия"
        ]

        for name in countries:
            if not session.query(Country).filter_by(name=name).first():
                session.add(Country(name=name))
                print(f"➕ Добавлена страна: {name}")
            else:
                print(f"🔄 Страна уже существует: {name}")
                
        session.commit()
        print("✅ Страны успешно добавлены")
    except Exception as e:
        session.rollback()
        print(f"Error seeding countries: {str(e)}")
    finally:
        Session.remove()

if __name__ == "__main__":
    seed_countries()
