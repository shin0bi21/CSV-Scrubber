from __future__ import annotations

import re

from ._01_types import Ruleset
from ._02_normalization import NormalizedValue


def value_has_content(value: NormalizedValue) -> bool:
    """Return whether a normalized row contains text."""

    return any(value)


def blocking_keys(
    value: NormalizedValue,
    ngram_size: int,
) -> set[tuple[int, str, str]]:
    """Build generic token and character keys partitioned by column."""

    keys: set[tuple[int, str, str]] = set()
    size = max(2, int(ngram_size))
    for column_index, text in enumerate(value):
        for token in text.split():
            keys.add((column_index, "token", token))
            compact = re.sub(r"\W", "", token)
            if len(compact) >= size:
                for start in range(len(compact) - size + 1):
                    keys.add((column_index, "gram", compact[start:start + size]))
    return keys


def candidate_pairs(
    left_values: list[NormalizedValue],
    right_values: list[NormalizedValue],
    same_source: bool,
    rules: Ruleset,
) -> set[tuple[int, int]]:
    """Return exhaustive or generically blocked non-empty candidate pairs."""

    strategy = rules.candidate_strategy.casefold()
    if strategy not in {"auto", "exhaustive", "blocked"}:
        raise ValueError(
            "candidate_strategy must be 'auto', 'exhaustive', or 'blocked'."
        )

    nonempty_left = [
        index for index, value in enumerate(left_values) if value_has_content(value)
    ]
    nonempty_right = [
        index for index, value in enumerate(right_values) if value_has_content(value)
    ]
    possible_count = (
        len(nonempty_left) * (len(nonempty_left) - 1) // 2
        if same_source
        else len(nonempty_left) * len(nonempty_right)
    )
    exhaustive = strategy == "exhaustive" or (
        strategy == "auto" and possible_count <= rules.exhaustive_pair_limit
    )
    if exhaustive:
        return {
            (left, right)
            for left in nonempty_left
            for right in nonempty_right
            if not same_source or right > left
        }

    index: dict[tuple[int, str, str], set[int]] = {}
    for right in nonempty_right:
        for key in blocking_keys(
            right_values[right],
            rules.blocking_ngram_size,
        ):
            index.setdefault(key, set()).add(right)

    pairs: set[tuple[int, int]] = set()
    for left in nonempty_left:
        matches: set[int] = set()
        for key in blocking_keys(
            left_values[left],
            rules.blocking_ngram_size,
        ):
            matches.update(index.get(key, ()))
        for right in matches:
            if not same_source or right > left:
                pairs.add((left, right))
    return pairs
