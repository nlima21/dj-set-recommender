"""
Camelot Wheel logic for harmonic mixing.

The Camelot Wheel maps musical keys to positions (1A-12B) so DJs
can identify compatible key transitions that sound natural when mixed.

Compatible transitions:
    - Same position (e.g. 8A → 8A): Perfect match
    - +/- 1 position (e.g. 8A → 7A or 9A): Adjacent, smooth
    - Same number, opposite letter (e.g. 8A → 8B): Relative major/minor
"""

# Spotify returns key as Pitch Class (0=C, 1=C#, 2=D ... 11=B)
# mode: 0 = minor, 1 = major
# This maps (pitch_class, mode) → Camelot position string
CAMELOT_MAP = {
    (0, 1): "8B",   # C major
    (1, 1): "3B",   # C# major
    (2, 1): "10B",  # D major
    (3, 1): "5B",   # Eb major
    (4, 1): "12B",  # E major
    (5, 1): "7B",   # F major
    (6, 1): "2B",   # F# major
    (7, 1): "9B",   # G major
    (8, 1): "4B",   # Ab major
    (9, 1): "11B",  # A major
    (10, 1): "6B",  # Bb major
    (11, 1): "1B",  # B major
    (0, 0): "5A",   # C minor
    (1, 0): "12A",  # C# minor
    (2, 0): "7A",   # D minor
    (3, 0): "2A",   # Eb minor
    (4, 0): "9A",   # E minor
    (5, 0): "4A",   # F minor
    (6, 0): "11A",  # F# minor
    (7, 0): "6A",   # G minor
    (8, 0): "1A",   # Ab minor
    (9, 0): "8A",   # A minor
    (10, 0): "3A",  # Bb minor
    (11, 0): "10A", # B minor
}

# Reverse map: Camelot string → (pitch_class, mode)
CAMELOT_REVERSE = {v: k for k, v in CAMELOT_MAP.items()}

# Human-readable key names for display
KEY_NAMES = {
    (0, 1): "C maj", (1, 1): "C# maj", (2, 1): "D maj",
    (3, 1): "Eb maj", (4, 1): "E maj", (5, 1): "F maj",
    (6, 1): "F# maj", (7, 1): "G maj", (8, 1): "Ab maj",
    (9, 1): "A maj", (10, 1): "Bb maj", (11, 1): "B maj",
    (0, 0): "C min", (1, 0): "C# min", (2, 0): "D min",
    (3, 0): "Eb min", (4, 0): "E min", (5, 0): "F min",
    (6, 0): "F# min", (7, 0): "G min", (8, 0): "Ab min",
    (9, 0): "A min", (10, 0): "Bb min", (11, 0): "B min",
}


def get_camelot(key: int, mode: int) -> str:
    """Convert Spotify pitch class + mode to Camelot position string."""
    return CAMELOT_MAP.get((key, mode), "Unknown")


def get_key_name(key: int, mode: int) -> str:
    """Return human-readable key name (e.g. 'A minor')."""
    return KEY_NAMES.get((key, mode), "Unknown")


def get_compatible_keys(camelot_position: str) -> list[str]:
    """
    Return list of Camelot positions that are harmonically compatible
    with the given position.

    Rules:
        1. Same position (perfect match)
        2. +1 number (energy boost)
        3. -1 number (wind down)
        4. Same number, swap A/B (relative major/minor)
    """
    if camelot_position == "Unknown":
        return []

    number = int(camelot_position[:-1])
    letter = camelot_position[-1]
    opposite = "B" if letter == "A" else "A"

    compatible = [
        camelot_position,                             # Same key
        f"{(number % 12) + 1}{letter}",              # +1
        f"{((number - 2) % 12) + 1}{letter}",        # -1
        f"{number}{opposite}",                        # Relative major/minor
    ]

    return compatible


def compatibility_score(key1: int, mode1: int, key2: int, mode2: int) -> float:
    """
    Return a harmonic compatibility score between 0.0 and 1.0.

    1.0 = perfect match (same key)
    0.8 = adjacent or relative key
    0.0 = incompatible
    """
    cam1 = get_camelot(key1, mode1)
    cam2 = get_camelot(key2, mode2)

    if cam1 == "Unknown" or cam2 == "Unknown":
        return 0.0

    compatible = get_compatible_keys(cam1)

    if cam2 == cam1:
        return 1.0
    elif cam2 in compatible:
        return 0.8
    else:
        return 0.0
