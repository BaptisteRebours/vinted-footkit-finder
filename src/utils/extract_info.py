# --- Imports ---
import re
from rapidfuzz import fuzz, process

from .text import normalize_season, normalize
from domain.kits import KIT_TYPE_KEYWORDS


# --- Parameters ---
# Season
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
ALL_KIT_KEYWORDS = []
KEYWORD_TO_TYPE = {}
for kit_type, keywords in KIT_TYPE_KEYWORDS.items():
    for kw in keywords:
        ALL_KIT_KEYWORDS.append(kw)
        KEYWORD_TO_TYPE[kw] = kit_type


# --- Functions ---

def extract_season(title):
    """Extract season from item title.
    
    Args:
        title (str): Item title.
    
    Returns:
        str|None: Extracted season string or None.
    """
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


def check_kit_type_simple(title):
    """Check kit type from title using simple keyword matching.
    
    Args:
        title (str): Item title.
        
    Returns:
        str|None: Kit type string or None.
    """
    if not title:
        return None

    text = normalize(title)

    for kit_type, keywords in KIT_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return kit_type

    return None


def guess_kit_type(title, threshold=80):
    """Guess kit type from title using fuzzy matching.
    
    Args:
        title (str): Item title.
        threshold (int): Minimum score threshold.
    
    Returns:
        str|None: Kit type string or None.
    """
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
    """Extract kit type from item title.

    Args:
        title (str): Item title.

    Returns:
        str|None: Kit type string or None.
    """
    return check_kit_type_simple(title) or guess_kit_type(title)
