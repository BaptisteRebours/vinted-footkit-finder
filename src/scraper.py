import asyncio
import random
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from vinted_api_kit import VintedApi
from aiohttp import ClientError
import time


# --- Parameters ---

# Saved items
SAVED_ITEMS_FILE = "./data/output/vinted_saved_items.json"

# Search parameters
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


# --- Loading saved items file ---
try:
    with open(SAVED_ITEMS_FILE, "r", encoding="utf-8") as f:
        saved_items = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    saved_items = []

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

        is_match = (
            "maillot" in title.lower()
            and "arsenal" in title.lower()
            and (brand in desired_brands or brand is None)
            and (size in desired_sizes or size is None)
        )

        if is_match and item_id not in saved_ids:
            new_items.append(
                {
                    "id": item_id,
                    "title": title,
                    "brand": brand,
                    "status": status,
                    "size": size,
                    "url": url_item,
                    "price": price,
                    "url_photo": url_photo,
                    "date_added": datetime.now().isoformat()
                }
            )
            saved_ids.add(item_id)

    return new_items




# --- Scraping ---

async def main():
    # URL
    base_url = "https://www.vinted.fr/catalog?"

    async with VintedApi(
        locale="fr",
        cookies_dir=COOKIES_DIR,
        persist_cookies=PERSIST_COOKIES,
    ) as vinted:
        for search_text in SEARCH_TEXTS_BRANDS:
            params = {"search_text": search_text, "order": ORDER}
            search_url = base_url + urlencode(params, doseq=True)

            # Sleeping
            await asyncio.sleep(random.uniform(1.5, 3.0))

            # Attempts with backoff in case of error
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    # Fetching
                    print(f"Sending request to {search_url} (attempt {attempt+1})")
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
            
            # --- Updating saved items file ---    
            if new_saved_items:
                saved_items.extend(new_saved_items)
                with open(SAVED_ITEMS_FILE, "w", encoding="utf-8") as f:
                    json.dump(saved_items, f, ensure_ascii=False, indent=2)    
                print(f"{len(new_saved_items)} new items saved")
            else:
                print(f"No item saved")


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    print(time.time() - start)
