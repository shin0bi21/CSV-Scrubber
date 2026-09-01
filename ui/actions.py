"""Semantic user actions for the PySide6 application."""

from __future__ import annotations

import json
from dataclasses import asdict
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
        needed = (
            [self.single]
            if self.scan_mode == "single"
            else [self.truth, self.dependent]
        )
        if all(source.rows and source.match_columns for source in needed):
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
        source.path = path
        source.headers = headers
        source.rows = rows
        source.match_columns = []
        source.reference_columns = []
        self.token_stats = []
        self.rules.token_weights.clear()
        self.token_weight_drafts.clear()
        views.render_workspace(self, self.scan_mode)

    def apply_column_selection(
        self,
        source,
        attribute: str,
        selected_columns: list[str],
    ) -> None:
        setattr(source, attribute, selected_columns)
        views.render_workspace(self, self.scan_mode)

    def start_scan(self, mode: str) -> None:
        self.mode = mode
        self.scan_mode = mode
        needed = (
            [self.single]
            if mode == "single"
            else [self.truth, self.dependent]
        )
        if any(not source.rows or not source.match_columns for source in needed):
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

        if mode == "single":
            work = lambda: find_single_file_groups(
                self.single.rows,
                self.single.match_columns,
                self.rules,
            )
        else:
            work = lambda: find_cross_file_groups(
                self.truth.rows,
                self.truth.match_columns,
                self.dependent.rows,
                self.dependent.match_columns,
                self.rules,
            )
        self._scan_progress = widgets.progress_dialog(
            self,
            "Finding likely duplicates…",
        )
        worker = ScanWorker(work)
        self._scan_worker = worker
        worker.signals.finished.connect(self._scan_finished)
        worker.signals.failed.connect(self._scan_failed)
        QThreadPool.globalInstance().start(worker)

    @Slot(object)
    def _scan_finished(self, groups: list[MatchGroup]) -> None:
        self._close_scan_progress()
        self.groups = groups
        self.group_index = 0
        self.decisions = {}
        if not groups:
            QMessageBox.information(
                self,
                "No matches",
                "No likely duplicates met the current review threshold.",
            )
            return
        self.show_review()

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
        canonical: dict[str, str] = {}
        selected_refs = set(selected)
        preferred = next(
            (ref for ref in selected if ref.source == "truth"),
            selected[0],
        )
        edited_rows = {
            ref: self._edited_row_from_ui(ref) for ref in selected
        }
        for ref in selected:
            for field, value in edited_rows[ref].items():
                if field not in canonical or not canonical[field]:
                    canonical[field] = value

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
        self.decisions[self.group_index] = {
            "action": action,
            "selected": selected,
            "canonical": (
                self._canonical_from_ui(group, selected)
                if action == "merge"
                else None
            ),
            "edits": edits,
        }
        if self.group_index + 1 < len(self.groups):
            self.group_index += 1
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
        needed = (
            [self.single]
            if self.scan_mode == "single"
            else [self.truth, self.dependent]
        )
        if any(not source.rows or not source.match_columns for source in needed):
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
        self.rules.common_token_min_documents = (
            self.common_token_min_documents_input.value()
        )
        for attribute, control in self.norm_inputs.items():
            setattr(self.rules, attribute, control.isChecked())

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
