from __future__ import annotations

import tkinter as tk

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
# Purpose: collect source files, select match/reference columns, review common tokens, and start a scan.
# Layout: page -> source cards -> match/reference choosers -> common-token review -> scan action.
# Events: app.load_source(), app.analyze_common_tokens(), and app.start_scan().
# ============================================================================
def render_workspace(app, mode: str):
    """Render Setup and its selected single-file or multi-file mode."""
    app.crumb.configure(text=f"Setup  ›  {'Single file' if mode == 'single' else 'Multi-file'}")

    outer = widgets.page(app, "Setup", "Set up a single-file or multi-file duplicate scan.")
    mode_bar = tk.Frame(outer, bg=widgets.COLORS["bg"])
    mode_bar.pack(fill="x", pady=(0, 16))
    tk.Label(mode_bar, text="SCAN MODE", bg=widgets.COLORS["bg"], fg=widgets.COLORS["muted"], font=widgets.FONTS["section"]).pack(side="left", padx=(0, 12))
    for option, label in (("single", "Single file"), ("multi", "Multi-file")):
        style = "primary_small" if option == mode else "secondary"
        widgets.button(mode_bar, label, lambda selected=option: app.show_workspace(selected), style, padx=13, pady=7).pack(side="left", padx=(0, 8))

    if mode == "single":
        _render_single_import(app, outer)
    else:
        _render_multi_import(app, outer)


def _render_single_import(app, outer):
    tk.Label(outer, text="Find duplicates in one CSV", bg=widgets.COLORS["bg"], fg=widgets.COLORS["ink"], font=widgets.FONTS["card_title"]).pack(anchor="w", pady=(0, 8))
    frame = widgets.card(outer)
    frame.pack_configure(fill="both", expand=True)

    widgets.source_picker(app, frame, app.single, "CSV file", 0)
    _render_column_picker(app, frame, app.single, 1, "match")
    _render_column_picker(app, frame, app.single, 2, "reference")
    _render_common_token_section(frame, app, 3)
    frame.grid_rowconfigure(4, weight=1)
    _render_scan_action(frame, lambda: app.start_scan("single"), 5)


def _render_multi_import(app, outer):
    tk.Label(outer, text="Reconcile two CSV sources", bg=widgets.COLORS["bg"], fg=widgets.COLORS["ink"], font=widgets.FONTS["card_title"]).pack(anchor="w", pady=(0, 8))
    sources = tk.Frame(outer, bg=widgets.COLORS["bg"])
    sources.pack(fill="x")

    _render_source_card(app, sources, app.truth, "SOURCE OF TRUTH", "Truth CSV", widgets.COLORS["truth_header"], (0, 8))
    _render_source_card(app, sources, app.dependent, "DEPENDENT SOURCE", "Dependent CSV", widgets.COLORS["panel_alt"], (8, 0))

    footer = widgets.card(outer)
    footer.pack_configure(fill="both", expand=True)
    _render_common_token_section(footer, app, 0)
    footer.grid_rowconfigure(1, weight=1)
    _render_scan_action(footer, lambda: app.start_scan("multi"), 2)


def _render_scan_action(parent, command, row: int):
    """Place the primary scan action at the bottom-right of a workspace card."""
    actions = tk.Frame(parent, bg=widgets.COLORS["paper"])
    actions.grid(row=row, column=0, columnspan=3, sticky="ew", padx=20, pady=(16, 20))
    widgets.button(actions, "Scan", command, "primary", padx=20, pady=10).pack(side="right")


def _render_source_card(app, parent, source, section_text, file_label, header_bg, padding):
    frame = widgets.card(parent)
    frame.pack_forget()
    frame.pack(side="left", fill="both", expand=True, padx=padding)

    widgets.section_label(frame, section_text, header_bg, widgets.COLORS["green"] if source.role == "truth" else widgets.COLORS["muted"], row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(18, 8))
    widgets.source_picker(app, frame, source, file_label, 1)
    _render_column_picker(app, frame, source, 2, "match")
    _render_column_picker(app, frame, source, 3, "reference")


