from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from engine import MatchGroup, RecordRef

from . import widgets


_COLUMN_PICKER_CONFIG = {
    "match": {
        "attribute": "match_columns",
        "label": "Match columns",
        "popup_title": "Choose match columns",
        "popup_subtitle": "Selected values are combined per row before fuzzy matching.",
    },
    "reference": {
        "attribute": "reference_columns",
        "label": "Reference columns",
        "popup_title": "Choose reference columns",
        "popup_subtitle": "These columns provide supporting context but do not affect the match score.",
    },
}


def _render_column_picker(app, frame, source, row: int, role: str):
    """Hydrate the shared column picker with source-specific view data."""
    config = _COLUMN_PICKER_CONFIG[role]
    attribute = config["attribute"]
    widgets.column_picker(
        frame,
        config["label"],
        row,
        columns=source.headers,
        selected_columns=getattr(source, attribute),
        popup_title=config["popup_title"],
        popup_subtitle=config["popup_subtitle"],
        on_apply=lambda selected, source=source, role=role: app.apply_column_selection(source, role, selected),
    )


# ============================================================================
# Setup view
# ============================================================================
def render_workspace(app, mode: str):
    """Render Setup and its selected single-file or multi-file mode."""
    app.crumb.configure(text=f"Setup  ›  {'Single file' if mode == 'single' else 'Multi-file'}")
    outer = widgets.page(app, "Setup", "Choose the files and columns for this duplicate scan.")

    mode_bar = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    mode_bar.pack(fill="x", pady=(0, 18))
    ctk.CTkLabel(mode_bar, text="SCAN MODE", text_color=widgets.COLORS["muted"], font=widgets.FONTS["section"], anchor="w").pack(side="left", padx=(0, 14))

    def select_mode(label: str):
        app.show_workspace("single" if label == "Single file" else "multi")

    mode_control = ctk.CTkSegmentedButton(
        mode_bar,
        values=["Single file", "Multi-file"],
        command=select_mode,
        fg_color=widgets.COLORS["panel_alt"],
        selected_color=widgets.COLORS["green_light"],
        selected_hover_color=widgets.COLORS["truth_header"],
        unselected_color=widgets.COLORS["paper"],
        unselected_hover_color=widgets.COLORS["panel_subtle"],
        text_color=widgets.COLORS["ink"],
        font=widgets.FONTS["button_small"],
        height=38,
        corner_radius=9,
    )
    mode_control.pack(side="left")
    mode_control.set("Single file" if mode == "single" else "Multi-file")

    if mode == "single":
        _render_single_import(app, outer)
    else:
        _render_multi_import(app, outer)


def _render_single_import(app, outer):
    ctk.CTkLabel(outer, text="Find duplicates in one CSV", text_color=widgets.COLORS["ink"], font=widgets.FONTS["card_title"], anchor="w").pack(fill="x", pady=(0, 10))
    frame = widgets.card(outer)
    frame.pack_configure(fill="both", expand=True)
    widgets.source_picker(app, frame, app.single, "CSV file", 0)
    _render_column_picker(app, frame, app.single, 1, "match")
    _render_column_picker(app, frame, app.single, 2, "reference")
    frame.grid_rowconfigure(3, weight=1)
    _render_scan_action(frame, lambda: app.start_scan("single"), 4)


def _render_multi_import(app, outer):
    ctk.CTkLabel(outer, text="Reconcile two CSV sources", text_color=widgets.COLORS["ink"], font=widgets.FONTS["card_title"], anchor="w").pack(fill="x", pady=(0, 10))
    sources = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    sources.pack(fill="x")
    _render_source_card(app, sources, app.truth, "SOURCE OF TRUTH", "Truth CSV", widgets.COLORS["truth_header"], (0, 8))
    _render_source_card(app, sources, app.dependent, "DEPENDENT SOURCE", "Dependent CSV", widgets.COLORS["panel_alt"], (8, 0))

    footer = widgets.card(outer)
    footer.pack_configure(fill="both", expand=True)
    footer.grid_rowconfigure(0, weight=1)
    _render_scan_action(footer, lambda: app.start_scan("multi"), 1)


