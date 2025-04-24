import os
import requests
import logging
from flask import current_app

# Configure logger
logger = logging.getLogger(__name__)

def get_telegram_file_url(file_id, bot_token=None):
    # First try the passed token
    if not bot_token:
        # Try environment variable
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
    # Try config (in case it's set there)
    if not bot_token and current_app:
        bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN is not set in environment or app config!")
        logger.error(f"Failed to get URL for file_id: {file_id}")
        return None  # Return None instead of raising an exception
        
    try:
        logger.info(f"🔄 Requesting file_path for file_id: {file_id}")
        url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        result = response.json().get("result")
        if not result:
            logger.error(f"❌ Failed to get file_path for {file_id}: empty result")
            return None

        file_path = result["file_path"]
        logger.info(f"📁 Received file_path: {file_path}")

        full_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        logger.info(f"🔗 Created full URL: {full_url}")
        return full_url
    except Exception as e:
        logger.exception(f"❌ Error getting Telegram file URL for {file_id}: {str(e)}")
        return None
