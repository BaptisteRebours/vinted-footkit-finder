# --- Parameters ---

# Saved items file
SAVED_ITEMS_FILE = "./data/output/vinted_saved_items.json"

# Request parameters
BASE_URL = "https://www.vinted.fr/catalog?"
ORDER = "newest_first"
MAX_RETRIES = 3
BACKOFF_BASE = 2 

# Query parameters
SEARCH_TEXT = "maillot arsenal"
DESIRED_BRANDS = ["nike", "adidas"]
DESIRED_SIZES = ["XS", "S", "M", "16 ans / 176cm"]

# Filters
MY_KITS = [
    {"player_name": "rice", "season": "2024-2025", "kit_type": "home"},
    {"player_name": "odegaard", "season": "2024-2025", "kit_type": "third"},
    {"player_name": "gabriel", "season": "2023-2024", "kit_type": "third"},
    {"player_name": "saka", "season": "2022-2023", "kit_type": "away"},
    {"player_name": "saliba", "season": "2022-2023", "kit_type": "third"},
    {"player_name": "martinelli", "season": "2021-2022", "kit_type": "away"},
    {"player_name": "tierney", "season": "2019-2020", "kit_type": "away"},
    {"player_name": "ramsey", "season": "2018-2019", "kit_type": "home"},
    {"player_name": "arteta", "season": "2013-2014", "kit_type": "home"},
    {"player_name": "arteta", "season": "2012-2013", "kit_type": "home"}, # bis
    {"player_name": "podolski", "season": "2012-2013", "kit_type": "away"},
    {"player_name": "wilshere", "season": "2012-2013", "kit_type": "third"},
    {"player_name": "henry", "season": "2011-2012", "kit_type": "home"},
    {"player_name": "wilshere", "season": "2010-2011", "kit_type": "away"}, # bis
    {"player_name": "rosicky", "season": "2009-2010", "kit_type": "away"},
    {"player_name": "fabregas", "season": "2008-2009", "kit_type": "third"},
    {"player_name": "fabregas", "season": "2007-2008", "kit_type": "away"}, # bis
    {"player_name": None, "season": "2007-2008", "kit_type": "home"},
    {"player_name": None, "season": "2006-2007", "kit_type": "home"}, # bis
    {"player_name": "henry", "season": "2004-2005", "kit_type": "third"},
    {"player_name": "henry", "season": "2003-2004", "kit_type": "away"}, # bis
    {"player_name": "wright", "season": "1994-1995", "kit_type": "away"},
]
