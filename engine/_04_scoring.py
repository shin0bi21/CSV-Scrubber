from __future__ import annotations

from difflib import SequenceMatcher

try:
    from rapidfuzz.fuzz import ratio as _rapid_ratio
except ImportError:  # The app remains usable before dependencies are installed.
    _rapid_ratio = None

from ._00_models import MatchEvidence, Ruleset
from ._02_weights import (
    automatic_token_weight,
    build_token_weights,
    token_document_frequencies,
)
from ._03_candidates import CandidateValue, as_columns, candidate_pairs


def sequence_ratio(left: str, right: str) -> float:
    """Return standard-library character similarity from 0 to 100."""

    return SequenceMatcher(None, left, right).ratio() * 100


def token_ratio(left: str, right: str) -> float:
    """Compare two individual tokens using RapidFuzz or the fallback."""

    if _rapid_ratio is not None:
        return float(_rapid_ratio(left, right))
    return sequence_ratio(left, right)


def weighted_token_score(
    left: str,
    right: str,
    weights: dict[str, float],
) -> MatchEvidence:
    """Match tokens one-to-one and return their weighted score and evidence."""

    left_tokens = left.split()
    right_tokens = right.split()
    if not left_tokens or not right_tokens:
        return MatchEvidence(score=0.0)

    def importance(token: str) -> float:
        return max(0.0, min(2.0, float(weights.get(token, 1.0))))

    left_weights = [importance(token) for token in left_tokens]
    right_weights = [importance(token) for token in right_tokens]
    active_left = [
        (index, token, weight)
        for index, (token, weight) in enumerate(zip(left_tokens, left_weights))
        if weight > 0
    ]
    active_right = [
        (index, token, weight)
        for index, (token, weight) in enumerate(zip(right_tokens, right_weights))
        if weight > 0
    ]
    if not active_left or not active_right:
        return MatchEvidence(
            score=0.0,
            unmatched_left_tokens=tuple(left_tokens),
            unmatched_right_tokens=tuple(right_tokens),
        )

    possible_matches = sorted(
        (
            token_ratio(left_token, right_token),
            left_index,
            right_index,
            left_weight,
            right_weight,
        )
        for left_index, left_token, left_weight in active_left
        for right_index, right_token, right_weight in active_right
    )
    possible_matches.reverse()

    used_left: set[int] = set()
    used_right: set[int] = set()
    matched_left: set[int] = set()
    matched_right: set[int] = set()
    matched_weight = 0.0
    exact_matches: list[tuple[str, str]] = []
    fuzzy_matches: list[tuple[str, str, float]] = []
    for similarity, left_index, right_index, left_weight, right_weight in possible_matches:
        if left_index in used_left or right_index in used_right:
            continue
        used_left.add(left_index)
        used_right.add(right_index)
        matched_weight += (similarity / 100.0) * min(left_weight, right_weight)
        if similarity <= 0:
            continue
        matched_left.add(left_index)
        matched_right.add(right_index)
        left_token = left_tokens[left_index]
        right_token = right_tokens[right_index]
        if left_token == right_token and similarity == 100:
            exact_matches.append((left_token, right_token))
        else:
            fuzzy_matches.append((left_token, right_token, round(similarity, 1)))

    left_total = sum(weight for _index, _token, weight in active_left)
    right_total = sum(weight for _index, _token, weight in active_right)
    smaller_total = min(left_total, right_total)
    larger_total = max(left_total, right_total)
    shorter_coverage = matched_weight / smaller_total * 100 if smaller_total else 0.0
    longer_coverage = matched_weight / larger_total * 100 if larger_total else 0.0
    unmatched_left = tuple(
        token for index, token in enumerate(left_tokens) if index not in matched_left
    )
    unmatched_right = tuple(
        token for index, token in enumerate(right_tokens) if index not in matched_right
    )
    return MatchEvidence(
        score=round(max(0.0, min(100.0, shorter_coverage)), 1),
        exact_token_matches=tuple(exact_matches),
        fuzzy_token_matches=tuple(fuzzy_matches),
        unmatched_left_tokens=unmatched_left,
        unmatched_right_tokens=unmatched_right,
        shorter_name_coverage=round(max(0.0, min(100.0, shorter_coverage)), 1),
        longer_name_coverage=round(max(0.0, min(100.0, longer_coverage)), 1),
    )


