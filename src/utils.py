import re
import unicodedata
from rapidfuzz import fuzz, process
import easyocr
import requests
import cv2
import numpy as np


# --- Parameters ---

# Season regex
SEASON_REGEX = re.compile(
    r"""
    (?<!\d)
    (
        (20\d{2})      # (2023)
        [\-/ ]         # -, / space
        (20\d{2}|\d{2}) # 2024 or 24
        |
        (\d{2})
        [\-/]
        (\d{2})
    )
    (?!\d)
    """,
    re.VERBOSE
)

YEAR_REGEX = re.compile(r"\b(20\d{2})\b")


# Kit types
KIT_TYPE_KEYWORDS = {
    "home": ["domicile", "home"],
    "away": ["extérieur", "exterieur", "away"],
    "third": ["third", "3rd", "troisième", "troisieme"]
}

ALL_KIT_KEYWORDS = []
KEYWORD_TO_TYPE = {}
for kit_type, keywords in KIT_TYPE_KEYWORDS.items():
    for kw in keywords:
        ALL_KIT_KEYWORDS.append(kw)
        KEYWORD_TO_TYPE[kw] = kit_type


# Players
PLAYERS = [
    "saka", "odegaard", "martinelli", "saliba", "gabriel",
    "white", "trossard", "jesus", "smithrowe", "havertz", "walcott",
    "henry", "pires", "vieira", "bergkamp", "adams", "ljungberg", "campbell",
    "cazorla", "wilshere", "koscielny", "lewisskelly", "nwaneri", "coquelin"
]
SPONSOR_WORDS = ["fly", "emirates", "adidas", "puma", "nike", "climalite", "aeroready"]
LANGS = ["en"]
reader = easyocr.Reader(LANGS)


# --- Functions ---

# Season
def normalize_season(match):
    if not match:
        return None

    groups = match.groups()

    # season regex
    if groups[1] and groups[2]:
        start = groups[1]
        end = groups[2]

        if len(end) == 2:
            end = start[:2] + end  # 23 -> 2023 → 2024

        return f"{start}-{end}"

    if groups[3] and groups[4]:
        start = "20" + groups[3]
        end = "20" + groups[4]
        return f"{start}-{end}"

    return None

def extract_season(title):
    title = title.lower()

    # season
    match = SEASON_REGEX.search(title)
    if match:
        return normalize_season(match)

    # fallback : year
    match = YEAR_REGEX.search(title)
    if match:
        year = match.group(1)
        return year

    return None


# Kit type
def normalize(s, input_type="kit"):
    """Lowercase, remove accents, remove spaces."""
    s = s.lower()
    s = ''.join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    if input_type == "kit":
        return s
    else:
        return s.replace(" ", "")


def check_kit_type_simple(title):
    if not title:
        return None

    text = normalize(title)

    for kit_type, keywords in KIT_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return kit_type

    return None


def guess_kit_type(title, threshold=80):
    if not title:
        return None

    text = normalize(title, input_type="kit")

    # split title into words to avoid matching the whole sentence
    words = text.split()

    best_match = None
    best_score = 0

    for word in words:
        match, score, _ = process.extractOne(
            word,
            ALL_KIT_KEYWORDS,
            scorer=fuzz.ratio
        )

        if score > best_score:
            best_match = match
            best_score = score

    if best_score < threshold:
        return None

    return KEYWORD_TO_TYPE.get(best_match)


def extract_kit_type(title):
    return check_kit_type_simple(title) or guess_kit_type(title)



# Player name
def guess_player_name(ocr_text, players_list, threshold=70):
    if not ocr_text:
        return None
    
    text = normalize(ocr_text, input_type="player")

    # hard filter: ignore sponsors
    if any(w in text for w in SPONSOR_WORDS):
        return None

    # fuzzy matching
    match, score, idx = process.extractOne(text, players_list, scorer=fuzz.ratio)

    # threshold condition
    if score < threshold:
        return None

    # length similarity condition (avoid matching "fly emirates")
    if abs(len(text) - len(match)) > 3:
        return None

    return match


def extract_player_name_ocr(image_url: str):
    try:
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to download image: {e}")
        return None

    # Convert image bytes to numpy array
    image_bytes = np.frombuffer(response.content, np.uint8)

    # Decode image (supports jpeg, png, webp, etc.)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    if image is None:
        print("Failed to decode image")
        return None

    # OCR
    result = reader.readtext(image)

    extracted_texts = [text for (_, text, _) in result]
    print(extracted_texts)

    # Try to find player name among detected texts
    detected_player = None
    for txt in extracted_texts:
        candidate = guess_player_name(txt, PLAYERS)
        if candidate:
            detected_player = candidate
            break

    return detected_player
