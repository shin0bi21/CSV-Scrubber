from __future__ import annotations

from typing import Iterable

from ._01_types import MatchEvidence, MatchGroup, RecordRef


class UnionFind:
    """Track connected records while accepted match edges are added."""

    def __init__(self, nodes: Iterable[RecordRef]):
        self.parent = {node: node for node in nodes}

    def find(self, node: RecordRef) -> RecordRef:
        """Return a record's group root and compress its parent path."""

        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[node] != node:
            node, self.parent[node] = self.parent[node], root
        return root

    def union(self, left: RecordRef, right: RecordRef) -> None:
        """Join the groups containing two records."""

        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def group_has_missing_direct_pair(
    records: list[RecordRef],
    position: dict[RecordRef, int],
    scores: dict[tuple[int, int], MatchEvidence],
) -> bool:
    """Return whether connected records lack a direct accepted edge."""

    for index, left_ref in enumerate(records):
        for right_ref in records[index + 1:]:
            if left_ref.source == right_ref.source:
                pair = tuple(sorted((position[left_ref], position[right_ref])))
            elif {left_ref.source, right_ref.source} == {"truth", "dependent"}:
                truth_ref = left_ref if left_ref.source == "truth" else right_ref
                dependent_ref = left_ref if left_ref.source == "dependent" else right_ref
                pair = (position[truth_ref], position[dependent_ref])
            else:
                continue
            if pair not in scores:
                return True
    return False


def build_groups(
    refs: list[RecordRef],
    union_find: UnionFind,
    scores: dict[tuple[int, int], MatchEvidence],
    exact_pairs: set[tuple[int, int]] | None = None,
) -> list[MatchGroup]:
    """Convert connected accepted edges into sorted review groups."""

    buckets: dict[RecordRef, list[RecordRef]] = {}
    position = {ref: index for index, ref in enumerate(refs)}
    for ref in refs:
        buckets.setdefault(union_find.find(ref), []).append(ref)

    exact_pairs = exact_pairs or set()
    groups: list[MatchGroup] = []
    for records in buckets.values():
        if len(records) < 2:
            continue
        ids = {position[ref] for ref in records}
        group_evidence = {
            pair: evidence
            for pair, evidence in scores.items()
            if pair[0] in ids and pair[1] in ids
        }
        score = min(
            (evidence.score for evidence in group_evidence.values()),
            default=100.0,
        )
        group_pairs = set(group_evidence)
        reasons: list[str] = []
        if group_pairs and group_pairs <= exact_pairs:
            reasons.append("Exact after normalization")
        else:
            if any(
                evidence.exact_token_matches
                and not evidence.fuzzy_token_matches
                and (evidence.unmatched_left_tokens or evidence.unmatched_right_tokens)
                and (
                    not evidence.unmatched_left_tokens
                    or not evidence.unmatched_right_tokens
                )
                for evidence in group_evidence.values()
            ):
                reasons.append("Exact name contained in longer name")
            if any(
                len(evidence.exact_token_matches) >= 2
                for evidence in group_evidence.values()
            ):
                reasons.append("Multiple exact tokens matched")
            if any(
                len(evidence.fuzzy_token_matches) == 1
                for evidence in group_evidence.values()
            ):
                reasons.append("Single fuzzy token matched")
            if any(
                evidence.fuzzy_token_matches
                for evidence in group_evidence.values()
            ):
                reasons.append("Spelling variation")
            if len(records) > 2 and group_has_missing_direct_pair(
                records,
                position,
                scores,
            ):
                reasons.append("Connected through another candidate")
            if not reasons:
                reasons.append("Fuzzy token similarity")

        groups.append(MatchGroup(
            records=records,
            score=round(score, 1),
            reasons=reasons,
            evidence={
                (refs[pair[0]], refs[pair[1]]): evidence
                for pair, evidence in group_evidence.items()
            },
        ))
    groups.sort(key=lambda group: (-group.score, group.records[0].index))
    return groups