def column_aware_score(
    left: CandidateValue,
    right: CandidateValue,
    weights: dict[str, float],
    column_weights: tuple[float, ...] | None = None,
) -> MatchEvidence:
    """Score corresponding selected columns with optional field weights."""

    left_columns = as_columns(left)
    right_columns = as_columns(right)
    column_count = max(len(left_columns), len(right_columns))
    column_evidence: list[tuple[MatchEvidence, float]] = []
    for index in range(column_count):
        field_weight = (
            column_weights[index]
            if column_weights and index < len(column_weights)
            else 1.0
        )
        if field_weight <= 0:
            continue
        left_value = left_columns[index] if index < len(left_columns) else ""
        right_value = right_columns[index] if index < len(right_columns) else ""
        if not left_value and not right_value:
            continue
        if not left_value or not right_value:
            column_evidence.append((MatchEvidence(
                score=0.0,
                unmatched_left_tokens=tuple(left_value.split()),
                unmatched_right_tokens=tuple(right_value.split()),
            ), field_weight))
            continue
        column_evidence.append((
            weighted_token_score(left_value, right_value, weights),
            field_weight,
        ))
    if not column_evidence:
        return MatchEvidence(score=0.0)

    total_weight = sum(weight for _evidence, weight in column_evidence)
    return MatchEvidence(
        score=round(
            sum(item.score * weight for item, weight in column_evidence) / total_weight,
            1,
        ),
        exact_token_matches=tuple(
            match
            for item, _weight in column_evidence
            for match in item.exact_token_matches
        ),
        fuzzy_token_matches=tuple(
            match
            for item, _weight in column_evidence
            for match in item.fuzzy_token_matches
        ),
        unmatched_left_tokens=tuple(
            token
            for item, _weight in column_evidence
            for token in item.unmatched_left_tokens
        ),
        unmatched_right_tokens=tuple(
            token
            for item, _weight in column_evidence
            for token in item.unmatched_right_tokens
        ),
        shorter_name_coverage=round(
            sum(item.shorter_name_coverage * weight for item, weight in column_evidence)
            / total_weight,
            1,
        ),
        longer_name_coverage=round(
            sum(item.longer_name_coverage * weight for item, weight in column_evidence)
            / total_weight,
            1,
        ),
    )


def score_candidate_edges(
    left_values: list[CandidateValue],
    right_values: list[CandidateValue],
    rules: Ruleset,
    same_source: bool = False,
    column_names: list[str] | tuple[str, ...] | None = None,
) -> dict[tuple[int, int], MatchEvidence]:
    """Score candidates and retain accepted edges with their evidence."""

    scores: dict[tuple[int, int], MatchEvidence] = {}
    values = left_values if same_source else left_values + right_values
    scalar_values = [
        column_value
        for value in values
        for column_value in as_columns(value)
        if column_value
    ]
    frequencies = token_document_frequencies(scalar_values)
    weights = build_token_weights(frequencies, len(scalar_values), rules)
    for token, count in frequencies.items():
        if token not in rules.token_weights:
            weights[token] = 1.0 + automatic_token_weight(count, len(scalar_values))

    names = tuple(column_names or ())
    field_weights = tuple(
        max(0.0, float(rules.column_weights.get(name, 1.0)))
        for name in names
    ) if names else None

    for left, right in candidate_pairs(left_values, right_values, same_source, rules):
        left_value = left_values[left]
        right_value = right_values[right]
        evidence = column_aware_score(
            left_value,
            right_value,
            weights,
            field_weights,
        )
        if evidence.score >= 100.0 and left_value != right_value:
            evidence = MatchEvidence(
                score=99.0,
                exact_token_matches=evidence.exact_token_matches,
                fuzzy_token_matches=evidence.fuzzy_token_matches,
                unmatched_left_tokens=evidence.unmatched_left_tokens,
                unmatched_right_tokens=evidence.unmatched_right_tokens,
                shorter_name_coverage=evidence.shorter_name_coverage,
                longer_name_coverage=evidence.longer_name_coverage,
            )
        if evidence.score >= rules.review_threshold:
            scores[(left, right)] = evidence
    return scores
