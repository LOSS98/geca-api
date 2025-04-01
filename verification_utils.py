import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from traceback import print_tb

from dotenv import load_dotenv
import datetime
import os
import sqlite3

load_dotenv()


def init_db():
    conn = sqlite3.connect("verification.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            code TEXT,
            attempts INTEGER DEFAULT 0,
            datetime TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def generate_code(email):
    if check_fisa(email):
        init_db()
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters).upper() for i in range(8))
        conn = sqlite3.connect("verification.db")
        cursor = conn.cursor()
        now = datetime.datetime.now()

        cursor.execute("DELETE FROM verification_table WHERE email = ?", (email,))
        cursor.execute("INSERT INTO verification_table (email, code, datetime) VALUES (?, ?, ?)",
                       (email, code, now.isoformat()))

        conn.commit()
        conn.close()
        return code
    return -1


def verify_code(email, code):
    if check_fisa(email):
        init_db()
        conn = sqlite3.connect("verification.db")
        cursor = conn.cursor()
        now = datetime.datetime.now()

        cursor.execute("SELECT code, attempts, datetime FROM verification_table WHERE email = ?", (email,))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            return -3  # Email n'existe pas

        db_code, attempts, db_datetime = row
        db_datetime = datetime.datetime.strptime(db_datetime, "%Y-%m-%dT%H:%M:%S.%f")

        if (now - db_datetime).total_seconds() > int(os.getenv("MAX_DURATION")):
            cursor.execute("DELETE FROM verification_table WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return -2  # Expired

        if attempts >= int(os.getenv("MAX_ATTEMPS")):
            cursor.execute("DELETE FROM verification_table WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return -1  # Lot of attemps

        if code == db_code:
            cursor.execute("DELETE FROM verification_table WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return 1  # Valid code
        else:
            cursor.execute("UPDATE verification_table SET attempts = attempts + 1 WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return 0  # Invalide code
    else:
        return -4


def load_html_template(variables, template_path="./email_template.html"):
    with open(template_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    for key, value in variables.items():
        html_content = html_content.replace(f"{{{{ {key} }}}}", value)
    return html_content


def send_code_email(to_email, subject, code):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASS")

    if not sender_email or not sender_password:
        raise ValueError(".env not complete")

    html_content = load_html_template({'code': code})

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL(os.getenv("EMAIL_SERVER"), int(os.getenv("EMAIL_PORT"))) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Email sent !")
    except Exception as e:
        print(f"Error while sending the email : {e}")


def check_fisa(email):
    if email[-7:] == "uphf.fr":
        return True
    return False