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

def list_countries():
    session = Session()
    try:
        countries = session.query(Country).all()
        print("Available countries in the database:")
        for country in countries:
            print(f"ID: {country.id}, Name: {country.name}")
    except Exception as e:
        print(f"Error listing countries: {str(e)}")
    finally:
        Session.remove()

if __name__ == "__main__":
    list_countries()