def _render_scan_action(parent, command, row: int):
    actions = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    actions.grid(row=row, column=0, columnspan=3, sticky="ew", padx=22, pady=(16, 22))
    widgets.button(actions, "Scan for duplicates", command, "primary").pack(side="right")


def _render_source_card(app, parent, source, section_text, file_label, header_bg, padding):
    frame = widgets.card(parent)
    frame.pack_forget()
    frame.pack(side="left", fill="both", expand=True, padx=padding)
    widgets.section_label(frame, section_text, header_bg, widgets.COLORS["green"] if source.role == "truth" else widgets.COLORS["muted"], row=0, column=0, columnspan=3, sticky="w", padx=22, pady=(20, 8))
    widgets.source_picker(app, frame, source, file_label, 1)
    _render_column_picker(app, frame, source, 2, "match")
    _render_column_picker(app, frame, source, 3, "reference")


# ============================================================================
# Review view
# ============================================================================
def render_review(app):
    """Render the current duplicate group for manual resolution."""
    app.crumb.configure(text=f"Review  ›  {'Single-file' if app.scan_mode == 'single' else 'Multi-file'}")
    outer = widgets.page(app, "Review", "Select rows to keep, or choose field values for a merged record.")

    if not app.groups:
        frame = widgets.card(outer)
        ctk.CTkLabel(frame, text="No review is ready yet", text_color=widgets.COLORS["ink"], font=widgets.FONTS["card_title"], anchor="w").pack(fill="x", padx=22, pady=(22, 6))
        ctk.CTkLabel(frame, text="Run a scan from Setup first.", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body"], anchor="w").pack(fill="x", padx=22, pady=(0, 18))
        widgets.button(frame, "Back to Setup", app.show_workspace, "secondary").pack(anchor="w", padx=22, pady=(0, 22))
        return

    group: MatchGroup = app.groups[app.group_index]
    _build_group_header(app, outer, group)
    review_frame = ctk.CTkFrame(outer, fg_color=widgets.COLORS["paper"], border_color=widgets.COLORS["line"], border_width=1, corner_radius=14)
    review_frame.pack(fill="both", expand=True)
    _build_reason_bar(review_frame, group)
    table = widgets.scrollable_frame(review_frame)
    _build_record_columns(app, table, group)
    _build_field_rows(app, table, group)
    _build_review_actions(app, outer)


def _build_group_header(app, outer, group: MatchGroup):
    top = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    top.pack(fill="x", pady=(0, 12))
    ctk.CTkLabel(top, text=f"GROUP {app.group_index + 1} OF {len(app.groups)}", text_color=widgets.COLORS["muted"], font=widgets.FONTS["section"]).pack(side="left")
    ctk.CTkLabel(top, text=f"{group.score:.0f}% MATCH", fg_color=widgets.COLORS["green_light"], text_color=widgets.COLORS["green"], font=widgets.FONTS["button_small"], width=110, height=32, corner_radius=8).pack(side="right")


def _build_reason_bar(parent, group: MatchGroup):
    reason = ctk.CTkFrame(parent, fg_color=widgets.COLORS["panel_subtle"], height=44, corner_radius=13)
    reason.pack(fill="x", padx=2, pady=2)
    reason.pack_propagate(False)
    ctk.CTkLabel(reason, text="●  " + "  •  ".join(group.reasons), text_color=widgets.COLORS["green"], font=widgets.FONTS["body"], anchor="w").pack(fill="x", padx=18, pady=11)


def _build_record_columns(app, table, group: MatchGroup):
    table.grid_columnconfigure(0, minsize=150)
    app.keep_vars = {}
    app.field_widgets = {}
    preferred_ref = next((ref for ref in group.records if ref.source == "truth"), group.records[0])

    for column, ref in enumerate(group.records, 1):
        table.grid_columnconfigure(column, weight=1, minsize=280)
        keep = tk.BooleanVar(value=ref == preferred_ref)
        app.keep_vars[ref] = keep
        header = ctk.CTkFrame(table, fg_color=widgets.COLORS["panel_header"], border_color=widgets.COLORS["line"], border_width=1, corner_radius=0)
        header.grid(row=0, column=column, sticky="nsew")
        ctk.CTkCheckBox(header, text=f"ROW {ref.index + 2}", variable=keep, fg_color=widgets.COLORS["green"], hover_color=widgets.COLORS["green_hover"], border_color=widgets.COLORS["line"], text_color=widgets.COLORS["green"], font=widgets.FONTS["section"], corner_radius=6).pack(anchor="w", padx=12, pady=12)


def _build_field_rows(app, table, group: MatchGroup):
    app.field_vars = {}
    app.edit_vars = {}
    headers = app._headers_for_review(group)
    default_ref = next((ref for ref in group.records if ref.source == "truth"), group.records[0])
    for row, field in enumerate(headers, 1):
        ctk.CTkLabel(table, text=field, fg_color=widgets.COLORS["paper"], text_color=widgets.COLORS["muted"], font=widgets.FONTS["section"], anchor="w", corner_radius=0).grid(row=row, column=0, sticky="nsew", padx=12, pady=12)
        preferred = _preferred_ref(app, group, field, default_ref)
        var = tk.StringVar(value=f"{preferred.source}:{preferred.index}")
        app.field_vars[field] = var
        _build_field_values(app, table, group, row, field, var)


def _preferred_ref(app, group, field: str, default_ref: RecordRef) -> RecordRef:
    if app._row_for(default_ref).get(field, ""):
        return default_ref
    return next((ref for ref in group.records if app._row_for(ref).get(field, "")), default_ref)


def _build_field_values(app, table, group, row: int, field: str, variable: tk.StringVar):
    for column, ref in enumerate(group.records, 1):
        value = app._row_for(ref).get(field, "")
        edit_variable = tk.StringVar(value=value)
        app.edit_vars[(ref, field)] = edit_variable
        bg = widgets.COLORS["paper"] if row % 2 else widgets.COLORS["panel_subtle"]
        cell_frame = ctk.CTkFrame(table, fg_color=bg, corner_radius=0)
        cell_frame.grid(row=row, column=column, sticky="nsew")
        cell = ctk.CTkRadioButton(
            cell_frame,
            text="",
            variable=variable,
            value=f"{ref.source}:{ref.index}",
            fg_color=widgets.COLORS["green"],
            hover_color=widgets.COLORS["green_hover"],
            border_color=widgets.COLORS["line"],
            text_color=widgets.COLORS["ink"],
            text_color_disabled=widgets.COLORS["muted"],
            font=widgets.FONTS["body"],
            width=28,
        )
        cell.pack(side="left", padx=(12, 4), pady=11)
        entry = ctk.CTkEntry(
            cell_frame,
            textvariable=edit_variable,
            fg_color=widgets.COLORS["entry_bg"],
            border_color=widgets.COLORS["line"],
            text_color=widgets.COLORS["ink"],
            font=widgets.FONTS["body"],
            height=36,
            corner_radius=8,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)
        app.field_widgets.setdefault(ref, []).append(cell)


def _refresh_field_choices(app):
    selected = [ref for ref, var in app.keep_vars.items() if var.get()]
    selected_refs = set(selected)
    for ref, cells in app.field_widgets.items():
        state = "normal" if ref in selected_refs else "disabled"
        for cell in cells:
            cell.configure(state=state)
    if not selected:
        return
    preferred = next((ref for ref in selected if ref.source == "truth"), selected[0])
    for field, variable in app.field_vars.items():
        source, index = variable.get().split(":", 1)
        current = RecordRef(source, int(index))
        if current in selected_refs:
            continue
        fallback = next((ref for ref in selected if app.edit_vars[(ref, field)].get()), preferred)
        variable.set(f"{fallback.source}:{fallback.index}")


def _update_selection_status(app):
    selected_count = sum(var.get() for var in app.keep_vars.values())
    if selected_count == 0:
        message = "No rows selected."
    elif selected_count == 1:
        message = "1 row selected. Merge uses values from that row."
    else:
        message = f"{selected_count} rows selected. Keep retains all; Merge combines their field choices."
    app.selection_status_var.set(message)


def _build_review_actions(app, outer):
    actions = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    actions.pack(fill="x", pady=(16, 0))
    app.selection_status_var = tk.StringVar()
    ctk.CTkLabel(actions, textvariable=app.selection_status_var, text_color=widgets.COLORS["muted"], font=widgets.FONTS["body_small"], anchor="w").pack(side="left", padx=(0, 12))
    for variable in app.keep_vars.values():
        variable.trace_add("write", lambda *_args: (_refresh_field_choices(app), _update_selection_status(app)))
    _refresh_field_choices(app)
    _update_selection_status(app)
    widgets.button(actions, "Not duplicates", lambda: app.resolve("not_duplicate"), "ghost").pack(side="left")
    widgets.button(actions, "Keep selected rows", lambda: app.resolve("keep"), "secondary").pack(side="right", padx=(10, 0))
    widgets.button(actions, "Merge selected rows", lambda: app.resolve("merge"), "primary_small").pack(side="right")


# ============================================================================
# Completion view
# ============================================================================
def render_complete(app):
    outer = widgets.page(app, "Review complete", "Export the clean CSV and its companion audit log.")
    frame = widgets.card(outer)
    resolved = len(app.decisions)
    ctk.CTkLabel(frame, text="✓", fg_color=widgets.COLORS["green_light"], text_color=widgets.COLORS["green"], font=widgets.FONTS["success_icon"], width=64, height=64, corner_radius=18).grid(row=0, column=0, rowspan=2, padx=24, pady=26)
    ctk.CTkLabel(frame, text=f"{resolved} duplicate groups reviewed", text_color=widgets.COLORS["ink"], font=widgets.FONTS["card_title"], anchor="w").grid(row=0, column=1, sticky="sw")
    ctk.CTkLabel(frame, text="Nothing is overwritten. Export creates new files.", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body"], anchor="w").grid(row=1, column=1, sticky="nw")
    widgets.button(frame, "Export cleaned CSV", app.export_results, "primary").grid(row=0, column=2, rowspan=2, padx=26)


# ============================================================================
# Analyze view
# ============================================================================
def render_analyze(app):
    app.crumb.configure(text=f"Analyze  ›  {'Single-file' if app.scan_mode == 'single' else 'Multi-file'}")
    outer = widgets.page(app, "Analyze", "Review common tokens and tune how strongly they influence matching.")
    ctk.CTkLabel(outer, text="Reference columns appear during review but never affect matching.", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body_large"], anchor="w").pack(fill="x", pady=(0, 4))
    ctk.CTkLabel(outer, text=f"Analyzes: {_matching_columns_text(app)}  •  Tokens must appear in at least {app.rules.common_token_min_documents} rows.", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body_small"], anchor="w").pack(fill="x", pady=(0, 16))

    app.token_weight_vars = {}
    if not app.token_stats:
        empty = widgets.card(outer)
        ctk.CTkLabel(empty, text="No token analysis yet", text_color=widgets.COLORS["ink"], font=widgets.FONTS["card_title"], anchor="w").pack(fill="x", padx=22, pady=(22, 5))
        ctk.CTkLabel(empty, text="Load files and choose match columns in Setup, then run Analyze.", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body"], anchor="w").pack(fill="x", padx=22, pady=(0, 22))
    else:
        table_holder = ctk.CTkFrame(outer, fg_color=widgets.COLORS["paper"], border_color=widgets.COLORS["line"], border_width=1, corner_radius=14)
        table_holder.pack(fill="both", expand=True)
        table = widgets.scrollable_frame(table_holder)
        for column, width in enumerate((150, 70, 80, 80, 360, 100)):
            table.grid_columnconfigure(column, minsize=width, weight=1 if column == 4 else 0)
        for column, heading in enumerate(("TOKEN", "ROWS", "SHARE", "AUTO", "EXAMPLES", "WEIGHT")):
            ctk.CTkLabel(table, text=heading, fg_color=widgets.COLORS["panel_header"], text_color=widgets.COLORS["muted"], font=widgets.FONTS["section"], anchor="w", corner_radius=0).grid(row=0, column=column, sticky="ew", padx=1, pady=1)

        for row, stat in enumerate(app.token_stats, 1):
            bg = widgets.COLORS["paper"] if row % 2 else widgets.COLORS["panel_subtle"]
            values = (stat.token, str(stat.count), f"{stat.percentage:.1f}%", f"{stat.automatic_weight:.2f}", " | ".join(stat.examples))
            for column, value in enumerate(values):
                ctk.CTkLabel(table, text=value, fg_color=bg, text_color=widgets.COLORS["ink"] if column == 0 else widgets.COLORS["muted"], font=widgets.FONTS["body"] if column != 4 else widgets.FONTS["body_small"], anchor="w", corner_radius=0).grid(row=row, column=column, sticky="ew", padx=1, pady=1)
            weight_var = tk.StringVar(value=f"{stat.weight:.2f}" if stat.token in app.rules.token_weights else "auto")
            app.token_weight_vars[stat.token] = weight_var
            ctk.CTkEntry(table, textvariable=weight_var, width=76, height=32, justify="right", fg_color=widgets.COLORS["entry_bg"], border_color=widgets.COLORS["line"], text_color=widgets.COLORS["ink"], font=widgets.FONTS["body"], corner_radius=8).grid(row=row, column=5, padx=10, pady=6)

    actions = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    actions.pack(fill="x", pady=(18, 0))
    widgets.button(actions, "Back to Setup", app.show_workspace, "ghost").pack(side="left")
    widgets.button(actions, "Run analysis", app.analyze_common_tokens, "primary_small").pack(side="right")


def _matching_columns_text(app):
    if app.scan_mode == "single":
        return ", ".join(app.single.match_columns) or "single-file match columns not selected"
    truth = ", ".join(app.truth.match_columns) or "truth match columns not selected"
    dependent = ", ".join(app.dependent.match_columns) or "dependent match columns not selected"
    return f"{truth} + {dependent}"


# ============================================================================
# Settings view
# ============================================================================
def render_settings(app):
    app.crumb.configure(text="Settings")
    outer = widgets.page(app, "Settings", "Configure matching behavior before scanning.")

    algorithm_card = widgets.card(outer)
    widgets.section_label(algorithm_card, "ALGORITHM", widgets.COLORS["green_light"], widgets.COLORS["green"], row=0, column=0, sticky="w", padx=22, pady=(22, 8))
    ctk.CTkLabel(algorithm_card, text="Soft weighted token matching", text_color=widgets.COLORS["ink"], font=widgets.FONTS["body_large"], anchor="w").grid(row=1, column=0, sticky="w", padx=22, pady=(0, 20))
    ctk.CTkLabel(algorithm_card, text="Handles reordered words while reducing common-token influence.", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body_small"], anchor="w").grid(row=1, column=1, sticky="w", pady=(0, 20))

    threshold_card = widgets.card(outer)
    app.review_var = tk.IntVar(value=app.rules.review_threshold)
    widgets.section_label(threshold_card, "THRESHOLDS", widgets.COLORS["panel_alt"], widgets.COLORS["muted"], row=0, column=0, columnspan=3, sticky="w", padx=22, pady=(22, 6))
    widgets.scale_row(threshold_card, "Similarity review", app.review_var, 1)
    app.common_token_min_documents_var = tk.IntVar(value=app.rules.common_token_min_documents)
    widgets.scale_row(threshold_card, "Minimum common-token rows", app.common_token_min_documents_var, 2, minimum=1, maximum=25)

    normalization_card = widgets.card(outer)
    app.norm_vars = {}
    widgets.section_label(normalization_card, "NORMALIZATION", widgets.COLORS["panel_alt"], widgets.COLORS["muted"], row=0, column=0, sticky="w", padx=22, pady=(22, 8))
    norm_frame = ctk.CTkFrame(normalization_card, fg_color="transparent", corner_radius=0)
    norm_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=22, pady=(0, 20))
    for attr, label in (("lowercase", "Lowercase text"), ("remove_punctuation", "Remove punctuation")):
        var = tk.BooleanVar(value=getattr(app.rules, attr))
        app.norm_vars[attr] = var
        ctk.CTkCheckBox(norm_frame, text=label, variable=var, fg_color=widgets.COLORS["green"], hover_color=widgets.COLORS["green_hover"], border_color=widgets.COLORS["line"], text_color=widgets.COLORS["ink"], font=widgets.FONTS["body"], corner_radius=6).pack(anchor="w", pady=5)

    actions = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    actions.pack(fill="x", pady=(2, 0))
    widgets.button(actions, "Save settings", app.save_rules, "primary_small").pack(side="right")
    widgets.button(actions, "Export JSON…", app.export_rules, "secondary").pack(side="right", padx=10)
