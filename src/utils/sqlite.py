# --- Imports ---
import sqlite3
import json
import os

from domain.request import SAVED_ITEMS_DB


# --- Functions ---

# Get connection
def get_connection():
    """Get a SQLite connection."""
    return sqlite3.connect(SAVED_ITEMS_DB)

# Create
def create_table():
    """Create the saved_items table if it does not exist.
    
    Returns:
        None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
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
    conn.commit()

# Insert
def insert_into_sqlite(item):
    """Insert an item into the SQLite database.
    
    Args:
        item (dict): The item dictionary to insert.
    
    Returns:
        None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
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
    conn.commit()

# Get all items
def get_all_items():
    """Retrieve all items from the database.
    
    Returns:
        list of dict: List of all items.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT *
    FROM saved_items
    """)
    data = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    all_items = [dict(zip(columns, row)) for row in data]
    return all_items

# Get unsent items
def get_unsent_items():
    """Retrieve all items that have not been marked as email sent.
    
    Returns:
        list of dict: List of unsent items.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT *
    FROM saved_items
    WHERE email_sent = 0
    """)
    data = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    items_to_email = [dict(zip(columns, row)) for row in data]
    return items_to_email


# Update after email sent
def mark_email_sent():
    """Mark all items as email sent in the database.
    
    Returns:
        None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE saved_items
    SET email_sent = 1
    WHERE email_sent = 0
    """)
    conn.commit()


# --- Main Execution ---

# # Create table
# create_table()

# # One shot insertion from JSON to SQLite
# with open("data/output/vinted_saved_items.json") as f:
#     data = json.load(f)
# for item in data["items"]:
#     insert_into_sqlite(item)
