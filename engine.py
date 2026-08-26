from __future__ import annotations

import csv
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from rapidfuzz.fuzz import ratio as _rapid_ratio
    from rapidfuzz.fuzz import token_set_ratio as _rapid_token_set_ratio
except ImportError:  # The app remains usable before dependencies are installed.
    _rapid_ratio = None
    _rapid_token_set_ratio = None


# ============================================================================
# Data models and rules
# Purpose: define the configuration and result objects shared by the UI and
# the engine pipeline.
# Data shapes:
# - CSV headers are list[str].
# - CSV rows are dict[str, str], keyed by header.
# - A normalized value is one whitespace-separated str of matching tokens.
# ============================================================================
# Shape: Ruleset stores the review threshold, normalization flags, minimum
# common-token frequency, and optional token-to-weight overrides.
@dataclass
class Ruleset:
    """User-controlled normalization, weighting, and review settings."""

    review_threshold: int = 82
    lowercase: bool = True
    remove_punctuation: bool = True
    common_token_min_documents: int = 3
    token_weights: dict[str, float] = field(default_factory=dict)


# Shape: RecordRef stores a source label and a zero-based row index.
@dataclass(frozen=True)
class RecordRef:
    """Identify a source row without copying the row data into a match group."""

    source: str
    index: int


# Shape: MatchGroup stores two or more RecordRef values, the group's score,
# and human-readable reasons for showing it to the reviewer.
@dataclass
class MatchGroup:
    """A connected set of records that requires manual review."""

    records: list[RecordRef]
    score: float
    reasons: list[str] = field(default_factory=list)


# Shape: TokenStat stores one token's document count, percentage, automatic and
# active weights, and up to three source-value examples.
@dataclass(frozen=True)
class TokenStat:
    """Frequency and weighting information shown in common-token analysis."""

    token: str
    count: int
    percentage: float
    automatic_weight: float
    weight: float
    examples: tuple[str, ...]


