"""Public interface for CSV I/O and the matching pipeline."""

from csv_io import read_csv, write_csv

from ._01_types import MatchEvidence, MatchGroup, RecordRef, Ruleset, TokenStat
from ._02_normalization import normalize, selected_values as _selected_values
from ._03_weights import (
    analyze_tokens,
    automatic_token_weight as _automatic_token_weight,
    build_token_weights as _build_token_weights,
    token_document_frequencies as _token_document_frequencies,
)
from ._04_candidates import (
    as_columns as _as_columns,
    blocking_keys as _blocking_keys,
    candidate_pairs as _candidate_pairs,
    value_has_content as _value_has_content,
)
from ._05_scoring import (
    column_aware_score as _column_aware_score,
    score_candidate_edges as _score_candidate_edges,
    sequence_ratio as _sequence_ratio,
    token_ratio as _token_ratio,
    weighted_token_score as _weighted_token_token_score,
)
from ._06_grouping import (
    UnionFind as _UnionFind,
    build_groups as _build_groups,
    group_has_missing_direct_pair as _group_has_missing_direct_pair,
)
from ._07_scans import find_cross_file_groups, find_single_file_groups


__all__ = [
    "MatchEvidence",
    "MatchGroup",
    "RecordRef",
    "Ruleset",
    "TokenStat",
    "analyze_tokens",
    "find_cross_file_groups",
    "find_single_file_groups",
    "normalize",
    "read_csv",
    "write_csv",
]
