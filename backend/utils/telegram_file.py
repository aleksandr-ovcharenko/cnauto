import os
import requests
import logging

# Настройка логгера
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Уровень можно изменить на DEBUG, WARNING и т.д.

def get_telegram_file_url(file_id, bot_token=None):
    if not bot_token:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN is not set")

    try:
        logger.info(f"🔄 Запрашиваем file_path для file_id: {file_id}")
        url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        result = response.json().get("result")
        if not result:
            raise ValueError("❌ Не удалось получить file_path: пустой result")

        file_path = result["file_path"]
        logger.info(f"📁 Получен file_path: {file_path}")

        full_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        logger.info(f"🔗 Сформирован полный URL: {full_url}")
        return full_url

    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ Ошибка при обращении к Telegram API: {e}")
        return None

    except Exception as ex:
        logger.error(f"❌ Ошибка: {ex}")
        return None
