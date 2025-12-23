# --- Imports ---
import sqlite3
import json
import os

from domain.request import SAVED_ITEMS_DB, OUTPUT_DIR


# --- Parameters ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
CONN = sqlite3.connect(SAVED_ITEMS_DB)
CURSOR = CONN.cursor()


# --- Functions ---

# Create
def create_table():
    """Create the saved_items table if it does not exist.
    
    Returns:
        None
    """
    CURSOR.execute("""
    CREATE TABLE IF NOT EXISTS saved_items (
        id TEXT PRIMARY KEY,
        title TEXT,
        brand TEXT,
        status TEXT,
        size TEXT,
        season TEXT,
        kit_type TEXT,
        player_name TEXT,
        url TEXT,
        price TEXT,
        url_photo TEXT,
        date_added TEXT,
        email_sent INTEGER DEFAULT 0
    )
    """)
    CONN.commit()

# Insert
def insert_into_sqlite(item):
    """Insert an item into the SQLite database.
    
    Args:
        item (dict): The item dictionary to insert.
    
    Returns:
        None
    """
    CURSOR.execute("""
    INSERT OR IGNORE INTO saved_items (
        id, title, brand, status, size, season, kit_type,
        player_name, url, price, url_photo, date_added
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["id"],
        item["title"],
        item["brand"],
        item["status"],
        item["size"],
        item["season"],
        item["kit_type"],
        item["player_name"],
        item["url"],
        item["price"],
        item["url_photo"],
        item["date_added"]
    ))
    CONN.commit()

# Get all items
def get_all_items():
    """Retrieve all items from the database.
    
    Returns:
        list of dict: List of all items.
    """
    CURSOR.execute("""
    SELECT *
    FROM saved_items
    """)
    data = CURSOR.fetchall()
    columns = [desc[0] for desc in CURSOR.description]
    all_items = [dict(zip(columns, row)) for row in data]
    return all_items

# Get unsent items
def get_unsent_items():
    """Retrieve all items that have not been marked as email sent.
    
    Returns:
        list of dict: List of unsent items.
    """
    CURSOR.execute("""
    SELECT *
    FROM saved_items
    WHERE email_sent = 0
    """)
    data = CURSOR.fetchall()
    columns = [desc[0] for desc in CURSOR.description]
    items_to_email = [dict(zip(columns, row)) for row in data]
    return items_to_email


# Update after email sent
def mark_email_sent():
    """Mark all items as email sent in the database.
    
    Returns:
        None
    """
    CURSOR.execute("""
    UPDATE saved_items
    SET email_sent = 1
    WHERE email_sent = 0
    """)
    CONN.commit()


# --- Main Execution ---

# # Create table
# create_table()

# # One shot insertion from JSON to SQLite
# with open("data/output/vinted_saved_items.json") as f:
#     data = json.load(f)
# for item in data["items"]:
#     insert_into_sqlite(item)
