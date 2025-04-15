import os
import sqlite3
import smtplib
import logging
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_email_db():
    conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"\\verification.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            to_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Email database initialized")

def queue_email(to_email, subject, body):
    try:

        init_email_db()

        conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"\\verification.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO email_queue (to_email, subject, body) VALUES (?, ?, ?)",
            (to_email, subject, body)
        )

        email_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Email added to queue: ID {email_id}")
        return email_id

    except Exception as e:
        logger.error(f"Error adding email to queue: {e}")
        return None

def send_email_direct(to_email, subject, body):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASS")
    smtp_server = os.getenv("EMAIL_SERVER")
    smtp_port = int(os.getenv("EMAIL_PORT", "465"))

    if not all([sender_email, sender_password, smtp_server]):
        logger.error("Incomplete email configuration in .env")
        return False, "Incomplete email configuration"

    try:

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}")
        return True, None

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending email: {error_msg}")
        return False, error_msg

def load_html_template(template_variables, template_path="./email_template.html"):
    try:
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        template = Template(template_content)

        rendered_html = template.render(**template_variables)

        return rendered_html
    except FileNotFoundError:

        html = """
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
                <h2>Message</h2>
                <p>{{ body }}</p>
                {% if code %}
                <p><strong>Verification Code: {{ code }}</strong></p>
                {% endif %}
            </div>
        </body>
        </html>
        """
        template = Template(html)
        return template.render(**template_variables)

def process_email_queue():
    try:
        conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"\\verification.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, to_email, subject, body FROM email_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
        )
        row = cursor.fetchone()

        if row:
            email_id, to_email, subject, body = row

            cursor.execute(
                "UPDATE email_queue SET status = 'processing' WHERE id = ?",
                (email_id,)
            )
            conn.commit()

            conn.close()

            success, error = send_email_direct(to_email, subject, body)

            conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+"\\verification.db")
            cursor = conn.cursor()

            if success:
                cursor.execute(
                    "UPDATE email_queue SET status = 'sent', processed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), email_id)
                )
            else:
                cursor.execute(
                    "UPDATE email_queue SET status = 'failed', processed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), email_id)
                )

            conn.commit()

        conn.close()

    except Exception as e:
        logger.error(f"Error processing email queue: {e}")
        try:
            conn.close()
        except:
            pass

def email_worker():
    logger.info("Starting email sender thread")

    while True:
        try:
            process_email_queue()

            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in email thread: {e}")
            time.sleep(1)

def start_email_worker():
    email_thread = threading.Thread(target=email_worker, daemon=True)
    email_thread.start()
    logger.info("Email sender thread started")

if __name__ == "__main__":
    init_email_db()
    start_email_worker()
    logger.info("Email service started")