# ============================================================================
# Stage 1: CSV input and output
# Purpose: load source files before matching and write cleaned results after
# review. Input files are never overwritten by the engine.
# ============================================================================
# Contract: read_csv consumes a str | Path and produces
#           tuple[list[str], list[dict[str, str]]].
# Purpose: read_csv(path) reads a CSV and produces its headers and row records.
# Effects: Opens path for reading.
# Requires: path identifies a readable CSV with a header row.
# Examples:
# read_csv("customers.csv") => (["Name"], [{"Name": "Alice"}])
def read_csv(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a CSV using the supported Windows-friendly encodings."""

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            with open(path, "r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    raise ValueError("The CSV has no header row.")
                headers = [str(header) for header in reader.fieldnames]
                rows = [{header: (row.get(header) or "") for header in headers} for row in reader]
                return headers, rows
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"Unable to decode CSV: {last_error}")


# Contract: write_csv consumes a str | Path, list[str], and Iterable[dict[str, str]]
#           and produces None.
# Purpose: write_csv(path, headers, rows) writes headers and rows to a CSV file.
# Effects: Opens path for writing and replaces its contents if it already exists.
# Requires: every row is compatible with headers; path is writable.
# Examples:
# write_csv("cleaned.csv", ["Name"], [{"Name": "Alice"}]) => None
def write_csv(path: str | Path, headers: list[str], rows: Iterable[dict[str, str]]) -> None:
    """Write headers and rows as a UTF-8 CSV with a BOM for Windows tools."""

    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ============================================================================
# Stage 2: selected-value preparation
# Purpose: combine the user-selected match columns and apply only the generic
# normalization rules before token analysis or matching.
# ============================================================================
# Contract: _combined_values consumes list[dict[str, str]] and list[str] | str
#           and produces list[str].
# Purpose: _combined_values(rows, columns) combines the selected column values
#           into one matching value for each row.
# Examples:
# _combined_values([{"A": "Acme", "B": "Toronto"}], ["A", "B"])
#   => ["Acme Toronto"]
def _combined_values(rows: list[dict[str, str]], columns: list[str] | str) -> list[str]:
    """Combine the selected columns into one match value per row."""

    selected_columns = [columns] if isinstance(columns, str) else columns
    return [" ".join(row.get(column, "") for column in selected_columns).strip() for row in rows]


# Contract: normalize consumes str and Ruleset and produces str.
# Purpose: normalize(value, rules) removes configured textual variation so
#           equivalent values can compare consistently.
# Examples:
# normalize("  ACME, Inc. ", Ruleset()) => "acme inc"
def normalize(value: str, rules: Ruleset) -> str:
    """Normalize Unicode, case, punctuation, and whitespace consistently."""

    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    if rules.lowercase:
        text = text.casefold()
    if rules.remove_punctuation:
        text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


# ============================================================================
# Stage 3: optional common-token analysis
# Purpose: calculate document frequencies and suggested token weights for the
# configuration workspace. This stage informs matching but does not create
# duplicate groups.
# ============================================================================
# Contract: _token_document_frequencies consumes list[str] and produces
#           dict[str, int].
# Purpose: _token_document_frequencies(values) counts the number of values that
#           contain each distinct token.
# Examples:
# _token_document_frequencies(["acme toronto", "acme ottawa"])
#   => {"acme": 2, "toronto": 1, "ottawa": 1}
def _token_document_frequencies(values: list[str]) -> dict[str, int]:
    """Count the number of values containing each distinct token."""

    frequencies: dict[str, int] = {}
    for value in values:
        for token in set(value.split()):
            frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies


# Contract: _automatic_token_weight consumes int and int and produces float.
# Purpose: _automatic_token_weight(count, total) converts token frequency into
#           a bounded IDF-style weight where common tokens weigh less.
# Requires: count and total are non-negative, and count is no greater than total.
# Examples:
# _automatic_token_weight(1, 10) => 0.71
# _automatic_token_weight(10, 10) => 0.0
def _automatic_token_weight(count: int, total: int) -> float:
    """Return an IDF-style weight from 0 (common) to 1 (rare)."""

    if not total or not count:
        return 0.0
    return round(max(0.0, min(1.0, math.log((total + 1) / (count + 1)) / math.log(total + 1))), 2)


# Contract: analyze_tokens consumes Iterable[str] and Ruleset and produces
#           list[TokenStat].
# Purpose: analyze_tokens(values, rules) finds frequent matching tokens and
#           produces their frequencies, examples, and suggested weights.
# Effects: None; does not change values or rules.
# Examples:
# analyze_tokens(["Acme Toronto", "Acme Ottawa", "Acme Hamilton"], Ruleset())
#   => token statistics including "acme"
def analyze_tokens(values: Iterable[str], rules: Ruleset) -> list[TokenStat]:
    """Return frequently occurring tokens and their suggested weights."""

    raw_values = [str(value or "") for value in values]
    normalized_values = [normalize(value, rules) for value in raw_values]
    frequencies = _token_document_frequencies(normalized_values)
    total = len(raw_values)
    if not total:
        return []

    stats: list[TokenStat] = []
    for token, count in frequencies.items():
        if count < rules.common_token_min_documents:
            continue
        automatic_weight = _automatic_token_weight(count, total)
        examples = tuple(
            value for value, normalized in zip(raw_values, normalized_values)
            if token in set(normalized.split())
        )[:3]
        weight = max(0.0, min(1.0, float(rules.token_weights.get(token, automatic_weight))))
        stats.append(TokenStat(
            token=token,
            count=count,
            percentage=round(count / total * 100, 1),
            automatic_weight=automatic_weight,
            weight=weight,
            examples=examples,
        ))
    return sorted(stats, key=lambda stat: (-stat.count, stat.token))


# Contract: _build_token_weights consumes dict[str, int], int, and Ruleset and
#           produces dict[str, float].
# Purpose: _build_token_weights(frequencies, total, rules) combines automatic
#           frequency weights with explicit user overrides.
# Examples:
# _build_token_weights({"acme": 3}, 3, Ruleset()) => {"acme": 0.0}
def _build_token_weights(
    frequencies: dict[str, int],
    total: int,
    rules: Ruleset,
) -> dict[str, float]:
    """Build automatic weights and apply any user-specified overrides."""

    weights = {
        token: _automatic_token_weight(count, total)
        for token, count in frequencies.items()
    }
    for token, weight in rules.token_weights.items():
        weights[token] = max(0.0, min(1.0, float(weight)))
    return weights


# ============================================================================
# Stage 4: candidate generation and fuzzy scoring
# Purpose: reduce comparisons with exact/trigram blocking, then score each
# surviving pair with frequency-weighted fuzzy token matching.
# ============================================================================
# Contract: _trigrams consumes str and produces set[str].
# Purpose: _trigrams(text) produces the three-character keys used to find
#           values that are plausible fuzzy candidates.
# Examples:
# _trigrams("abcd") => {"abc", "bcd"}
def _trigrams(text: str) -> set[str]:
    """Return the compact text's three-character blocking keys."""

    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) < 3:
        return {compact} if compact else set()
    return {compact[index:index + 3] for index in range(len(compact) - 2)}


