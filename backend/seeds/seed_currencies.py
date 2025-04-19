from backend.models import db, Currency

def seed_currencies():
    currencies = [
        {"code": "RUB", "name": "Russian Ruble", "symbol": "₽"},
        {"code": "USD", "name": "US Dollar", "symbol": "$"},
        {"code": "EUR", "name": "Euro", "symbol": "€"},
        {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥"},
        {"code": "KZT", "name": "Kazakhstani Tenge", "symbol": "₸"},
        {"code": "GBP", "name": "British Pound", "symbol": "£"},
    ]
    for cur in currencies:
        if not Currency.query.filter_by(code=cur["code"]).first():
            db.session.add(Currency(**cur))
    db.session.commit()
    print("✅ Валюты успешно добавлены.")
