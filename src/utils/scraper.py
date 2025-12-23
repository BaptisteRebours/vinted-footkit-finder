# --- Imports ---
import os
import json
from datetime import datetime, timezone

from utils.extract_info import (
    extract_kit_type,
    extract_season,
)
from utils.ocr import extract_player_name_ocr
from domain.request import SAVED_ITEMS_FILE, MY_KITS


# --- Parameters ---
MY_KITS_SEASON_KITTYPE = [
    (kit["season"], kit["kit_type"]) for kit in MY_KITS
]


# --- Functions ---
def load_state():
    """Load saved items state from file.
    
    Returns:
        dict: State dictionary with 'last_email_sent' and 'items' keys.
    """
    if not os.path.exists(SAVED_ITEMS_FILE):
        return {"last_email_sent": None, "items": []}

    try:
        with open(SAVED_ITEMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return {"last_email_sent": None, "items": []}

    # Force correct format
    return {
        "last_email_sent": data.get("last_email_sent"),
        "items": data.get("items", [])
    }


def filter_and_build_items(items, desired_brands, desired_sizes, saved_ids):
    """Filter and build new items from scraped data.

    Args:
        items (list): List of scraped item objects.
        desired_brands (set): Set of desired brand names.
        desired_sizes (set): Set of desired size titles.
        saved_ids (set): Set of already saved item IDs.

    Returns:
        list: List of new item dictionaries.
    """
    new_items = []

    for item in items:
        data = item.raw_data or {}

        item_id = str(data.get("id"))
        title = (data.get("title") or "").strip()
        brand = (data.get("brand_title") or "")
        brand = brand.lower() if brand else None
        size = data.get("size_title")
        status = data.get("status")
        url_item = data.get("url")
        price = (data.get("price") or {}).get("amount")
        photos = data.get('photos') or []
        urls_photo = [
            photo.get("full_size_url") for photo in photos if photo.get("full_size_url")
        ] if photos else []

        if item_id in saved_ids:
            continue

        if not title:
            continue
        else:
            season = extract_season(title)
            kit_type = extract_kit_type(title)
            
        is_match = (
            "maillot" in title.lower()
            and "arsenal" in title.lower()
            and (brand in desired_brands or brand is None)
            and (size in desired_sizes or size is None)
        )

        player_name = None

        if is_match and urls_photo:
            for url_photo in urls_photo:
                player_name = extract_player_name_ocr(url_photo)
                if player_name:
                    break
            
            item_to_add = (
                player_name is not None and
                item_id not in saved_ids and
                (season, kit_type) not in MY_KITS_SEASON_KITTYPE
            )

            if item_to_add:
                new_items.append(
                    {
                        "id": item_id,
                        "title": title,
                        "brand": brand,
                        "status": status,
                        "size": size,
                        "season": season,
                        "kit_type": kit_type,
                        "player_name": player_name,
                        "url": url_item,
                        "price": price,
                        "urls_photo": urls_photo,
                        "date_added": datetime.now(timezone.utc).isoformat()
                    }
                )
                saved_ids.add(item_id)

    return new_items
