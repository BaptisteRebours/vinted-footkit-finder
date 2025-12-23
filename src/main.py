# --- Imports ---
import asyncio
import random
import os
from pathlib import Path
from urllib.parse import urlencode
from vinted_api_kit import VintedApi
from aiohttp import ClientError
import sqlite3
import traceback
import sys

from domain.request import (
    SAVED_ITEMS_DB,
    OUTPUT_DIR,
    BASE_URL,
    ORDER,
    MAX_RETRIES,
    BACKOFF_BASE,
    SEARCH_TEXT,
    DESIRED_BRANDS,
    DESIRED_SIZES,
)
from utils.scraper import filter_and_build_items
from utils.sqlite import create_table, get_all_items, insert_into_sqlite


# --- Parameters ---

# Saved items
os.makedirs(OUTPUT_DIR, exist_ok=True)
CONN = sqlite3.connect(SAVED_ITEMS_DB)

# Search parameters
SEARCH_TEXTS_BRANDS = [SEARCH_TEXT] + [f"{SEARCH_TEXT} {b}" for b in DESIRED_BRANDS]

# Environment
RUNNING_IN_GITHUB = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
PERSIST_COOKIES = not RUNNING_IN_GITHUB
COOKIES_DIR = Path("./cookies") if PERSIST_COOKIES else None
if COOKIES_DIR :
    COOKIES_DIR.mkdir(parents=True, exist_ok=True)


# --- Loading saved items db ---
create_table()
saved_items = get_all_items()
saved_items_ids = {item["id"] for item in saved_items}


# --- Functions ---
async def main():
    try:
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
                
                # Updating saved items db
                if new_saved_items:
                    for item in new_saved_items:
                        insert_into_sqlite(item)
                    print(f"{len(new_saved_items)} new items saved")
        
        print("Scraper finished.")
    
    except Exception as e:
        print("Fatal error in main:")
        traceback.print_exc()
        sys.exit(1)


# --- Running main ---
if __name__ == "__main__":
    asyncio.run(main())
