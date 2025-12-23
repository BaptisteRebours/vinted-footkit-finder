# --- Imports ---
from datetime import datetime, timezone
from html import escape


# --- Functions ---
def items_since_last_email(items, last_sent):
    """Filter items added since last email sent timestamp.
    
    Args:
        items (list): List of item dicts with "date_added" key.
        last_sent (str|None): ISO format timestamp of last email sent.
    
    Returns:
        list: Filtered list of items added after last_sent.
    """
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


def build_email_html(items):
    """Build HTML body for email listing new items.
    
    Args:
        items (list): List of item dicts.

    Returns:
        str: HTML string for email body.
    """
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
            photos = item.get("urls_photo", [])
            if photos:
                photo = escape(photos[0], "https://via.placeholder.com/300x300?text=No+Image")
            else:
                photo = "https://via.placeholder.com/300x300?text=No+Image"
            brand = escape(item.get("brand") or "Unknown brand")
            size = escape(item.get("size") or "Unknown size")
            season = escape(item.get("season") or "Unknown season")
            kit_type = escape(item.get("kit_type") or "Unknown kit type")
            player_name = escape(item.get("player_name") or "Unknown player")
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
                        <div><strong>Season:</strong> {season}</div>
                        <div><strong>Kit type:</strong> {kit_type}</div>
                        <div><strong>Player:</strong> {player_name.title()}</div>
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
