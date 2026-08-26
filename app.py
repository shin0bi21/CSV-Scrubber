from __future__ import annotations

import tkinter as tk

from engine import MatchGroup, RecordRef, Ruleset, TokenStat
from ui import shell, widgets
from ui.events import AppEvents


class CSVSource:
    """Loaded CSV state used by the application."""

    def __init__(self, role: str):
        self.role = role
        self.path = ""
        self.headers: list[str] = []
        self.rows: list[dict[str, str]] = []
        self.match_columns: list[str] = []
        self.reference_columns: list[str] = []
        self._column_pickers: dict[str, tk.Frame] = {}


class ScrubberApp(AppEvents, tk.Tk):
    """Application composition, initialization, and shared state."""

    def __init__(self):
        super().__init__()
        self.title("CSV Scrubber")
        self.geometry("1260x820")
        self.minsize(980, 680)
        self.configure(bg=widgets.COLORS["bg"])

        self.rules = Ruleset()
        self.single = CSVSource("single")
        self.truth = CSVSource("truth")
        self.dependent = CSVSource("dependent")
        self.mode = "single"
        self.scan_mode = "single"
        self.groups: list[MatchGroup] = []
        self.group_index = 0
        self.decisions: dict[int, dict] = {}
        self.token_stats: list[TokenStat] = []
        self.token_weight_vars: dict[str, tk.StringVar] = {}

        shell.setup_styles(self)
        shell.build(self)
        self.show_import("single")

    # Application state and data helpers
    def _row_for(self, ref: RecordRef) -> dict[str, str]:
        if ref.source == "single":
            return self.single.rows[ref.index]
        if ref.source == "truth":
            return self.truth.rows[ref.index]
        return self.dependent.rows[ref.index]

    def _headers_for_review(self, group: MatchGroup) -> list[str]:
        headers: list[str] = []
        for ref in group.records:
            source = self.single if ref.source == "single" else self.truth if ref.source == "truth" else self.dependent
            for header in source.match_columns + source.reference_columns:
                if header not in headers:
                    headers.append(header)
        return headers

    def _matching_values(self) -> list[str]:
        def combined_value(row: dict[str, str], columns: list[str]) -> str:
            return " ".join(row.get(column, "") for column in columns).strip()

        if self.scan_mode == "single":
            return [combined_value(row, self.single.match_columns) for row in self.single.rows]
        return [combined_value(row, self.truth.match_columns) for row in self.truth.rows] + [
            combined_value(row, self.dependent.match_columns) for row in self.dependent.rows
        ]

    def _build_export(self):
        sources = {"single": self.single.rows, "truth": self.truth.rows, "dependent": self.dependent.rows}
        if self.mode == "single":
            headers, refs = list(self.single.headers), [RecordRef("single", index) for index in range(len(self.single.rows))]
        else:
            headers = list(self.truth.headers) + [header for header in self.dependent.headers if header not in self.truth.headers]
            refs = [RecordRef("truth", index) for index in range(len(self.truth.rows))] + [RecordRef("dependent", index) for index in range(len(self.dependent.rows))]
        removed: set[RecordRef] = set()
        replacements: list[dict[str, str]] = []
        audit: list[dict[str, str]] = []
        for index, group in enumerate(self.groups):
            decision = self.decisions.get(index)
            if not decision or decision["action"] == "not_duplicate":
                action = "not_duplicate" if decision else "unreviewed"
            elif decision["action"] == "keep":
                selected = set(decision["selected"])
                removed.update(ref for ref in group.records if ref not in selected)
                action = "keep_selected"
            else:
                removed.update(group.records)
                replacements.append(decision["canonical"])
                action = "merge"
            audit.append({"group": str(index + 1), "score": str(group.score), "action": action, "records": "; ".join(f"{ref.source}:row {ref.index + 2}" for ref in group.records)})
        output = [dict(sources[ref.source][ref.index]) for ref in refs if ref not in removed] + replacements
        return headers, output, audit

if __name__ == "__main__":
    ScrubberApp().mainloop()
