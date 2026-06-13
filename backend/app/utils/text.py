import re


def normalize_query(query: str) -> str:
    """Normalize user search text without losing Korean keywords."""
    return re.sub(r"\s+", " ", query.strip().lower())


def unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
