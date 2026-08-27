from __future__ import annotations

from dataclasses import replace

from .stage_00_models import MatchGroup, RecordRef, Ruleset
from .stage_01_normalization import selected_values
from .stage_04_scoring import score_candidate_edges
from .stage_05_grouping import UnionFind, build_groups


def find_single_file_groups(
    rows: list[dict[str, str]],
    columns: list[str] | str,
    rules: Ruleset,
) -> list[MatchGroup]:
    """Find likely duplicate groups within one CSV source."""

    selected_columns = [columns] if isinstance(columns, str) else list(columns)
    values = selected_values(rows, selected_columns, rules)
    refs = [RecordRef("single", index) for index in range(len(rows))]
    union_find = UnionFind(refs)
    edge_scores = score_candidate_edges(
        values,
        values,
        rules,
        same_source=True,
        column_names=selected_columns,
    )
    for left, right in edge_scores:
        union_find.union(refs[left], refs[right])
    exact_pairs = {
        pair
        for pair in edge_scores
        if values[pair[0]] == values[pair[1]]
    }
    return build_groups(refs, union_find, edge_scores, exact_pairs)


def find_cross_file_groups(
    truth_rows: list[dict[str, str]],
    truth_columns: list[str] | str,
    dependent_rows: list[dict[str, str]],
    dependent_columns: list[str] | str,
    rules: Ruleset,
) -> list[MatchGroup]:
    """Find likely matches between source-of-truth and dependent CSVs."""

    left_columns = [truth_columns] if isinstance(truth_columns, str) else list(truth_columns)
    right_columns = (
        [dependent_columns]
        if isinstance(dependent_columns, str)
        else list(dependent_columns)
    )
    left_values = selected_values(truth_rows, left_columns, rules)
    right_values = selected_values(dependent_rows, right_columns, rules)
    left_refs = [RecordRef("truth", index) for index in range(len(truth_rows))]
    right_refs = [
        RecordRef("dependent", index) for index in range(len(dependent_rows))
    ]
    refs = left_refs + right_refs
    union_find = UnionFind(refs)

    display_columns = [
        left if left == right else f"{left} / {right}"
        for left, right in zip(left_columns, right_columns)
    ]
    cross_column_weights = dict(rules.column_weights)
    for left, right, display in zip(
        left_columns,
        right_columns,
        display_columns,
    ):
        cross_column_weights[display] = rules.column_weights.get(
            display,
            rules.column_weights.get(left, rules.column_weights.get(right, 1.0)),
        )
    cross_rules = replace(rules, column_weights=cross_column_weights)
    local_scores = score_candidate_edges(
        left_values,
        right_values,
        cross_rules,
        column_names=display_columns,
    )
    offset = len(left_values)
    edge_scores = {
        (left, offset + right): evidence
        for (left, right), evidence in local_scores.items()
    }
    exact_pairs = {
        (left, offset + right)
        for left, right in local_scores
        if left_values[left] == right_values[right]
    }
    for left, right in local_scores:
        union_find.union(left_refs[left], right_refs[right])
    return build_groups(refs, union_find, edge_scores, exact_pairs)