# Contract: _candidate_pairs consumes list[str], list[str], and bool and
#           produces set[tuple[int, int]].
# Purpose: _candidate_pairs(left_values, right_values, same_source) produces
#           exact/trigram candidate index pairs without fuzzy-scoring every pair.
# Requires: indexes in the result refer to the supplied left and right lists.
# Examples:
# _candidate_pairs(["acme toronto"], ["acme toronto"]) => {(0, 0)}
def _candidate_pairs(
    left_values: list[str],
    right_values: list[str],
    same_source: bool = False,
) -> set[tuple[int, int]]:
    """Build candidate pairs using exact values and shared trigrams."""

    trigram_index: dict[str, set[int]] = {}
    exact_index: dict[str, set[int]] = {}
    for right, value in enumerate(right_values):
        if value:
            exact_index.setdefault(value, set()).add(right)
        for gram in _trigrams(value):
            trigram_index.setdefault(gram, set()).add(right)

    pairs: set[tuple[int, int]] = set()
    for left, value in enumerate(left_values):
        if not value:
            continue
        candidates = set(exact_index.get(value, ()))
        for gram in _trigrams(value):
            candidates.update(trigram_index.get(gram, ()))
        for right in candidates:
            if same_source and right <= left:
                continue
            pairs.add((left, right))
    return pairs


# Contract: _sequence_ratio consumes str and str and produces float.
# Purpose: _sequence_ratio(a, b) produces a 0-to-100 character similarity
#           score using the standard-library fallback.
# Examples:
# _sequence_ratio("acme", "acme") => 100.0
def _sequence_ratio(a: str, b: str) -> float:
    """Provide the standard-library fuzzy ratio fallback."""

    from difflib import SequenceMatcher

    return SequenceMatcher(None, a, b).ratio() * 100


# Contract: _token_ratio consumes str and str and produces float.
# Purpose: _token_ratio(left, right) produces the fuzzy similarity of two
#           individual tokens using RapidFuzz when available.
# Examples:
# _token_ratio("toronto", "toronto") => 100.0
def _token_ratio(left: str, right: str) -> float:
    """Compare two individual tokens using RapidFuzz or the fallback."""

    if _rapid_ratio is not None:
        return float(_rapid_ratio(left, right))
    return _sequence_ratio(left, right)


# Contract: _weighted_token_token_score consumes str, str, and dict[str, float]
#           and produces float.
# Purpose: _weighted_token_token_score(a, b, weights) pairs tokens by fuzzy
#           similarity and produces one frequency-weighted score from 0 to 100.
# Requires: weights contains values from 0 to 1 when a token is present.
# Examples:
# _weighted_token_token_score("acme toronto", "acme toronto", {}) => 100.0
def _weighted_token_token_score(a: str, b: str, weights: dict[str, float]) -> float:
    """Match tokens one-to-one and combine similarities by token importance.

    No business vocabulary is treated as inherently generic or conflicting.
    Token importance comes from the selected data or an explicit user weight,
    while fuzzy token similarity allows abbreviations and small spelling
    changes to contribute without becoming automatic equivalences.
    """

    left_tokens = a.split()
    right_tokens = b.split()
    if not left_tokens or not right_tokens:
        return 0.0

    # Contract: importance consumes str and produces float.
    # Purpose: importance(token) produces the base contribution plus the
    #           configured rarity weight for token.
    def importance(token: str) -> float:
        # Every token still contributes; rare tokens receive additional weight.
        return 1.0 + max(0.0, min(1.0, float(weights.get(token, 1.0))))

    left_weights = [importance(token) for token in left_tokens]
    right_weights = [importance(token) for token in right_tokens]
    possible_matches = sorted(
        (
            _token_ratio(left_token, right_token),
            left_index,
            right_index,
        )
        for left_index, left_token in enumerate(left_tokens)
        for right_index, right_token in enumerate(right_tokens)
    )
    possible_matches.reverse()

    used_left: set[int] = set()
    used_right: set[int] = set()
    matched_weight = 0.0
    for similarity, left_index, right_index in possible_matches:
        if left_index in used_left or right_index in used_right:
            continue
        used_left.add(left_index)
        used_right.add(right_index)
        matched_weight += (similarity / 100.0) * min(
            left_weights[left_index],
            right_weights[right_index],
        )

    smaller_total = min(sum(left_weights), sum(right_weights))
    if not smaller_total:
        return 0.0
    return round(max(0.0, min(100.0, matched_weight / smaller_total * 100)), 1)


