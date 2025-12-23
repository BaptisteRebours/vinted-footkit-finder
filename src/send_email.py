# --- Imports ---
import os
import json
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from domain.request import SAVED_ITEMS_FILE
from utils.email import items_since_last_email, build_email_html


# --- Checking its time to send email ---
now = datetime.now(ZoneInfo("Europe/Paris"))
mail_days = {0, 3, 6}
if not (now.hour >= 22 and now.weekday() in mail_days):
    print("Not email time, exiting.")
    exit(0)


# --- Parameters ---
# Environment variables
load_dotenv()
EMAIL_SENDER = EMAIL_RECEIVER = os.getenv("EMAIL_SENDER")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_PWD = os.getenv("EMAIL_PWD")

# Saved items
if not os.path.exists(SAVED_ITEMS_FILE):
    print("No state file found.")
    exit(0)
with open(SAVED_ITEMS_FILE, "r", encoding="utf-8") as f:
    state = json.load(f)
last_email_sent = state.get("last_email_sent")
saved_items = state.get("items", [])


# --- Filtering recent items ---
recent_items = items_since_last_email(saved_items, last_email_sent)


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
state["last_email_sent"] = datetime.now(timezone.utc).isoformat()

with open(SAVED_ITEMS_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

print("State updated.")
