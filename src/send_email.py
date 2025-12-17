import os
import json
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from datetime import datetime, timezone
from dotenv import load_dotenv
from zoneinfo import ZoneInfo


# --- Checking its time to send email ---
now = datetime.now(ZoneInfo("Europe/Paris"))
mail_days = {0, 3, 6}
if not (now.hour >= 14 and now.weekday() in mail_days):
    print("Not email time, exiting.")
    exit(0)


# --- Parameters ---
# Secret parameters
load_dotenv()
EMAIL_SENDER = EMAIL_RECEIVER = os.getenv("EMAIL_SENDER")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_PWD = os.getenv("EMAIL_PWD")

# Code parameters
SAVED_ITEMS_FILE = "./data/output/vinted_saved_items.json"


# --- Loading saved items file ---
if not os.path.exists(SAVED_ITEMS_FILE):
    print("No state file found.")
    exit(0)

with open(SAVED_ITEMS_FILE, "r", encoding="utf-8") as f:
    state = json.load(f)

last_email_sent = state.get("last_email_sent")
saved_items = state.get("items", [])

print(f"DEBUG 1 last_email_sent: {last_email_sent}, type ({type(last_email_sent)})")


if last_email_sent:
    last_email_dt = datetime.fromisoformat(last_email_sent)
else:
    last_email_dt = None

print(f"DEBUG 2 last_email_sent: {last_email_sent}, type ({type(last_email_sent)})")


# --- FIltering new items ---
def items_since_last_email(items, last_sent):
    if last_sent is None:
        return items

    threshold = datetime.fromisoformat(last_sent)
    out = []

    for item in items:
        try:
            added = datetime.fromisoformat(item["date_added"]).astimezone(timezone.utc)
            if added > threshold:
                out.append(item)
        except:
            pass
    return out


recent_items = items_since_last_email(saved_items, last_email_sent)


# --- Sending email ---
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
