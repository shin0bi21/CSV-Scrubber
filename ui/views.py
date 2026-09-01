from __future__ import annotations

from itertools import zip_longest
import tkinter as tk

import customtkinter as ctk

from engine import MatchGroup, RecordRef

from . import widgets


_COLUMN_PICKER_CONFIG = {
    "match": {
        "attribute": "match_columns",
        "label": "Match columns",
        "popup_title": "Choose match columns",
        "popup_subtitle": "Selected columns are matched by position; values do not cross column boundaries.",
    },
    "reference": {
        "attribute": "reference_columns",
        "label": "Reference columns",
        "popup_title": "Choose reference columns",
        "popup_subtitle": "These columns provide supporting context but do not affect the match score.",
    },
}

_REVIEW_RECORD_WIDTH = 250
_REVIEW_HEADER_HEIGHT = 50
_REVIEW_ROW_HEIGHT = 62


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
# Review view
# ============================================================================
def render_review(app):
    """Render the current duplicate group for manual resolution."""
    app.crumb.configure(text=f"Review  ›  {'Single-file' if app.scan_mode == 'single' else 'Multi-file'}")
    outer = widgets.page(
        app,
        "Review",
        "Select rows to keep, or choose field values for a merged record. "
        "Main rows are editable; dependent rows are read-only.",
    )

    if not app.groups:
        frame = widgets.card(outer)
        ctk.CTkLabel(frame, text="No review is ready yet", text_color=widgets.COLORS["ink"], font=widgets.FONTS["card_title"], anchor="w").pack(fill="x", padx=22, pady=(22, 6))
        ctk.CTkLabel(frame, text="Run a scan from Setup first.", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body"], anchor="w").pack(fill="x", padx=22, pady=(0, 18))
        widgets.button(frame, "Back to Setup", app.show_workspace, "secondary").pack(anchor="w", padx=22, pady=(0, 22))
        return

    group: MatchGroup = app.groups[app.group_index]
    _build_group_header(app, outer, group)
    review_frame = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    review_frame.pack(fill="both", expand=True)
    _build_reason_summary(review_frame, group)
    _initialize_review_state(app, group)
    if app.scan_mode == "multi":
        _build_cross_source_review(app, review_frame, group)
    else:
        _build_single_source_review(app, review_frame, group)
    _build_review_actions(app, outer)


def _build_group_header(app, outer, group: MatchGroup):
    top = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    top.pack(fill="x", pady=(0, 12))
    ctk.CTkLabel(top, text=f"GROUP {app.group_index + 1} OF {len(app.groups)}", text_color=widgets.COLORS["muted"], font=widgets.FONTS["section"]).pack(side="left")
    ctk.CTkLabel(top, text=f"{group.score:.0f}% MATCH", fg_color=widgets.COLORS["green_light"], text_color=widgets.COLORS["green"], font=widgets.FONTS["button_small"], width=110, height=32, corner_radius=8).pack(side="right")


def _build_reason_summary(parent, group: MatchGroup):
    """Keep matching evidence available without taking space from the table."""
    summary = ctk.CTkFrame(parent, fg_color=widgets.COLORS["paper"], border_color=widgets.COLORS["line"], border_width=1, corner_radius=13)
    summary.pack(fill="x", pady=(0, 12))
    ctk.CTkLabel(
        summary,
        text="Match reason: " + ("  •  ".join(group.reasons) or "Candidate match"),
        text_color=widgets.COLORS["green"],
        font=widgets.FONTS["body_small"],
        anchor="w",
    ).pack(side="left", fill="x", expand=True, padx=(16, 10), pady=9)
    info_button = widgets.button(
        summary,
        "Match info",
        lambda: None,
        "ghost_green",
        width=104,
    )
    info_button.pack(side="right", padx=(0, 8), pady=4)
    info_card = _build_match_info_card(parent, group)
    pinned = {"value": False}

    def pointer_is_over(widget) -> bool:
        hovered = parent.winfo_containing(parent.winfo_pointerx(), parent.winfo_pointery())
        while hovered is not None:
            if hovered == widget:
                return True
            hovered = hovered.master
        return False

    def show_card(_event=None):
        parent.update_idletasks()
        y = summary.winfo_y() + summary.winfo_height() + 6
        info_card.place(relx=1, x=0, y=y, anchor="ne")
        info_card.lift()

    def hide_card_if_clear():
        if pinned["value"]:
            return
        if not pointer_is_over(info_button) and not pointer_is_over(info_card):
            info_card.place_forget()

    def schedule_hide(_event=None):
        parent.after(120, hide_card_if_clear)

    def toggle_card():
        pinned["value"] = not pinned["value"]
        if pinned["value"]:
            show_card()
        else:
            info_card.place_forget()

    def bind_hover_tree(widget):
        widget.bind("<Enter>", show_card, add=True)
        widget.bind("<Leave>", schedule_hide, add=True)
        for child in widget.winfo_children():
            bind_hover_tree(child)

    info_button.configure(command=toggle_card)
    info_button.bind("<Enter>", show_card)
    info_button.bind("<Leave>", schedule_hide)
    bind_hover_tree(info_card)


def _match_evidence_lines(group: MatchGroup) -> list[str]:
    evidence_lines = []
    for (left_ref, right_ref), evidence in group.evidence.items():
        pair_label = (
            f"{left_ref.source} row {left_ref.index + 2} ↔ "
            f"{right_ref.source} row {right_ref.index + 2}"
        )
        exact = ", ".join(left for left, _right in evidence.exact_token_matches)
        fuzzy = ", ".join(
            f"{left} <-> {right} ({similarity:.0f}%)"
            for left, right, similarity in evidence.fuzzy_token_matches
        )
        unmatched = ", ".join(evidence.unmatched_left_tokens + evidence.unmatched_right_tokens)
        parts = []
        if exact:
            parts.append(f"exact: {exact}")
        if fuzzy:
            parts.append(f"fuzzy: {fuzzy}")
        if unmatched:
            parts.append(f"unmatched: {unmatched}")
        parts.append(
            f"coverage: {evidence.shorter_name_coverage:.0f}% short / "
            f"{evidence.longer_name_coverage:.0f}% long"
        )
        evidence_lines.append(f"{pair_label}\n" + " • ".join(parts))
    return evidence_lines


def _build_match_info_card(parent, group: MatchGroup):
    """Create the compact hover card used for on-demand match evidence."""
    card = ctk.CTkFrame(
        parent,
        width=620,
        height=286,
        fg_color=widgets.COLORS["paper"],
        border_color=widgets.COLORS["line"],
        border_width=1,
        corner_radius=12,
    )
    card.pack_propagate(False)
    heading = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
    heading.pack(fill="x", padx=18, pady=(15, 4))
    ctk.CTkLabel(heading, text="Match details", text_color=widgets.COLORS["ink"], font=widgets.FONTS["card_title"], anchor="w").pack(side="left")
    ctk.CTkLabel(heading, text=f"{group.score:.0f}%", fg_color=widgets.COLORS["green_light"], text_color=widgets.COLORS["green"], font=widgets.FONTS["section"], height=26, corner_radius=7).pack(side="right", ipadx=8)
    ctk.CTkLabel(card, text=" • ".join(group.reasons) or "Candidate match", text_color=widgets.COLORS["green"], font=widgets.FONTS["body_small"], anchor="w").pack(fill="x", padx=18, pady=(0, 10))
    details = ctk.CTkTextbox(
        card,
        fg_color=widgets.COLORS["panel_subtle"],
        border_color=widgets.COLORS["line"],
        border_width=1,
        text_color=widgets.COLORS["muted"],
        font=widgets.FONTS["body_small"],
        corner_radius=9,
        wrap="word",
    )
    details.pack(fill="both", expand=True, padx=18, pady=(0, 16))
    details.insert("1.0", "\n\n".join(_match_evidence_lines(group)) or "No detailed match evidence is available.")
    details.configure(state="disabled")
    return card


def _initialize_review_state(app, group: MatchGroup):
    """Create review variables independently from the visual table arrangement."""
    app.keep_vars = {}
    app.field_widgets = {}
    app.field_vars = {}
    app.edit_vars = {}
    default_ref = next((ref for ref in group.records if ref.source == "truth"), group.records[0])
    for ref in group.records:
        app.keep_vars[ref] = tk.BooleanVar(value=ref == default_ref)
    for field in app._headers_for_review(group):
        preferred = _preferred_ref(app, group, field, default_ref)
        app.field_vars[field] = tk.StringVar(value=f"{preferred.source}:{preferred.index}")
        for ref in group.records:
            app.edit_vars[(ref, field)] = tk.StringVar(value=app._row_for(ref).get(field, ""))


def _preferred_ref(app, group, field: str, default_ref: RecordRef) -> RecordRef:
    if app._row_for(default_ref).get(field, ""):
        return default_ref
    return next((ref for ref in group.records if app._row_for(ref).get(field, "")), default_ref)


def _paired_review_fields(app) -> list[tuple[str, int, str | None, str | None]]:
    """Pair cross-file fields by the same position used by the matcher."""
    rows = []
    seen = set()
    sections = (
        ("MATCH", app.truth.match_columns, app.dependent.match_columns),
        ("REFERENCE", app.truth.reference_columns, app.dependent.reference_columns),
    )
    for role, truth_fields, dependent_fields in sections:
        for position, (truth_field, dependent_field) in enumerate(
            zip_longest(truth_fields, dependent_fields),
            1,
        ):
            pair = (truth_field, dependent_field)
            if pair in seen:
                continue
            seen.add(pair)
            rows.append((role, position, truth_field, dependent_field))
    return rows


def _build_cross_source_review(app, parent, group: MatchGroup):
    truth_refs = [ref for ref in group.records if ref.source == "truth"]
    dependent_refs = [ref for ref in group.records if ref.source == "dependent"]
    rows = _paired_review_fields(app)
    comparison_height = 116 + _REVIEW_ROW_HEIGHT * max(1, len(rows)) + (18 if max(len(truth_refs), len(dependent_refs)) > 1 else 0)
    comparison = ctk.CTkFrame(parent, height=comparison_height, fg_color="transparent", corner_radius=0)
    comparison.pack(fill="x")
    comparison.grid_propagate(False)
    comparison.grid_rowconfigure(0, weight=1)
    if len(truth_refs) > 1:
        comparison.grid_columnconfigure(0, weight=1, uniform="review_sources")
        comparison.grid_columnconfigure(1, weight=1, uniform="review_sources")
    else:
        comparison.grid_columnconfigure(0, weight=2, uniform="review_sources")
        comparison.grid_columnconfigure(1, weight=3, uniform="review_sources")

    _build_review_card(app, comparison, truth_refs, rows, "truth", 0, padx=(0, 7))
    _build_review_card(app, comparison, dependent_refs, rows, "dependent", 1, padx=(7, 0))


def _build_single_source_review(app, parent, group: MatchGroup):
    rows = [("FIELD", position, field, field) for position, field in enumerate(app._headers_for_review(group), 1)]
    comparison_height = 116 + _REVIEW_ROW_HEIGHT * max(1, len(rows)) + (18 if len(group.records) > 1 else 0)
    comparison = ctk.CTkFrame(parent, height=comparison_height, fg_color="transparent", corner_radius=0)
    comparison.pack(fill="x")
    comparison.grid_propagate(False)
    comparison.grid_rowconfigure(0, weight=1)
    comparison.grid_columnconfigure(0, weight=1)
    _build_review_card(app, comparison, group.records, rows, "single", 0)


def _review_card_title(rows, source: str) -> str:
    fields = []
    for _role, _position, truth_field, dependent_field in rows:
        field = truth_field if source in ("truth", "single") else dependent_field
        if field and field not in fields:
            fields.append(field)
    return " / ".join(fields) or "Unmapped fields"


def _build_review_card(app, parent, refs: list[RecordRef], rows, source: str, column: int, padx=0):
    """Render one source as a self-contained field-and-record card."""
    card = ctk.CTkFrame(
        parent,
        width=1,
        height=1,
        fg_color=widgets.COLORS["paper"],
        border_color=widgets.COLORS["line"],
        border_width=1,
        corner_radius=12,
    )
    card.grid(row=0, column=column, sticky="nsew", padx=padx)
    card.pack_propagate(False)

    heading = ctk.CTkFrame(card, height=52, fg_color="transparent", corner_radius=0)
    heading.pack(fill="x", padx=16)
    heading.pack_propagate(False)
    ctk.CTkLabel(
        heading,
        text=_review_card_title(rows, source),
        text_color=widgets.COLORS["green"] if source == "truth" else widgets.COLORS["ink"],
        font=widgets.FONTS["card_title"],
        anchor="w",
    ).pack(side="left", fill="y")
    source_label = {"truth": "Truth", "dependent": "Dependent", "single": "Review"}[source]
    row_label = "row" if len(refs) == 1 else "rows"
    ctk.CTkLabel(
        heading,
        text=f"{source_label}  ·  {len(refs)} {row_label}",
        fg_color=widgets.COLORS["green_light"] if source == "truth" else widgets.COLORS["panel_alt"],
        text_color=widgets.COLORS["green"] if source == "truth" else widgets.COLORS["muted"],
        font=widgets.FONTS["body_tiny"],
        height=26,
        corner_radius=7,
    ).pack(side="right", pady=13, ipadx=8)

    body = ctk.CTkFrame(card, fg_color=widgets.COLORS["paper"], corner_radius=0)
    body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    if len(refs) <= 1:
        table = ctk.CTkFrame(body, fg_color=widgets.COLORS["paper"], corner_radius=0)
        table.pack(side="left", fill="both", expand=True)
    else:
        table = widgets.horizontal_scrollable_frame(body)
    if not refs:
        ctk.CTkLabel(table, text="No rows in this section", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body"], width=240).grid(row=0, column=0, padx=18, pady=18)
        return
    for column, ref in enumerate(refs):
        table.grid_columnconfigure(column, minsize=_REVIEW_RECORD_WIDTH, weight=0)
        _build_record_header(app, table, ref, column, source)
        for row, (_role, _position, truth_field, dependent_field) in enumerate(rows, 1):
            field = truth_field if source in ("truth", "single") else dependent_field
            _build_review_cell(app, table, ref, field, row, column)


def _build_record_header(app, table, ref: RecordRef, column: int, source: str):
    header = ctk.CTkFrame(table, height=_REVIEW_HEADER_HEIGHT, fg_color=widgets.COLORS["truth_header"] if source == "truth" else widgets.COLORS["panel_header"], border_color=widgets.COLORS["line"], border_width=1, corner_radius=0)
    header.grid(row=0, column=column, sticky="nsew")
    header.grid_propagate(False)
    ctk.CTkCheckBox(
        header,
        text=f"ROW {ref.index + 2}",
        variable=app.keep_vars[ref],
        fg_color=widgets.COLORS["green"],
        hover_color=widgets.COLORS["green_hover"],
        border_color=widgets.COLORS["line"],
        text_color=widgets.COLORS["green"],
        font=widgets.FONTS["section"],
        corner_radius=6,
    ).pack(anchor="w", padx=12, pady=12)
    table.grid_rowconfigure(0, minsize=_REVIEW_HEADER_HEIGHT)


def _build_review_cell(app, table, ref: RecordRef, field: str | None, row: int, column: int):
    bg = widgets.COLORS["paper"] if row % 2 else widgets.COLORS["panel_subtle"]
    cell_frame = ctk.CTkFrame(table, height=_REVIEW_ROW_HEIGHT, fg_color=bg, corner_radius=0)
    cell_frame.grid(row=row, column=column, sticky="nsew")
    cell_frame.grid_propagate(False)
    table.grid_rowconfigure(row, minsize=_REVIEW_ROW_HEIGHT)
    if field is None:
        ctk.CTkLabel(cell_frame, text="Not mapped", text_color=widgets.COLORS["muted"], font=widgets.FONTS["body_small"]).pack(fill="both", expand=True, padx=12)
        return
    cell = ctk.CTkRadioButton(
        cell_frame,
        text="",
        variable=app.field_vars[field],
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
        textvariable=app.edit_vars[(ref, field)],
        state="normal" if app._review_field_editable(ref, field) else "disabled",
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
        valued_fallback = next(
            (ref for ref in selected if app.edit_vars[(ref, field)].get()),
            None,
        )
        current_has_value = (
            current in selected_refs
            and bool(app.edit_vars[(current, field)].get())
        )
        if current_has_value or (current in selected_refs and valued_fallback is None):
            continue
        fallback = valued_fallback or preferred
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
