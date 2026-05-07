import logging
import requests
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def my_scheduled_task():
    """
    Pings the server's own endpoint to keep it awake.
    For this to keep a cloud server (like Render or Heroku) awake, 
    set the APP_BASE_URL in your .env to your live URL.
    (e.g., APP_BASE_URL=https://my-eduwise.onrender.com)
    """
    app_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")
    ping_url = f"{app_url.rstrip('/')}/keep-alive"
    
    try:
        response = requests.get(ping_url, timeout=10)
        logger.info("Cron job pinged %s | Status: %s", ping_url, response.status_code)
    except Exception as e:
        logger.error("Cron job failed to ping %s | Error: %s", ping_url, e)
