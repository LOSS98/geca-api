import os
import sqlite3
import requests
import logging
import threading
import time
from urllib.parse import quote
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEXTMEBOT_API_KEY = os.getenv("TEXTMEBOT_API_KEY")
TEXTMEBOT_API_URL =os.getenv("TEXTMEBOT_API_URL")
if not TEXTMEBOT_API_KEY:
    logger.warning("TEXTMEBOT_API_KEY is not defined in the .env file")

def init_sms_db():
    conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"\\verification.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sms_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("SMS database initialized")

def queue_sms(recipient, message):
    try:

        init_sms_db()

        conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"\\verification.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO sms_queue (recipient, message) VALUES (?, ?)",
            (recipient, message)
        )

        sms_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"SMS added to queue: ID {sms_id}")
        return sms_id

    except Exception as e:
        logger.error(f"Error adding SMS to queue: {e}")
        return None

def send_sms(recipient, message):
    if not TEXTMEBOT_API_KEY:
        logger.error("TEXTMEBOT_API_KEY not defined, cannot send SMS")
        return False, "TextMeBot API key not configured"

    try:

        api_url = TEXTMEBOT_API_URL

        encoded_message = quote(message)
        url = f"{api_url}?recipient={recipient}&apikey={TEXTMEBOT_API_KEY}&text={encoded_message}"

        response = requests.get(url)

        if response.status_code == 200:
            logger.info(f"SMS sent successfully to {recipient}")
            return True, "SMS sent successfully"
        else:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return False, error_msg

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending SMS: {error_msg}")
        return False, error_msg

def process_sms_queue():
    try:
        conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"\\verification.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, recipient, message FROM sms_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
        )
        row = cursor.fetchone()

        if row:
            sms_id, recipient, message = row

            cursor.execute(
                "UPDATE sms_queue SET status = 'processing' WHERE id = ?",
                (sms_id,)
            )
            conn.commit()

            conn.close()

            success, result_message = send_sms(recipient, message)

            conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"\\verification.db")
            cursor = conn.cursor()

            if success:
                cursor.execute(
                    "UPDATE sms_queue SET status = 'sent', processed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), sms_id)
                )
            else:
                cursor.execute(
                    "UPDATE sms_queue SET status = 'failed', processed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), sms_id)
                )

            conn.commit()

        conn.close()

    except Exception as e:
        logger.error(f"Error processing SMS queue: {e}")
        try:
            conn.close()
        except:
            pass

def sms_worker():
    logger.info("Starting SMS sender thread")

    while True:
        try:
            process_sms_queue()

            time.sleep(7)
        except Exception as e:
            logger.error(f"Error in SMS thread: {e}")
            time.sleep(7)

def start_sms_worker():
    sms_thread = threading.Thread(target=sms_worker, daemon=True)
    sms_thread.start()
    logger.info("SMS sender thread started")

if __name__ == "__main__":
    init_sms_db()
    start_sms_worker()
    logger.info("SMS service started")