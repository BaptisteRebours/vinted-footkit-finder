# --- Imports ---
import os
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import sqlite3

from domain.request import SAVED_ITEMS_DB, OUTPUT_DIR
from utils.email import build_email_html
from utils.sqlite import get_unsent_items, mark_email_sent


# --- Checking its time to send email ---
now = datetime.now(ZoneInfo("Europe/Paris"))
mail_days = {0, 3, 5}
if not (now.hour >= 22 and now.weekday() in mail_days):
    print("Not email time, exiting.")
    exit(0)


# --- Parameters ---
# Environment variables
load_dotenv()
EMAIL_SENDER = EMAIL_RECEIVER = os.getenv("EMAIL_SENDER")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_PWD = os.getenv("EMAIL_PWD")

# Recent saved items
os.makedirs(OUTPUT_DIR, exist_ok=True)
CONN = sqlite3.connect(SAVED_ITEMS_DB)
recent_items = get_unsent_items()


# --- Sending email ---
html_body = build_email_html(recent_items)

print("Sending email...")

context = ssl.create_default_context()
message = MIMEMultipart("alternative")
message["Subject"] = "New Vinted kits"
message["From"] = EMAIL_SENDER
message["To"] = EMAIL_RECEIVER

message.attach(MIMEText(html_body, "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", port=EMAIL_PORT, context=context) as server:
    server.login(user=EMAIL_SENDER, password=EMAIL_PWD)
    server.sendmail(
        from_addr=EMAIL_SENDER,
        to_addrs=[EMAIL_RECEIVER],
        msg=message.as_string()
    )
print("Email sent.")


# --- Update last_email_sent ---
mark_email_sent()
print("State updated.")
