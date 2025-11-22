import os
import json
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from datetime import datetime, timedelta
from dotenv import load_dotenv
from zoneinfo import ZoneInfo


### --- Checking its time to send email ---
now = datetime.now(ZoneInfo("Europe/Paris"))
mail_days = {1, 3, 5}
if not (now.hour == 22 and now.weekday() in mail_days):
    print("Not email time, exiting.")
    exit(0)


### --- Parameters ---
# Secret parameters
load_dotenv()
EMAIL_SENDER = EMAIL_RECEIVER = os.getenv("EMAIL_SENDER")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_PWD = os.getenv("EMAIL_PWD")

# Code parameters
SAVED_ITEMS_FILE = "./data/output/vinted_saved_items.json"
DAYS_RANGE = 7  


### --- Loading saved items file ---
try:
    with open(SAVED_ITEMS_FILE, "r", encoding="utf-8") as f:
        saved_items = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    saved_items = []


### --- FIltering new items ---
def get_recent_items(items, days=7):
    now = datetime.utcnow()
    limit_date = now - timedelta(days=days)

    recent = []
    for item in items:
        date_str = item.get("date_added")
        if not date_str:
            continue
        try:
            added = datetime.fromisoformat(date_str)
        except:
            continue
        
        if added >= limit_date:
            recent.append(item)

    return recent


recent_items = get_recent_items(saved_items, DAYS_RANGE)


### --- Sending email ---
def build_email_html(items):
    html = """\
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family:Arial, Helvetica, sans-serif; background:#f5f5f5; padding:24px;">
    """

    if not items:
        html += """\
        <div style="max-width:600px; margin:0 auto; background:#fff1c4; 
                    padding:18px; border-radius:8px; border:1px solid #f2d98c;
                    font-size:16px; color:#705e2f; text-align:center;">
            No new items found this week.
        </div>
        """
    else:
        first = True
        for item in items:
            title = escape(item.get("title", "Untitled"))
            url = escape(item.get("url", "#"))
            photo = escape(item.get("url_photo", "https://via.placeholder.com/300x300?text=No+Image"))
            brand = escape(item.get("brand") or "Unknown brand")
            size = escape(item.get("size") or "Unknown size")
            price = item.get("price", "?")

            # Divider between cards (skip the first one)
            if not first:
                html += """\
                <div style="max-width:600px; margin:24px auto; 
                            border-bottom:2px solid #00A86B33;"></div>
                """
            first = False

            html += f"""\
            <div style="max-width:580px; margin:0 auto; background:#ffffff;
                        border-radius:14px; overflow:hidden; border:1px solid #e0e0e0;
                        box-shadow:0 3px 10px rgba(0,0,0,0.07);">

                <!-- IMAGE -->
                <a href="{url}" target="_blank">
                    <img src="{photo}" alt="{title}" 
                         style="width:100%; display:block;
                                max-height:230px; object-fit:cover;">
                </a>

                <!-- CONTENT -->
                <div style="padding:20px 22px;">

                    <!-- TITLE -->
                    <h2 style="margin:0 0 12px 0; font-size:20px; font-weight:700; color:#008a5a;">
                        <a href="{url}" target="_blank"
                           style="color:#008a5a; text-decoration:none;">
                            {title}
                        </a>
                    </h2>

                    <!-- INFO BOX -->
                    <div style="background:#f8fff9; border:1px solid #bde7cd; padding:14px 16px;
                                border-radius:8px; margin-bottom:18px; font-size:15px; color:#333;">
                        <div><strong>Brand:</strong> {brand}</div>
                        <div><strong>Size:</strong> {size}</div>
                        <div><strong>Price:</strong> {price}€</div>
                    </div>

                    <!-- BUTTON -->
                    <div style="text-align:center;">
                        <a href="{url}" target="_blank"
                           style="display:inline-block; background:#00A86B; color:white;
                                  padding:10px 22px; font-size:15px; border-radius:6px;
                                  text-decoration:none; font-weight:600;">
                            Open listing →
                        </a>
                    </div>

                </div>
            </div>
            """

    html += """
        </body>
    </html>
    """

    return html



html_body = build_email_html(recent_items)


print("Sending email...")

context = ssl.create_default_context()
message = MIMEMultipart("alternative")
message["Subject"] = f"New kits - week {datetime.today().strftime('%Y-%m-%d')}"
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