# Contract: _score_candidate_edges consumes list[str], list[str], Ruleset, and
#           bool and produces dict[tuple[int, int], float].
# Purpose: _score_candidate_edges(left_values, right_values, rules, same_source)
#           scores blocked pairs and keeps only edges at or above the threshold.
# Examples:
# _score_candidate_edges(["acme"], ["acme"], Ruleset()) => {(0, 0): 100.0}
def _score_candidate_edges(
    left_values: list[str],
    right_values: list[str],
    rules: Ruleset,
    same_source: bool = False,
) -> dict[tuple[int, int], float]:
    """Keep candidate edges whose weighted token scores meet the threshold."""

    scores: dict[tuple[int, int], float] = {}
    values = left_values if same_source else left_values + right_values
    frequencies = _token_document_frequencies(values)
    weights = _build_token_weights(frequencies, len(values), rules)

    for left, right in _candidate_pairs(left_values, right_values, same_source):
        left_value = left_values[left]
        right_value = right_values[right]
        if left_value == right_value:
            scores[(left, right)] = 100.0
            continue

        score = _weighted_token_token_score(left_value, right_value, weights)
        if score < rules.review_threshold:
            continue
        scores[(left, right)] = score
    return scores


# Contract: token_set_ratio consumes str and str and produces float.
# Purpose: token_set_ratio(a, b) produces a complete-value token-set similarity
#           score using RapidFuzz or the standard-library fallback.
# Examples:
# token_set_ratio("Acme Toronto", "Toronto Acme") => 100.0
def token_set_ratio(a: str, b: str) -> float:
    """Compare two complete values with a token-set ratio utility."""

    if not a or not b:
        return 0.0
    if _rapid_token_set_ratio is not None:
        return float(_rapid_token_set_ratio(a, b))
    left, right = set(a.split()), set(b.split())
    common = left & right
    left_only, right_only = left - common, right - common
    shared = " ".join(sorted(common))
    combined_left = " ".join(sorted(common | left_only))
    combined_right = " ".join(sorted(common | right_only))
    return max(
        _sequence_ratio(shared, combined_left) if shared else 0,
        _sequence_ratio(shared, combined_right) if shared else 0,
        _sequence_ratio(combined_left, combined_right),
    )


# ============================================================================
# Stage 5: match grouping
# Purpose: turn accepted pairwise edges into connected duplicate groups and
# calculate one review score/reason for each group.
# ============================================================================
# Shape: _UnionFind stores parent links from each RecordRef to another
# RecordRef, with each root RecordRef representing one connected group.
class _UnionFind:
    """Track connected records while accepted match edges are added."""

    # Contract: _UnionFind.__init__ consumes Iterable[RecordRef] and produces
    #           an initialized _UnionFind object.
    # Purpose: _UnionFind(nodes) starts every supplied record in its own group.
    def __init__(self, nodes: Iterable[RecordRef]):
        """Start each record in its own independent group."""

        self.parent = {node: node for node in nodes}

    # Contract: _UnionFind.find consumes RecordRef and produces RecordRef.
    # Purpose: find(node) produces the root of node's connected group.
    # Effects: Compresses parent links along node's path.
    def find(self, node: RecordRef) -> RecordRef:
        """Return a record's group root and compress its parent path."""

        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[node] != node:
            node, self.parent[node] = self.parent[node], root
        return root

    # Contract: _UnionFind.union consumes two RecordRef values and produces
    #           None.
    # Purpose: union(a, b) joins the groups containing a and b.
    # Effects: Changes the parent links stored by this _UnionFind.
    def union(self, a: RecordRef, b: RecordRef) -> None:
        """Join the groups containing two records."""

        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self.parent[root_b] = root_a


