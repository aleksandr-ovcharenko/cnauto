import os
import requests

def get_telegram_file_url(file_id, bot_token=None):
    if not bot_token:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")

    print(f"🔄 Запрашиваем file_path для file_id: {file_id}")
    response = requests.get(f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}")
    response.raise_for_status()
    file_path = response.json()["result"]["file_path"]
    print(f"📁 Получен file_path: {file_path}")

    full_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    print(f"🔗 Сформирован полный URL: {full_url}")
    return full_url