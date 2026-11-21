def normalize_key(value: str) -> str:
    """Lowercase, trim and collapse repeated whitespace.

    Used for the rule 7 keys (artist and title) and for tag names, so
    "  Arthur   VEROCAI " and "arthur verocai" are the same value.
    """
    return " ".join(value.split()).casefold()
