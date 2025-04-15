import random
import string
import datetime
import os
import sqlite3
from dotenv import load_dotenv

from email_utils import queue_email, load_html_template

load_dotenv()

def init_db():
    conn = sqlite3.connect("/app/verification.db")
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
        conn = sqlite3.connect("/app/verification.db")
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
        conn = sqlite3.connect("/app/verification.db")
        cursor = conn.cursor()
        now = datetime.datetime.now()

        cursor.execute("SELECT code, attempts, datetime FROM verification_table WHERE email = ?", (email,))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            return -3

        db_code, attempts, db_datetime = row
        db_datetime = datetime.datetime.strptime(db_datetime, "%Y-%m-%dT%H:%M:%S.%f")

        if (now - db_datetime).total_seconds() > int(os.getenv("MAX_DURATION")):
            cursor.execute("DELETE FROM verification_table WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return -2

        if attempts >= int(os.getenv("MAX_ATTEMPS")):
            cursor.execute("DELETE FROM verification_table WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return -1

        if code == db_code:
            cursor.execute("DELETE FROM verification_table WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return 1
        else:
            cursor.execute("UPDATE verification_table SET attempts = attempts + 1 WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return 0
    else:
        return -4

def send_code_email(to_email, subject, code):
    try:

        html_content = load_html_template({'code': code})

        email_id = queue_email(to_email, subject, html_content)

        if email_id:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error while queuing the email: {e}")
        return False

def check_fisa(email):
    if email[-7:] == "uphf.fr":
        return True
    return False