# Contract: _build_groups consumes list[RecordRef], _UnionFind, and
#           dict[tuple[int, int], float] and produces list[MatchGroup].
# Purpose: _build_groups(refs, union_find, scores) converts connected match
#           edges into sorted groups for manual review.
# Examples:
# _build_groups(refs, union_find, scores) => [MatchGroup(...)]
def _build_groups(
    refs: list[RecordRef],
    union_find: _UnionFind,
    scores: dict[tuple[int, int], float],
) -> list[MatchGroup]:
    """Create sorted review groups from the connected match components."""

    buckets: dict[RecordRef, list[RecordRef]] = {}
    position = {ref: index for index, ref in enumerate(refs)}
    for ref in refs:
        buckets.setdefault(union_find.find(ref), []).append(ref)

    groups: list[MatchGroup] = []
    for records in buckets.values():
        if len(records) < 2:
            continue
        ids = {position[ref] for ref in records}
        group_scores = [score for pair, score in scores.items() if pair[0] in ids and pair[1] in ids]
        score = min(group_scores) if group_scores else 100.0
        reason = "Exact after normalization" if group_scores and all(value == 100 for value in group_scores) else "Fuzzy token similarity"
        groups.append(MatchGroup(records, round(score, 1), [reason]))
    groups.sort(key=lambda group: (-group.score, group.records[0].index))
    return groups


# ============================================================================
# Stage 6: public scan entry points
# Purpose: orchestrate the complete matching pipeline for single-file and
# cross-file workspaces. Each entry point follows the same sequence:
# prepare values -> score candidate edges -> connect records -> build groups.
# ============================================================================
# Contract: find_single_file_groups consumes list[dict[str, str]], list[str] | str,
#           and Ruleset and produces list[MatchGroup].
# Purpose: find_single_file_groups(rows, columns, rules) finds likely duplicate
#           groups within one CSV source.
# Examples:
# find_single_file_groups(rows, ["Name"], Ruleset()) => [MatchGroup(...)]
def find_single_file_groups(
    rows: list[dict[str, str]],
    columns: list[str] | str,
    rules: Ruleset,
) -> list[MatchGroup]:
    """Find duplicate groups within one CSV source."""

    values = [normalize(value, rules) for value in _combined_values(rows, columns)]
    refs = [RecordRef("single", index) for index in range(len(rows))]
    union_find = _UnionFind(refs)
    edge_scores = _score_candidate_edges(values, values, rules, same_source=True)
    for (left, right), _score in edge_scores.items():
        union_find.union(refs[left], refs[right])
    return _build_groups(refs, union_find, edge_scores)


# Contract: find_cross_file_groups consumes two list[dict[str, str]] values,
#           two list[str] | str values, and Ruleset, and produces list[MatchGroup].
# Purpose: find_cross_file_groups(truth_rows, truth_columns, dependent_rows,
#           dependent_columns, rules) finds likely matches across two CSVs.
# Examples:
# find_cross_file_groups(truth_rows, ["Name"], dependent_rows, ["Customer"],
#                        Ruleset()) => [MatchGroup(...)]
def find_cross_file_groups(
    truth_rows: list[dict[str, str]],
    truth_columns: list[str] | str,
    dependent_rows: list[dict[str, str]],
    dependent_columns: list[str] | str,
    rules: Ruleset,
) -> list[MatchGroup]:
    """Find matching groups between source-of-truth and dependent CSVs."""

    left_values = [normalize(value, rules) for value in _combined_values(truth_rows, truth_columns)]
    right_values = [normalize(value, rules) for value in _combined_values(dependent_rows, dependent_columns)]
    left_refs = [RecordRef("truth", index) for index in range(len(truth_rows))]
    right_refs = [RecordRef("dependent", index) for index in range(len(dependent_rows))]
    refs = left_refs + right_refs
    union_find = _UnionFind(refs)
    local_scores = _score_candidate_edges(left_values, right_values, rules)
    edge_scores = {
        (left, len(left_values) + right): score
        for (left, right), score in local_scores.items()
    }
    for (left, right), _score in local_scores.items():
        union_find.union(left_refs[left], right_refs[right])
    return _build_groups(refs, union_find, edge_scores)
