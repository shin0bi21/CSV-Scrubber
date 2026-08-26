from __future__ import annotations

import json
import threading
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox

from engine import (
    MatchGroup, RecordRef, analyze_tokens, find_cross_file_groups,
    find_single_file_groups, read_csv, write_csv,
)

from . import shell, views, widgets


class AppEvents:
    """User-triggered actions and application event handlers."""

    # ========================================================================
    # Navigation events
    # Purpose: switch screens and keep the application shell in sync.
    # UI work: update navigation state and call the appropriate view renderer.
    # ========================================================================
    def show_workspace(self, mode: str | None = None):
        """Open the setup screen, optionally switching its scan mode."""
        mode = mode or (self.scan_mode if self.scan_mode in ("single", "multi") else "single")
        self.mode = mode
        self.scan_mode = mode
        shell.set_nav(self, "workspace")
        views.render_workspace(self, mode)

    def show_review(self):
        shell.set_nav(self, "review")
        views.render_review(self)

    def show_complete(self):
        shell.set_nav(self, "review")
        views.render_complete(self)

    def show_rules(self):
        self.mode = "rules"
        shell.set_nav(self, "rules")
        views.render_rules(self)

    # ========================================================================
    # Input and scan events
    # Purpose: load CSV sources, validate scan inputs, and start engine work.
    # UI work: file dialogs, progress overlays, and scan-result notifications.
    # ========================================================================
    def load_source(self, source, path_var: tk.StringVar):
        path = filedialog.askopenfilename(title="Choose CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            headers, rows = read_csv(path)
        except Exception as exc:
            messagebox.showerror("Could not open CSV", str(exc))
            return
        source.path, source.headers, source.rows = path, headers, rows
        source.match_columns = []
        source.reference_columns = []
        self.token_stats = []
        self.rules.token_weights.clear()
        path_var.set(path)
        views.render_workspace(self, self.scan_mode)

    def apply_column_selection(self, source, role: str, selected_columns: list[str]):
        """Map a column-picker role to engine state and rehydrate Setup."""
        attribute = {"match": "match_columns", "reference": "reference_columns"}[role]
        setattr(source, attribute, selected_columns)
        views.render_workspace(self, self.scan_mode)

    def start_scan(self, mode: str):
        self.mode = mode
        self.scan_mode = mode
        needed = [self.single] if mode == "single" else [self.truth, self.dependent]
        if any(not source.rows or not source.match_columns for source in needed):
            messagebox.showwarning("Choose input", "Choose each CSV and at least one match column first.")
            return
        try:
            self._apply_token_weight_inputs()
        except (AttributeError, tk.TclError, ValueError):
            messagebox.showwarning("Invalid token weight", "Token weights must be numbers from 0 to 1, or use auto.")
            return
        overlay = widgets.progress_overlay(self)

        def work():
            try:
                if mode == "single":
                    result = find_single_file_groups(self.single.rows, self.single.match_columns, self.rules)
                else:
                    result = find_cross_file_groups(self.truth.rows, self.truth.match_columns, self.dependent.rows, self.dependent.match_columns, self.rules)
                self.after(0, lambda result=result: (overlay.destroy(), self._scan_done(result)))
            except Exception as exc:
                self.after(0, lambda exc=exc: messagebox.showerror("Scan failed", str(exc)))
                self.after(0, overlay.destroy)

        threading.Thread(target=work, daemon=True).start()

    def _scan_done(self, groups: list[MatchGroup]):
        self.groups, self.group_index, self.decisions = groups, 0, {}
        if not groups:
            messagebox.showinfo("No matches", "No likely duplicates met the current review threshold.")
            return
        self.show_review()

    # ========================================================================
    # Review events
    # Purpose: translate review controls into decisions for the current groups.
    # UI work: read Tk variables, show validation messages, and navigate onward.
    # ========================================================================
    def _canonical_from_ui(self, group: MatchGroup, selected: list[RecordRef]) -> dict[str, str]:
        """Read field selections from the review controls."""
        canonical: dict[str, str] = {}
        selected_refs = set(selected)
        preferred = next((ref for ref in selected if ref.source == "truth"), selected[0])
        for ref in selected:
            for field, value in self._row_for(ref).items():
                if field not in canonical or not canonical[field]:
                    canonical[field] = value
        for field, var in self.field_vars.items():
            source, idx = var.get().split(":", 1)
            chosen = RecordRef(source, int(idx))
            if chosen not in selected_refs:
                chosen = preferred if self._row_for(preferred).get(field, "") else next((ref for ref in selected if self._row_for(ref).get(field, "")), preferred)
            canonical[field] = self._row_for(chosen).get(field, "")
        return canonical

    def resolve(self, action: str):
        """Record a manual decision and advance to the next review state."""
        group = self.groups[self.group_index]
        selected = [ref for ref, var in self.keep_vars.items() if var.get()]
        if action in ("keep", "merge") and not selected:
            messagebox.showwarning("Select rows", "Select at least one row first.")
            return
        self.decisions[self.group_index] = {
            "action": action,
            "selected": selected,
            "canonical": self._canonical_from_ui(group, selected) if action == "merge" else None,
        }
        if self.group_index + 1 < len(self.groups):
            self.group_index += 1
            self.show_review()
        else:
            self.show_complete()

    # ========================================================================
    # Export events
    # Purpose: write cleaned results and the audit log through user-selected paths.
    # ========================================================================
    def export_results(self):
        unresolved = [index + 1 for index in range(len(self.groups)) if index not in self.decisions]
        if unresolved:
            messagebox.showwarning("Review incomplete", "Resolve every duplicate group before exporting.")
            return
        path = filedialog.asksaveasfilename(title="Save cleaned CSV", defaultextension=".csv", initialfile="cleaned.csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        headers, rows, audit = self._build_export()
        try:
            write_csv(path, headers, rows)
            audit_path = str(Path(path).with_name(Path(path).stem + "_audit.csv"))
            write_csv(audit_path, ["group", "score", "action", "records"], audit)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Export complete", f"Saved:\n{path}\n{audit_path}")

    # ========================================================================
    # Workspace matching setup events
    # Purpose: analyze common tokens in the selected workspace columns and save or export matching configuration.
    # ========================================================================
    def open_common_token_analysis(self):
        dialog = tk.Toplevel(self)
        dialog.transient(self)
        dialog.grab_set()
        self.common_token_dialog = dialog
        views.render_common_token_dialog(self, dialog)
        self.analyze_common_tokens()

    def analyze_common_tokens(self):
        try:
            self._apply_token_weight_inputs()
        except (AttributeError, tk.TclError, ValueError):
            messagebox.showwarning("Invalid token weight", "Token weights must be numbers from 0 to 1, or use auto.")
            return

        needed = [self.single] if self.scan_mode == "single" else [self.truth, self.dependent]
        if any(not source.rows or not source.match_columns for source in needed):
            messagebox.showwarning("Choose input", "Choose each CSV and at least one match column first.")
            return

        self.token_stats = analyze_tokens(self._matching_values(), self.rules)
        dialog = getattr(self, "common_token_dialog", None)
        if dialog is not None and dialog.winfo_exists():
            views.render_common_token_dialog(self, dialog)

    def save_rules(self) -> bool:
        review = self.review_var.get()
        try:
            review = int(review)
        except (AttributeError, tk.TclError, ValueError):
            messagebox.showwarning("Invalid ruleset", "Thresholds must be whole numbers.")
            return False
        self.rules.review_threshold = review
        for attr, var in self.norm_vars.items():
            setattr(self.rules, attr, var.get())
        messagebox.showinfo("Rules saved", "The fuzzy ruleset is active for new scans.")
        return True

    def _apply_token_weight_inputs(self):
        for token, var in getattr(self, "token_weight_vars", {}).items():
            value = var.get().strip().lower()
            if value in ("", "auto"):
                self.rules.token_weights.pop(token, None)
                continue
            self.rules.token_weights[token] = min(1.0, max(0.0, float(value)))

    def export_rules(self):
        if not self.save_rules():
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="csv_scrubber_rules.json", filetypes=[("JSON", "*.json")])
        if path:
            exported_rules = asdict(self.rules)
            exported_rules.pop("common_token_min_documents", None)
            exported_rules.pop("token_weights", None)
            Path(path).write_text(json.dumps({"algorithm": "soft_weighted_token_matching", **exported_rules}, indent=2), encoding="utf-8")
