# --- Imports ---
import asyncio
import random
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from vinted_api_kit import VintedApi
from aiohttp import ClientError

from domain.request import (
    SAVED_ITEMS_FILE,
    BASE_URL,
    ORDER,
    MAX_RETRIES,
    BACKOFF_BASE,
    SEARCH_TEXT,
    DESIRED_BRANDS,
    DESIRED_SIZES,
)
from utils.scraper import load_state, filter_and_build_items


# --- Parameters ---

# Saved items
os.makedirs(os.path.dirname(SAVED_ITEMS_FILE), exist_ok=True)

# Search parameters
SEARCH_TEXTS_BRANDS = [SEARCH_TEXT] + [f"{SEARCH_TEXT} {b}" for b in DESIRED_BRANDS]

# Environment
RUNNING_IN_GITHUB = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
PERSIST_COOKIES = not RUNNING_IN_GITHUB
COOKIES_DIR = Path("./cookies") if PERSIST_COOKIES else None
if COOKIES_DIR :
    COOKIES_DIR.mkdir(parents=True, exist_ok=True)


# --- Loading saved items file ---
state = load_state()
saved_items = state["items"]
saved_items_ids = {item["id"] for item in saved_items}


# --- Functions ---
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


# --- Running main ---
if __name__ == "__main__":
    asyncio.run(main())
