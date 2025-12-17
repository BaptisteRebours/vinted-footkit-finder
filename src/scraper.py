import asyncio
import random
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from vinted_api_kit import VintedApi
from aiohttp import ClientError

from utils import (
    extract_season, 
    extract_kit_type, 
    extract_player_name_ocr,
)


# --- Parameters ---

# Saved items
SAVED_ITEMS_FILE = "./data/output/vinted_saved_items.json"
os.makedirs(os.path.dirname(SAVED_ITEMS_FILE), exist_ok=True)

# Search parameters
BASE_URL = "https://www.vinted.fr/catalog?"
SEARCH_TEXT = "maillot arsenal"
ORDER = "newest_first"
DESIRED_BRANDS = ["nike", "adidas"]
DESIRED_SIZES = ["XS", "S", "M", "16 ans / 176cm"]

MAX_RETRIES = 3
BACKOFF_BASE = 2  

SEARCH_TEXTS_BRANDS = [SEARCH_TEXT] + [f"{SEARCH_TEXT} {b}" for b in DESIRED_BRANDS]

# Environment
RUNNING_IN_GITHUB = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
PERSIST_COOKIES = not RUNNING_IN_GITHUB
COOKIES_DIR = Path("./cookies") if PERSIST_COOKIES else None
if COOKIES_DIR :
    COOKIES_DIR.mkdir(parents=True, exist_ok=True)


# --- Loading saved items file ---
def load_state():
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

state = load_state()
saved_items = state["items"]
saved_items_ids = {item["id"] for item in saved_items}


# --- Functions ---
def filter_and_build_items(items, desired_brands, desired_sizes, saved_ids):
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
        url_photo = (data.get("photo") or {}).get("full_size_url")

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

        if is_match and url_photo:
            
            player_name = extract_player_name_ocr(url_photo)

            if player_name and item_id not in saved_ids:
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
                        "url_photo": url_photo,
                        "date_added": datetime.now(timezone.utc).isoformat()
                    }
                )
                saved_ids.add(item_id)

    return new_items




# --- Scraping ---

async def main():
    print("Running scraper...")

    async with VintedApi(
        locale="fr",
        cookies_dir=COOKIES_DIR,
        persist_cookies=PERSIST_COOKIES,
    ) as vinted:
        
        for search_text in SEARCH_TEXTS_BRANDS:
            params = {"search_text": search_text, "order": ORDER}
            search_url = BASE_URL + urlencode(params, doseq=True)

            # Sleeping
            await asyncio.sleep(random.uniform(1.5, 3.0))

            # Attempts with backoff in case of error
            new_saved_items = []
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    # Fetching
                    print(f"Sending request to {search_url} (attempt {attempt})")
                    items = await vinted.search_items(url=search_url)
                    print(f"{len(items)} items fetched")

                    # Processing each item
                    new_saved_items = filter_and_build_items(
                        items,
                        DESIRED_BRANDS,
                        DESIRED_SIZES,
                        saved_items_ids
                    )
                    break

                except ClientError as e:
                    print(f"Client error: {e}")
                    if attempt == MAX_RETRIES:
                        print("Maximum retries for this search_text - stop.")
                        break
                    backoff = (BACKOFF_BASE ** attempt) + random.uniform(0, 1.0)
                    print(f"Waiting before retry: {backoff:.1f}s")
                    await asyncio.sleep(backoff)
                
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    break
            
            # Updating saved items file
            if new_saved_items:
                saved_items.extend(new_saved_items) 
                print(f"{len(new_saved_items)} new items saved")
    
    # Save updated state
    new_state = {
        "last_email_sent": state["last_email_sent"],
        "items": saved_items
    }
    with open(SAVED_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)
    print("Scraper finished.")


if __name__ == "__main__":
    asyncio.run(main())
