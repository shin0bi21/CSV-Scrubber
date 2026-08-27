"""Public interface for CSV I/O and the matching pipeline."""

from csv_io import read_csv, write_csv

from .stage_00_models import MatchEvidence, MatchGroup, RecordRef, Ruleset, TokenStat
from .stage_01_normalization import normalize, selected_values as _selected_values
from .stage_02_weights import (
    analyze_tokens,
    automatic_token_weight as _automatic_token_weight,
    build_token_weights as _build_token_weights,
    token_document_frequencies as _token_document_frequencies,
)
from .stage_03_candidates import (
    as_columns as _as_columns,
    blocking_keys as _blocking_keys,
    candidate_pairs as _candidate_pairs,
    value_has_content as _value_has_content,
)
from .stage_04_scoring import (
    column_aware_score as _column_aware_score,
    score_candidate_edges as _score_candidate_edges,
    sequence_ratio as _sequence_ratio,
    token_ratio as _token_ratio,
    weighted_token_score as _weighted_token_token_score,
)
from .stage_05_grouping import (
    UnionFind as _UnionFind,
    build_groups as _build_groups,
    group_has_missing_direct_pair as _group_has_missing_direct_pair,
)
from .stage_06_scans import find_cross_file_groups, find_single_file_groups


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
