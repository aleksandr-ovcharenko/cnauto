# Break circular import dependency between app.py and admin.py
# by moving the shared functionality to __init__.py
import logging

logger = logging.getLogger(__name__)


def import_with_fallback(package_import, direct_import):
    """
    Helper function to import modules with fallback pattern.
    Enables consistent imports whether running as a module or directly.
    
    Args:
        package_import (str): The import path when running as a package (e.g., 'backend.utils.file_logger')
        direct_import (str): The import path when running directly (e.g., 'utils.file_logger')
        
    Returns:
        module: The imported module
        
    Example:
        get_module_logger = import_with_fallback('backend.utils.file_logger', 'utils.file_logger').get_module_logger
    """
    import importlib

    try:
        return importlib.import_module(package_import)
    except ImportError:
        return importlib.import_module(direct_import)


def format_currency_filter(price, currency_obj=None):
    """Format a price based on currency object or with defaults"""
    if not price:
        return "-"

    # Currency-specific locale mapping
    currency_locale_map = {
        'RUB': 'ru-RU',
        'USD': 'en-US',
        'EUR': 'de-DE',
        'GBP': 'en-GB',
        'CNY': 'zh-CN',
        'JPY': 'ja-JP'
    }

    if currency_obj:
        currency = currency_obj.code if currency_obj and currency_obj.code else 'RUB'
        # Use currency-specific locale if no explicit locale is set
        if currency_obj and hasattr(currency_obj, 'locale') and currency_obj.locale:
            locale = currency_obj.locale.replace('_', '-')
        else:
            # Try to get locale from the currency code
            locale = currency_locale_map.get(currency, 'ru-RU')
        symbol = currency_obj.symbol if currency_obj and hasattr(currency_obj,
                                                                 'symbol') and currency_obj.symbol else '₽'
    else:
        # Default to Russian locale and currency
        locale = 'ru-RU'
        currency = 'RUB'
        symbol = '₽'

    # Special case for Russian Rubles
    if currency == 'RUB':
        # Format with space as thousands separator and no decimal places
        try:
            # Try to convert to integer first to remove decimal part for whole numbers
            clean_price = float(price)
            formatted_price = f"{int(clean_price):,}".replace(',', ' ')
            return f"{formatted_price} {symbol}"
        except Exception as e:
            logger.error(f"Error formatting RUB price: {e}")
            # Fallback if any error occurs
            return f"{price} {symbol}"

    # Format with Babel for other currencies
    try:
        from babel.numbers import format_currency
        return format_currency(price, currency, locale=locale)
    except Exception as e:
        # Fallback to simpler formatting
        try:
            import locale as loc
            loc.setlocale(loc.LC_ALL, locale.replace('-', '_'))
            return loc.currency(price, symbol=symbol, grouping=True)
        except:
            # Last resort
            return f"{price:,.2f} {symbol}"
