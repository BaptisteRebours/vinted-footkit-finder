# --- Imports ---
import requests
from rapidfuzz import fuzz, process
import cv2
import numpy as np
import easyocr

from .text import normalize
from domain.kits import SPONSOR_WORDS
from domain.players import PLAYERS


# --- Parameters ---
LANGS = ["en"]
reader = easyocr.Reader(LANGS, verbose=False)


# --- Functions ---

# Player name
def guess_player_name(ocr_text, players_list, threshold=85):
    """Guess player name from OCR text using fuzzy matching.

    Args:
        ocr_text (str): OCR extracted text.
        players_list (list): List of player names.
        threshold (int): Minimum score threshold.

    Returns:
        str|None: Player name string or None.
    """
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
    """Extract player name from image URL using OCR.
    
    Args:
        image_url (str): URL of the image.
    
    Returns:
        str|None: Detected player name or None.
    """
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

    # Try to find player name among detected texts
    detected_player = None
    for txt in extracted_texts:
        candidate = guess_player_name(txt, PLAYERS)
        if candidate:
            print(f"Image URL: {image_url}\nExtracted text: {txt} --> player: {candidate}")
            detected_player = candidate
            break

    return detected_player