# ============================================================================
# Review view
# Purpose: present one duplicate group and collect keep/merge decisions.
# Layout: group header -> reason bar -> scrollable record grid -> actions.
# Widgets: page(), scrollable_frame(), record headers, field radio buttons.
# Events: app.resolve().
# ============================================================================
def render_review(app):
    """Render the current duplicate group for manual resolution."""
    app.crumb.configure(text=f"Review  ›  {'Single-file' if app.scan_mode == 'single' else 'Multi-file'}")
    outer = widgets.page(app, "Review", "Select one or more rows to keep, or choose field values to merge.")

    if not app.groups:
        frame = widgets.card(outer)
        tk.Label(frame, text="No review is ready yet.", bg=widgets.COLORS["paper"], fg=widgets.COLORS["ink"], font=widgets.FONTS["body_large"]).pack(anchor="w", padx=20, pady=(20, 6))
        tk.Label(frame, text="Run a scan from Setup first.", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body"]).pack(anchor="w", padx=20, pady=(0, 16))
        widgets.button(frame, "Back to Setup", app.show_workspace, "secondary", padx=14, pady=8).pack(anchor="w", padx=20, pady=(0, 20))
        return

    group: MatchGroup = app.groups[app.group_index]
    _build_group_header(app, outer, group)
    review_frame = tk.Frame(outer, bg=widgets.COLORS["paper"], highlightbackground=widgets.COLORS["line"], highlightthickness=1)
    review_frame.pack(fill="both", expand=True)

    _build_reason_bar(review_frame, group)
    table = widgets.scrollable_frame(review_frame)
    _build_record_columns(app, table, group)
    _build_field_rows(app, table, group)
    _build_review_actions(app, outer)


def _build_group_header(app, outer, group: MatchGroup):
    top = tk.Frame(outer, bg=widgets.COLORS["bg"])
    top.pack(fill="x", pady=(0, 10))
    tk.Label(top, text=f"GROUP {app.group_index + 1} OF {len(app.groups)}", bg=widgets.COLORS["bg"], fg=widgets.COLORS["muted"], font=widgets.FONTS["section"]).pack(side="left")

    tk.Label(top, text=f"{group.score:.0f}% MATCH", bg=widgets.COLORS["panel_subtle"], fg=widgets.COLORS["muted"], font=widgets.FONTS["button_small"], padx=10, pady=5).pack(side="right")


def _build_reason_bar(parent, group: MatchGroup):
    reason = tk.Frame(parent, bg=widgets.COLORS["panel_subtle"], height=38)
    reason.pack(fill="x")
    reason.pack_propagate(False)

    tk.Label(reason, text="●  " + "  •  ".join(group.reasons), bg=widgets.COLORS["panel_subtle"], fg=widgets.COLORS["green"], font=widgets.FONTS["body"]).pack(side="left", padx=16, pady=10)


def _build_record_columns(app, table, group: MatchGroup):
    table.grid_columnconfigure(0, minsize=140)
    app.keep_vars = {}
    app.field_widgets = {}
    preferred_ref = next((ref for ref in group.records if ref.source == "truth"), group.records[0])

    for column, ref in enumerate(group.records, 1):
        table.grid_columnconfigure(column, weight=1, minsize=220)
        keep = tk.BooleanVar(value=ref == preferred_ref)
        app.keep_vars[ref] = keep
        header = tk.Frame(table, bg=widgets.COLORS["panel_header"], highlightbackground=widgets.COLORS["line"], highlightthickness=1)
        header.grid(row=0, column=column, sticky="nsew")
        tk.Checkbutton(header, variable=keep, text=f"ROW {ref.index + 2}", bg=widgets.COLORS["panel_header"], fg=widgets.COLORS["green"], activebackground=widgets.COLORS["panel_header"], selectcolor=widgets.COLORS["paper"], font=widgets.FONTS["section"]).pack(anchor="w", padx=10, pady=10)


def _build_field_rows(app, table, group: MatchGroup):
    app.field_vars = {}
    headers = app._headers_for_review(group)
    default_ref = next((ref for ref in group.records if ref.source == "truth"), group.records[0])

    for row, field in enumerate(headers, 1):
        tk.Label(table, text=field, bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["section"], anchor="w", padx=12).grid(row=row, column=0, sticky="nsew", ipady=10)
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
        cell = tk.Radiobutton(table, text=value or "—", variable=variable, value=f"{ref.source}:{ref.index}", bg=widgets.COLORS["paper"], activebackground=widgets.COLORS["field_active"], selectcolor=widgets.COLORS["green_light"], fg=widgets.COLORS["ink"], font=widgets.FONTS["body"], anchor="w", justify="left", wraplength=250, padx=10, pady=9)
        cell.grid(row=row, column=column, sticky="nsew")
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
        fallback = next((ref for ref in selected if app._row_for(ref).get(field, "")), preferred)
        variable.set(fallback.source + ":" + str(fallback.index))


def _update_selection_status(app):
    selected_count = sum(var.get() for var in app.keep_vars.values())
    if selected_count == 0:
        message = "No rows selected."
    elif selected_count == 1:
        message = "1 row selected. Merge uses the field choices from that row."
    else:
        message = f"{selected_count} rows selected. Keep retains all; Merge combines their field choices into one row."
    app.selection_status_var.set(message)


def _build_review_actions(app, outer):
    actions = tk.Frame(outer, bg=widgets.COLORS["bg"])
    actions.pack(fill="x", pady=(14, 0))

    app.selection_status_var = tk.StringVar()
    tk.Label(actions, textvariable=app.selection_status_var, bg=widgets.COLORS["bg"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body_small"], anchor="w").pack(side="left")
    for variable in app.keep_vars.values():
        variable.trace_add("write", lambda *_args: (_refresh_field_choices(app), _update_selection_status(app)))
    _refresh_field_choices(app)
    _update_selection_status(app)

    widgets.button(actions, "Not duplicates", lambda: app.resolve("not_duplicate"), "ghost").pack(side="left")
    widgets.button(actions, "Keep selected rows", lambda: app.resolve("keep"), "secondary", padx=15, pady=9).pack(side="right", padx=(9, 0))
    widgets.button(actions, "Merge selected rows", lambda: app.resolve("merge"), "primary_small", padx=16, pady=10).pack(side="right")


# ============================================================================
# Completion view
# Purpose: confirm that review is finished and offer cleaned-file export.
# Layout: result card with summary text and the export action.
# Widgets: page(), card(), and a primary export button.
# Events: app.export_results().
# ============================================================================
def render_complete(app):
    """Render the post-review export screen."""
    outer = widgets.page(app, "Review complete", "Export the clean CSV and its companion audit log.")
    frame = widgets.card(outer)

    resolved = len(app.decisions)
    tk.Label(frame, text="✓", bg=widgets.COLORS["green_light"], fg=widgets.COLORS["green"], font=widgets.FONTS["success_icon"], width=3, pady=12).grid(row=0, column=0, rowspan=2, padx=20, pady=24)
    tk.Label(frame, text=f"{resolved} duplicate groups reviewed", bg=widgets.COLORS["paper"], fg=widgets.COLORS["ink"], font=widgets.FONTS["card_title"]).grid(row=0, column=1, sticky="sw")
    tk.Label(frame, text="Nothing is overwritten. Export creates new files.", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body"]).grid(row=1, column=1, sticky="nw")
    widgets.button(frame, "Export cleaned CSV", app.export_results, "primary", padx=18, pady=10).grid(row=0, column=2, rowspan=2, padx=24)


def _render_common_token_section(frame, app, row: int):
    common_frame = tk.Frame(frame, bg=widgets.COLORS["paper"])
    common_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 18))
    common_frame.grid_columnconfigure(1, weight=1)

    tk.Label(common_frame, text="COMMON TOKENS", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["section"]).grid(row=0, column=0, sticky="w", pady=(0, 5))
    tk.Label(common_frame, text="Analyze frequent tokens from the match columns. Reference columns do not affect token scoring.", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body_small"]).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
    tk.Label(common_frame, text=f"Analyzes: {_matching_columns_text(app)}", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body_small"]).grid(row=2, column=0, sticky="w", pady=(0, 5))
    widgets.button(common_frame, "Analyze common tokens…", app.open_common_token_analysis, "secondary", padx=12, pady=7).grid(row=2, column=2, sticky="e", pady=(0, 5))


def render_common_token_dialog(app, dialog):
    """Render the scrollable common-token analysis window."""
    for child in dialog.winfo_children():
        child.destroy()
    dialog.title("Common-token analysis")
    dialog.geometry("760x620")
    dialog.minsize(560, 420)
    dialog.configure(bg=widgets.COLORS["bg"])
    app.common_token_dialog = dialog

    tk.Label(dialog, text="Common-token analysis", bg=widgets.COLORS["bg"], fg=widgets.COLORS["ink"], font=widgets.FONTS["title"]).pack(anchor="w", padx=24, pady=(22, 4))
    tk.Label(dialog, text="Reference columns are shown during review but do not affect matching.", bg=widgets.COLORS["bg"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body_large"]).pack(anchor="w", padx=24, pady=(0, 4))
    tk.Label(dialog, text=f"Analyzes: {_matching_columns_text(app)}  •  Showing tokens appearing in at least {app.rules.common_token_min_documents} rows.", bg=widgets.COLORS["bg"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body_small"]).pack(anchor="w", padx=24, pady=(0, 14))

    app.token_weight_vars = {}
    if not app.token_stats:
        tk.Label(dialog, text="No token analysis yet.", bg=widgets.COLORS["panel_subtle"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body"], padx=12, pady=10).pack(fill="x", padx=24, pady=8)
    else:
        table_holder = tk.Frame(dialog, bg=widgets.COLORS["paper"], highlightbackground=widgets.COLORS["line"], highlightthickness=1)
        table_holder.pack(fill="both", expand=True, padx=24)
        table = widgets.scrollable_frame(table_holder)
        for column, width in enumerate((150, 70, 80, 80, 360, 100)):
            table.grid_columnconfigure(column, minsize=width, weight=1 if column == 4 else 0)
        for column, heading in enumerate(("TOKEN", "ROWS", "SHARE", "AUTO", "EXAMPLES", "WEIGHT")):
            tk.Label(table, text=heading, bg=widgets.COLORS["panel_header"], fg=widgets.COLORS["muted"], font=widgets.FONTS["section"], anchor="w", padx=10, pady=7).grid(row=0, column=column, sticky="ew")

        for row, stat in enumerate(app.token_stats, 1):
            bg = widgets.COLORS["paper"] if row % 2 else widgets.COLORS["panel_subtle"]
            tk.Label(table, text=stat.token, bg=bg, fg=widgets.COLORS["ink"], font=widgets.FONTS["body"], anchor="w", padx=10, pady=7).grid(row=row, column=0, sticky="ew")
            tk.Label(table, text=str(stat.count), bg=bg, fg=widgets.COLORS["muted"], font=widgets.FONTS["body"], anchor="w", padx=10).grid(row=row, column=1, sticky="ew")
            tk.Label(table, text=f"{stat.percentage:.1f}%", bg=bg, fg=widgets.COLORS["muted"], font=widgets.FONTS["body"], anchor="w", padx=10).grid(row=row, column=2, sticky="ew")
            tk.Label(table, text=f"{stat.automatic_weight:.2f}", bg=bg, fg=widgets.COLORS["muted"], font=widgets.FONTS["body"], anchor="w", padx=10).grid(row=row, column=3, sticky="ew")
            tk.Label(table, text=" | ".join(stat.examples), bg=bg, fg=widgets.COLORS["muted"], font=widgets.FONTS["body_small"], anchor="w", padx=10).grid(row=row, column=4, sticky="ew")
            weight_var = tk.StringVar(value=f"{stat.weight:.2f}" if stat.token in app.rules.token_weights else "auto")
            app.token_weight_vars[stat.token] = weight_var
            tk.Entry(table, textvariable=weight_var, width=7, font=widgets.FONTS["body"], justify="right").grid(row=row, column=5, padx=10, pady=4)

    actions = tk.Frame(dialog, bg=widgets.COLORS["bg"])
    actions.pack(fill="x", padx=24, pady=18)
    widgets.button(actions, "Analyze", app.analyze_common_tokens, "primary_small", padx=14, pady=8).pack(side="right")
    widgets.button(actions, "Close", dialog.destroy, "ghost", padx=14, pady=8).pack(side="right", padx=(0, 9))


def _matching_columns_text(app):
    if app.scan_mode == "single":
        return ", ".join(app.single.match_columns) or "single-file match columns not selected"
    truth = ", ".join(app.truth.match_columns) or "truth match columns not selected"
    dependent = ", ".join(app.dependent.match_columns) or "dependent match columns not selected"
    return f"{truth} + {dependent}"


# ============================================================================
# Rules view
# Purpose: configure thresholds and normalization for matching.
# Layout: algorithm -> threshold -> normalization -> actions.
# Widgets: scale rows, normalization checkboxes, and action buttons.
# Events: app.save_rules() and app.export_rules().
# ============================================================================
def render_rules(app):
    """Render the fuzzy-matching configuration screen."""
    app.crumb.configure(text="Setup  ›  Ruleset")

    outer = widgets.page(app, "Configure ruleset", "Configure matching behavior before scanning.")
    frame = widgets.card(outer)

    tk.Label(frame, text="ALGORITHM", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["section"]).grid(row=0, column=0, sticky="w", padx=20, pady=18)
    tk.Label(frame, text="Soft weighted token matching", bg=widgets.COLORS["paper"], fg=widgets.COLORS["ink"], font=widgets.FONTS["body_large"]).grid(row=1, column=0, sticky="w", padx=20)
    tk.Label(frame, text="Handles reordered words while reducing common-token influence.", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["body_small"]).grid(row=1, column=1, sticky="w", pady=14)

    app.review_var = tk.IntVar(value=app.rules.review_threshold)

    tk.Label(frame, text="THRESHOLD", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["section"]).grid(row=2, column=0, columnspan=3, sticky="w", padx=20, pady=(18, 4))
    widgets.scale_row(frame, "Review threshold", app.review_var, 3)
    app.common_token_min_documents_var = tk.IntVar(value=app.rules.common_token_min_documents)
    widgets.scale_row(frame, "Minimum rows for common tokens", app.common_token_min_documents_var, 4, minimum=1, maximum=25)

    app.norm_vars = {}
    norms = [("lowercase", "Lowercase"), ("remove_punctuation", "Remove punctuation")]
    norm_frame = tk.Frame(frame, bg=widgets.COLORS["paper"])
    norm_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=20, pady=18)
    tk.Label(norm_frame, text="NORMALIZATION", bg=widgets.COLORS["paper"], fg=widgets.COLORS["muted"], font=widgets.FONTS["section"]).pack(anchor="w", pady=(0, 8))

    for attr, label in norms:
        var = tk.BooleanVar(value=getattr(app.rules, attr))
        app.norm_vars[attr] = var
        tk.Checkbutton(norm_frame, text=label, variable=var, bg=widgets.COLORS["paper"], activebackground=widgets.COLORS["paper"], selectcolor=widgets.COLORS["paper"], font=widgets.FONTS["body"]).pack(anchor="w", pady=3)

    actions = tk.Frame(frame, bg=widgets.COLORS["paper"])
    actions.grid(row=6, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 20))

    widgets.button(actions, "Save ruleset", app.save_rules, "primary_small", padx=18, pady=9).pack(side="right")
    widgets.button(actions, "Export JSON…", app.export_rules, "secondary", padx=14, pady=8).pack(side="right", padx=9)
