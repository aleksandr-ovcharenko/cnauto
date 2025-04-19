# This script updates the locale field for all currencies in the database.
# Run with: flask shell < backend/seeds/fix_currency_locales.py

from backend.models import db, Currency

# Mapping of currency codes to locales
CURRENCY_LOCALES = {
    'RUB': 'ru_RU',
    'USD': 'en_US',
    'EUR': 'fr_FR',
    'CNY': 'zh_CN',
    'KZT': 'kk_KZ',
    'BYN': 'be_BY',
    'UAH': 'uk_UA',
    # Add more as needed
}

for code, locale in CURRENCY_LOCALES.items():
    currency = Currency.query.filter_by(code=code).first()
    if currency:
        print(f"Updating {code}: {currency.locale} -> {locale}")
        currency.locale = locale
        db.session.add(currency)
    else:
        print(f"Currency {code} not found.")

db.session.commit()
print("✅ Currency locales updated!")
