from __future__ import annotations

import re
import unicodedata

from ._01_types import Ruleset


NormalizedValue = tuple[str, ...]


def normalize(value: str, rules: Ruleset) -> str:
    """Normalize Unicode, case, punctuation, and whitespace consistently."""

    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    if rules.lowercase:
        text = text.casefold()
    if rules.remove_punctuation:
        text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def selected_values(
    rows: list[dict[str, str]],
    columns: list[str] | str,
    rules: Ruleset,
) -> list[NormalizedValue]:
    """Normalize every selected column independently for each row."""

    selected_columns = [columns] if isinstance(columns, str) else list(columns)
    return [
        tuple(normalize(row.get(column, ""), rules) for column in selected_columns)
        for row in rows
    ]
