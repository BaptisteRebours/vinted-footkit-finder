# --- Imports ---
import unicodedata


# --- Functions ---

# Season normalization
def normalize_season(match):
    """Normalize season from regex match object.
    
    Args:
        match (re.Match): Match object from SEASON_REGEX.
    
    Returns:
        str|None: Normalized season string or None.
    """
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

# Kit and player name normalization
def normalize(s, input_type="kit"):
    """Lowercase, remove accents, remove spaces.
    
    Args:
        s (str): Input string.
        input_type (str): "kit" or "player" normalization type.

    Returns:
        str: Normalized string.
    """
    s = s.lower()
    s = ''.join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    if input_type == "kit":
        return s
    else:
        return s.replace(" ", "")
    