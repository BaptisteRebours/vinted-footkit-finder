import re
import unicodedata
from rapidfuzz import fuzz, process


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



# --- TEST ---


test_titles = [
    "Maillot domicile Arsenal 23/24",
    "Arsenal away kit 2023-24",
    "Maillot third Arsenal 2024",
    "Arsenal maillot extérieur vintage",
    "arsenal odegaard 8 domucile",
    "arsenal exterrieur ok"
]

for title in test_titles:
    print(extract_kit_type(title))






