from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Ruleset:
    """User-controlled normalization, weighting, and review settings."""

    review_threshold: int = 82
    auto_accept: bool = False
    auto_accept_threshold: int = 95
    lowercase: bool = True
    remove_punctuation: bool = True
    common_token_min_documents: int = 3
    token_weights: dict[str, float] = field(default_factory=dict)
    column_weights: dict[str, float] = field(default_factory=dict)
    candidate_strategy: str = "auto"
    exhaustive_pair_limit: int = 2_000_000
    blocking_ngram_size: int = 3


@dataclass(frozen=True)
class RecordRef:
    """Identify a source row without copying row data into a match group."""

    source: str
    index: int


@dataclass(frozen=True)
class MatchEvidence:
    """Explain the token-level evidence behind one candidate score."""

    score: float
    exact_token_matches: tuple[tuple[str, str], ...] = ()
    fuzzy_token_matches: tuple[tuple[str, str, float], ...] = ()
    unmatched_left_tokens: tuple[str, ...] = ()
    unmatched_right_tokens: tuple[str, ...] = ()
    shorter_name_coverage: float = 0.0
    longer_name_coverage: float = 0.0


@dataclass
class MatchGroup:
    """A connected set of records that requires manual review."""

    records: list[RecordRef]
    score: float
    reasons: list[str] = field(default_factory=list)
    evidence: dict[tuple[RecordRef, RecordRef], MatchEvidence] = field(default_factory=dict)


@dataclass(frozen=True)
class TokenStat:
    """Frequency and weighting information shown in token analysis."""

    token: str
    count: int
    percentage: float
    automatic_weight: float
    weight: float
    examples: tuple[str, ...]
