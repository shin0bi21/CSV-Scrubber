"""Semantic user actions for the PySide6 application."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox

from engine import (
    MatchGroup,
    RecordRef,
    analyze_tokens,
    find_cross_file_groups,
    find_single_file_groups,
    read_csv,
    write_csv,
)

from . import shell, views, widgets


@dataclass
class ReviewDecision:
    action: str
    selected: list[RecordRef]
    canonical: dict[str, str]
    edits: dict[RecordRef, dict[str, str]]


class WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class ScanWorker(QRunnable):
    def __init__(self, work) -> None:
        super().__init__()
        self.work = work
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.finished.emit(self.work())
        except Exception as exc:  # UI boundary reports engine failures
            self.signals.failed.emit(str(exc))


class AppActions:
    """Actions that coordinate the views with engine and file operations."""

    def show_workspace(self, mode: str | None = None) -> None:
        mode = self.scan_mode if mode is None else mode
        self.mode = mode
        self.scan_mode = mode
        shell.set_nav(self, "setup")
        views.render_workspace(self, mode)

    def show_analyze(self) -> None:
        shell.set_nav(self, "analyze")
        if self._scan_inputs_ready(self.scan_mode):
            self.token_stats = analyze_tokens(
                self._matching_values(),
                self.rules,
            )
        views.render_analyze(self)

    def show_review(self) -> None:
        shell.set_nav(self, "review")
        views.render_review(self)

    def show_complete(self) -> None:
        shell.set_nav(self, "complete")
        views.render_complete(self)

    def show_settings(self) -> None:
        shell.set_nav(self, "settings")
        views.render_settings(self)

    def load_source(self, source) -> None:
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Choose CSV",
            "",
            "CSV files (*.csv);;All files (*.*)",
        )
        if not path:
            return
        try:
            headers, rows = read_csv(path)
        except Exception as exc:
            QMessageBox.critical(self, "Could not open CSV", str(exc))
            return
        source.replace_data(path, headers, rows)
        self.token_stats = []
        self.rules.token_weights.clear()
        self.token_weight_drafts.clear()
        views.render_workspace(self, self.scan_mode)

    def set_match_columns(
        self,
        source,
        selected_columns: list[str],
    ) -> None:
        source.match_columns = selected_columns
        views.render_workspace(self, self.scan_mode)

    def set_reference_columns(
        self,
        source,
        selected_columns: list[str],
    ) -> None:
        source.reference_columns = selected_columns
        views.render_workspace(self, self.scan_mode)

    def start_scan(self, mode: str) -> None:
        self.mode = mode
        self.scan_mode = mode
        if not self._scan_inputs_ready(mode):
            QMessageBox.warning(
                self,
                "Choose input",
                "Choose each CSV and at least one match column first.",
            )
            return
        try:
            self._apply_token_weight_inputs()
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid token weight",
                "Token weights must be numbers from 0 to 1, or use auto.",
            )
            return

        self._scan_progress = widgets.progress_dialog(
            self,
            "Finding likely duplicates…",
        )
        worker = ScanWorker(self._scan_work(mode))
        self._scan_worker = worker
        worker.signals.finished.connect(self._scan_finished)
        worker.signals.failed.connect(self._scan_failed)
        QThreadPool.globalInstance().start(worker)

    def _scan_inputs_ready(self, mode: str) -> bool:
        return all(
            source.rows and source.match_columns
            for source in self._sources_for_mode(mode)
        )

    def _scan_work(self, mode: str) -> Callable[[], list[MatchGroup]]:
        if mode == "single":
            return lambda: find_single_file_groups(
                self.single.rows,
                self.single.match_columns,
                self.rules,
            )
        return lambda: find_cross_file_groups(
            self.truth.rows,
            self.truth.match_columns,
            self.dependent.rows,
            self.dependent.match_columns,
            self.rules,
        )

    @Slot(object)
    def _scan_finished(self, groups: list[MatchGroup]) -> None:
        self._close_scan_progress()
        self.groups = groups
        self.group_index = 0
        self.decisions = self._auto_accept_decisions(groups)
        if not groups:
            QMessageBox.information(
                self,
                "No matches",
                "No likely duplicates met the current review threshold.",
            )
            return
        next_group = self._next_unresolved_group_index()
        if next_group is None:
            self.show_complete()
            return
        self.group_index = next_group
        self.show_review()

    def _auto_accept_decisions(
        self,
        groups: list[MatchGroup],
    ) -> dict[int, ReviewDecision]:
        if not self.rules.auto_accept:
            return {}
        return {
            index: self._auto_accept_decision(group)
            for index, group in enumerate(groups)
            if group.score >= self.rules.auto_accept_threshold
        }

    def _auto_accept_decision(self, group: MatchGroup) -> ReviewDecision:
        selected = list(group.records)
        edits = {ref: dict(self._row_for(ref)) for ref in selected}
        return ReviewDecision(
            action="auto_accept",
            selected=selected,
            canonical=self._canonical_from_rows(selected, edits),
            edits=edits,
        )

    def _next_unresolved_group_index(self, start: int = 0) -> int | None:
        return next(
            (
                index
                for index in range(start, len(self.groups))
                if index not in self.decisions
            ),
            None,
        )

    @Slot(str)
    def _scan_failed(self, message: str) -> None:
        self._close_scan_progress()
        QMessageBox.critical(self, "Scan failed", message)

    def _close_scan_progress(self) -> None:
        self._scan_progress.close()
        self._scan_progress.deleteLater()
        self._scan_progress = None
        self._scan_worker = None

    def _edited_row_from_ui(self, ref: RecordRef) -> dict[str, str]:
        row = dict(self._row_for(ref))
        for (edited_ref, field), control in self.edit_inputs.items():
            if (
                edited_ref == ref
                and self._review_field_editable(ref, field)
            ):
                row[field] = control.text()
        return row

    def _canonical_from_ui(
        self,
        group: MatchGroup,
        selected: list[RecordRef],
    ) -> dict[str, str]:
        selected_refs = set(selected)
        preferred = next(
            (ref for ref in selected if ref.source == "truth"),
            selected[0],
        )
        edited_rows = {
            ref: self._edited_row_from_ui(ref) for ref in selected
        }
        canonical = self._canonical_from_rows(selected, edited_rows)

        for field, chosen in self.field_choices.items():
            if chosen not in selected_refs:
                chosen = next(
                    (
                        ref
                        for ref in selected
                        if edited_rows[ref].get(field, "")
                    ),
                    preferred,
                )
            canonical[field] = edited_rows[chosen].get(field, "")
        return canonical

    @staticmethod
    def _canonical_from_rows(
        selected: list[RecordRef],
        rows: dict[RecordRef, dict[str, str]],
    ) -> dict[str, str]:
        canonical: dict[str, str] = {}
        for ref in selected:
            for field, value in rows[ref].items():
                if field not in canonical or not canonical[field]:
                    canonical[field] = value
        return canonical

    def resolve(self, action: str) -> None:
        group = self.groups[self.group_index]
        selected = [
            ref
            for ref, control in self.keep_checks.items()
            if control.isChecked()
        ]
        if action in ("keep", "merge") and not selected:
            QMessageBox.warning(
                self,
                "Select rows",
                "Select at least one row first.",
            )
            return
        edits = {
            ref: self._edited_row_from_ui(ref) for ref in group.records
        }
        self.decisions[self.group_index] = ReviewDecision(
            action=action,
            selected=selected,
            canonical=(
                self._canonical_from_ui(group, selected)
                if action == "merge"
                else {}
            ),
            edits=edits,
        )
        next_group = self._next_unresolved_group_index(self.group_index + 1)
        if next_group is not None:
            self.group_index = next_group
            self.show_review()
        else:
            self.show_complete()

    def export_results(self) -> None:
        unresolved = [
            index + 1
            for index in range(len(self.groups))
            if index not in self.decisions
        ]
        if unresolved:
            QMessageBox.warning(
                self,
                "Review incomplete",
                "Resolve every duplicate group before exporting.",
            )
            return
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save cleaned CSV",
            "cleaned.csv",
            "CSV files (*.csv)",
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        headers, rows, audit = self._build_export()
        try:
            write_csv(path, headers, rows)
            output = Path(path)
            audit_path = str(
                output.with_name(output.stem + "_audit.csv")
            )
            write_csv(
                audit_path,
                ["group", "score", "action", "records"],
                audit,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        QMessageBox.information(
            self,
            "Export complete",
            f"Saved:\n{path}\n{audit_path}",
        )

    def analyze_common_tokens(self) -> None:
        try:
            self._apply_token_weight_inputs()
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid token weight",
                "Token weights must be numbers from 0 to 1, or use auto.",
            )
            return
        if not self._scan_inputs_ready(self.scan_mode):
            QMessageBox.warning(
                self,
                "Choose input",
                "Choose each CSV and at least one match column first.",
            )
            return
        self.token_stats = analyze_tokens(
            self._matching_values(),
            self.rules,
        )
        views.render_analyze(self)

    def _store_rules(self) -> None:
        self.rules.review_threshold = self.review_input.value()
        self.rules.auto_accept = self.auto_accept_input.isChecked()
        self.rules.auto_accept_threshold = (
            self.auto_accept_threshold_input.value()
        )
        self.rules.common_token_min_documents = (
            self.common_token_min_documents_input.value()
        )
        self.rules.lowercase = self.lowercase_input.isChecked()
        self.rules.remove_punctuation = (
            self.remove_punctuation_input.isChecked()
        )

    def save_rules(self) -> None:
        self._store_rules()
        QMessageBox.information(
            self,
            "Settings saved",
            "The matching settings are active for new scans.",
        )

    def _apply_token_weight_inputs(self) -> None:
        for token, value in self.token_weight_drafts.items():
            value = value.strip().lower()
            if value in ("", "auto"):
                self.rules.token_weights.pop(token, None)
                continue
            weight = float(value)
            if not 0 <= weight <= 1:
                raise ValueError
            self.rules.token_weights[token] = weight

    def export_rules(self) -> None:
        self._store_rules()
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export matching settings",
            "csv_scrubber_rules.json",
            "JSON files (*.json)",
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        exported_rules = asdict(self.rules)
        exported_rules.pop("token_weights", None)
        Path(path).write_text(
            json.dumps(
                {
                    "algorithm": "soft_weighted_token_matching",
                    **exported_rules,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
