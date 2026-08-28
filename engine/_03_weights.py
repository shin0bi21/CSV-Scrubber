from __future__ import annotations

import math
from typing import Iterable

from ._01_types import Ruleset, TokenStat
from ._02_normalization import normalize


def token_document_frequencies(values: Iterable[str]) -> dict[str, int]:
    """Count the number of supplied values containing each distinct token."""

    frequencies: dict[str, int] = {}
    for value in values:
        for token in set(value.split()):
            frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies


def automatic_token_weight(count: int, total: int) -> float:
    """Return an IDF-style rarity weight from 0 (common) to 1 (rare)."""

    if not total or not count:
        return 0.0
    value = math.log((total + 1) / (count + 1)) / math.log(total + 1)
    return round(max(0.0, min(1.0, value)), 2)


def analyze_tokens(values: Iterable[str], rules: Ruleset) -> list[TokenStat]:
    """Return frequent tokens, examples, and their active weights."""

    raw_values = [str(value or "") for value in values]
    normalized_values = [normalize(value, rules) for value in raw_values]
    frequencies = token_document_frequencies(normalized_values)
    total = len(raw_values)
    if not total:
        return []

    stats: list[TokenStat] = []
    for token, count in frequencies.items():
        if count < rules.common_token_min_documents:
            continue
        automatic = automatic_token_weight(count, total)
        examples = tuple(
            value
            for value, normalized in zip(raw_values, normalized_values)
            if token in set(normalized.split())
        )[:3]
        active = max(
            0.0,
            min(1.0, float(rules.token_weights.get(token, automatic))),
        )
        stats.append(TokenStat(
            token=token,
            count=count,
            percentage=round(count / total * 100, 1),
            automatic_weight=automatic,
            weight=active,
            examples=examples,
        ))
    return sorted(stats, key=lambda item: (-item.count, item.token))


def build_token_weights(
    frequencies: dict[str, int],
    total: int,
    rules: Ruleset,
) -> dict[str, float]:
    """Build automatic token weights and apply explicit overrides."""

    weights = {
        token: automatic_token_weight(count, total)
        for token, count in frequencies.items()
    }
    for token, weight in rules.token_weights.items():
        weights[token] = max(0.0, min(1.0, float(weight)))
    return weights
