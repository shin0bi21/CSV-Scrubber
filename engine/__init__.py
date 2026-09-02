"""Public interface for CSV I/O and the matching pipeline."""

from csv_io import read_csv, write_csv

from ._01_types import MatchEvidence, MatchGroup, RecordRef, Ruleset, TokenStat
from ._02_normalization import normalize
from ._03_weights import analyze_tokens
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
