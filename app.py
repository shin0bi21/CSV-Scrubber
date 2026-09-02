from __future__ import annotations

import sys
from dataclasses import dataclass, field

from PySide6.QtWidgets import QApplication, QMainWindow

from engine import MatchGroup, RecordRef, Ruleset, TokenStat
from ui import shell
from ui.actions import AppActions, ReviewDecision


@dataclass
class CSVSource:
    """Loaded CSV state used by the application."""

    role: str
    path: str = ""
    headers: list[str] = field(default_factory=list)
    rows: list[dict[str, str]] = field(default_factory=list)
    match_columns: list[str] = field(default_factory=list)
    reference_columns: list[str] = field(default_factory=list)

    @property
    def review_columns(self) -> list[str]:
        return self.match_columns + self.reference_columns

    def matching_values(self) -> list[str]:
        return [
            row[column]
            for row in self.rows
            for column in self.match_columns
            if row[column]
        ]

    def replace_data(
        self,
        path: str,
        headers: list[str],
        rows: list[dict[str, str]],
    ) -> None:
        self.path = path
        self.headers = headers
        self.rows = rows
        self.match_columns.clear()
        self.reference_columns.clear()

    def refs(self) -> list[RecordRef]:
        return [
            RecordRef(self.role, index)
            for index in range(len(self.rows))
        ]

    def field_editable(self, field: str) -> bool:
        return self.role in ("single", "truth") and field in self.match_columns


class ScrubberApp(AppActions, QMainWindow):
    """Application composition, initialization, and shared state."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CSV Scrubber")
        self.resize(1320, 860)
        self.setMinimumSize(1040, 700)

        self.rules = Ruleset()
        self.single = CSVSource("single")
        self.truth = CSVSource("truth")
        self.dependent = CSVSource("dependent")
        self.sources = {
            source.role: source
            for source in (self.single, self.truth, self.dependent)
        }
        self.mode = "single"
        self.scan_mode = "single"
        self.groups: list[MatchGroup] = []
        self.group_index = 0
        self.decisions: dict[int, ReviewDecision] = {}
        self.edit_inputs = {}
        self.token_stats: list[TokenStat] = []
        self.token_weight_drafts: dict[str, str] = {}

        shell.setup_styles(self)
        shell.build(self)
        self.show_workspace()

    def _row_for(self, ref: RecordRef) -> dict[str, str]:
        return self.sources[ref.source].rows[ref.index]

    def _sources_for_mode(self, mode: str) -> tuple[CSVSource, ...]:
        return (
            (self.single,)
            if mode == "single"
            else (self.truth, self.dependent)
        )

    def _headers_for_review(self, group: MatchGroup) -> list[str]:
        headers: list[str] = []
        for ref in group.records:
            source = self.sources[ref.source]
            for header in source.review_columns:
                if header not in headers:
                    headers.append(header)
        return headers

    def _review_field_editable(self, ref: RecordRef, field: str) -> bool:
        return self.sources[ref.source].field_editable(field)

    def _matching_values(self) -> list[str]:
        return [
            value
            for source in self._sources_for_mode(self.scan_mode)
            for value in source.matching_values()
        ]

    def _export_scope(self) -> tuple[list[str], list[RecordRef]]:
        if self.mode == "single":
            return list(self.single.headers), self.single.refs()
        headers = list(self.truth.headers) + [
            header
            for header in self.dependent.headers
            if header not in self.truth.headers
        ]
        return headers, self.truth.refs() + self.dependent.refs()

    def _export_changes(
        self,
    ) -> tuple[
        set[RecordRef],
        dict[RecordRef, dict[str, str]],
        list[dict[str, str]],
        list[dict[str, str]],
    ]:
        removed: set[RecordRef] = set()
        edited_rows: dict[RecordRef, dict[str, str]] = {}
        replacements: list[dict[str, str]] = []
        audit: list[dict[str, str]] = []
        for index, group in enumerate(self.groups):
            decision = self.decisions.get(index)
            if decision:
                edited_rows.update(decision.edits)
            if not decision or decision.action == "not_duplicate":
                action = "not_duplicate" if decision else "unreviewed"
            elif decision.action == "keep":
                selected = set(decision.selected)
                removed.update(
                    ref for ref in group.records if ref not in selected
                )
                action = "keep_selected"
            else:
                removed.update(group.records)
                replacements.append(decision.canonical)
                action = (
                    "auto_accept"
                    if decision.action == "auto_accept"
                    else "merge"
                )
            audit.append(self._audit_entry(index, group, action))
        return removed, edited_rows, replacements, audit

    @staticmethod
    def _audit_entry(
        index: int,
        group: MatchGroup,
        action: str,
    ) -> dict[str, str]:
        return {
            "group": str(index + 1),
            "score": str(group.score),
            "action": action,
            "records": "; ".join(
                f"{ref.source}:row {ref.index + 2}"
                for ref in group.records
            ),
        }

    def _build_export(self):
        headers, refs = self._export_scope()
        removed, edited_rows, replacements, audit = self._export_changes()
        output = [
            dict(edited_rows.get(ref, self._row_for(ref)))
            for ref in refs
            if ref not in removed
        ] + replacements
        return headers, output, audit


def main() -> int:
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("CSV Scrubber")
    qt_app.setStyle("Fusion")
    window = ScrubberApp()
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
