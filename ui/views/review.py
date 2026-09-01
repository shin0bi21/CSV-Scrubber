"""Side-by-side duplicate review with native horizontal table scrolling."""

from itertools import zip_longest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from engine import MatchGroup, RecordRef
from ui import widgets


RECORD_WIDTH = 250
HEADER_HEIGHT = 50
FIELD_ROW_HEIGHT = 62


def render_review(app) -> None:
    mode_name = "Single-file" if app.scan_mode == "single" else "Multi-file"
    app.crumb.setText(f"Review  ›  {mode_name}")
    outer = widgets.page(
        app,
        "Review",
        "Select rows to keep, or choose field values for a merged record.",
    )

    if not app.groups:
        _render_empty(app, outer)
        return

    group = app.groups[app.group_index]
    group_row = QHBoxLayout()
    group_label = QLabel(
        f"GROUP {app.group_index + 1} OF {len(app.groups)}"
    )
    group_label.setObjectName("navSection")
    group_row.addWidget(group_label)
    group_row.addStretch()
    group_row.addWidget(widgets.badge(f"{group.score:.0f}% MATCH"))
    outer.addLayout(group_row)
    outer.addWidget(_match_summary(group))

    _initialize_review_state(app, group)
    if app.scan_mode == "multi":
        splitter = _cross_source_tables(app, group)
    else:
        fields = [
            ("FIELD", position, field, field)
            for position, field in enumerate(app._headers_for_review(group), 1)
        ]
        splitter = QSplitter(Qt.Orientation.Horizontal)
        review_card = _review_card(app, group.records, fields, "single")
        splitter.addWidget(review_card)
        splitter.setFixedHeight(review_card.review_height)
    outer.addWidget(splitter)
    outer.addStretch(1)
    _review_actions(app, outer)
    _refresh_field_choices(app)
    _update_selection_status(app)


def _render_empty(app, outer) -> None:
    frame = widgets.card()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 22, 22, 22)
    title = QLabel("No review is ready yet")
    title.setObjectName("cardTitle")
    note = QLabel("Run a scan from Setup first.")
    note.setObjectName("muted")
    layout.addWidget(title)
    layout.addWidget(note)
    layout.addWidget(
        widgets.button("Back to Setup", app.show_workspace, "secondary"),
        0,
        Qt.AlignmentFlag.AlignLeft,
    )
    outer.addWidget(frame)
    outer.addStretch()


def _match_summary(group: MatchGroup) -> QFrame:
    summary = QFrame()
    summary.setObjectName("summary")
    layout = QHBoxLayout(summary)
    layout.setContentsMargins(16, 7, 10, 7)
    layout.setSpacing(10)
    reason = QLabel(
        "Match reason: " + ("  •  ".join(group.reasons) or "Candidate match")
    )
    reason.setObjectName("muted")
    layout.addWidget(reason, 1)
    details = "\n\n".join(_match_evidence_lines(group))
    if not details:
        details = "No additional token-level evidence is available."
    layout.addWidget(
        widgets.MatchInfoButton("Match info", details, summary)
    )
    return summary


def _match_evidence_lines(group: MatchGroup) -> list[str]:
    lines: list[str] = []
    for (left_ref, right_ref), evidence in group.evidence.items():
        pair = (
            f"{left_ref.source} row {left_ref.index + 2} ↔ "
            f"{right_ref.source} row {right_ref.index + 2}"
        )
        parts: list[str] = []
        exact = ", ".join(left for left, _right in evidence.exact_token_matches)
        fuzzy = ", ".join(
            f"{left} ↔ {right} ({similarity:.0f}%)"
            for left, right, similarity in evidence.fuzzy_token_matches
        )
        unmatched = ", ".join(
            evidence.unmatched_left_tokens + evidence.unmatched_right_tokens
        )
        if exact:
            parts.append(f"Exact: {exact}")
        if fuzzy:
            parts.append(f"Fuzzy: {fuzzy}")
        if unmatched:
            parts.append(f"Unmatched: {unmatched}")
        parts.append(
            f"Coverage: {evidence.shorter_name_coverage:.0f}% short / "
            f"{evidence.longer_name_coverage:.0f}% long"
        )
        lines.append(pair + "\n" + " • ".join(parts))
    return lines


def _initialize_review_state(app, group: MatchGroup) -> None:
    default_ref = next(
        (ref for ref in group.records if ref.source == "truth"),
        group.records[0],
    )
    app.keep_checks = {}
    app.field_choices = {}
    app.field_buttons = {}
    app.field_groups = {}
    app.edit_inputs = {}
    for field in app._headers_for_review(group):
        app.field_choices[field] = _preferred_ref(app, group, field, default_ref)
        app.field_buttons[field] = {}
        app.field_groups[field] = QButtonGroup()
    app.default_review_ref = default_ref


def _preferred_ref(
    app,
    group: MatchGroup,
    field: str,
    default_ref: RecordRef,
) -> RecordRef:
    if app._row_for(default_ref).get(field, ""):
        return default_ref
    return next(
        (
            ref
            for ref in group.records
            if app._row_for(ref).get(field, "")
        ),
        default_ref,
    )


def _paired_review_fields(app):
    rows = []
    seen = set()
    sections = (
        ("MATCH", app.truth.match_columns, app.dependent.match_columns),
        (
            "REFERENCE",
            app.truth.reference_columns,
            app.dependent.reference_columns,
        ),
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


def _cross_source_tables(app, group: MatchGroup) -> QSplitter:
    truth_refs = [ref for ref in group.records if ref.source == "truth"]
    dependent_refs = [
        ref for ref in group.records if ref.source == "dependent"
    ]
    fields = _paired_review_fields(app)
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setChildrenCollapsible(False)
    truth_card = _review_card(app, truth_refs, fields, "truth")
    dependent_card = _review_card(
        app,
        dependent_refs,
        fields,
        "dependent",
    )
    splitter.addWidget(truth_card)
    splitter.addWidget(dependent_card)
    splitter.setFixedHeight(
        max(truth_card.review_height, dependent_card.review_height)
    )
    truth_scroll = truth_card.review_table.verticalScrollBar()
    dependent_scroll = dependent_card.review_table.verticalScrollBar()
    truth_scroll.valueChanged.connect(dependent_scroll.setValue)
    dependent_scroll.valueChanged.connect(truth_scroll.setValue)
    if len(truth_refs) == 1:
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([400, 600])
    else:
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 500])
    return splitter


def _card_fields(rows, source: str) -> list[str]:
    fields: list[str] = []
    for _role, _position, truth_field, dependent_field in rows:
        field = (
            truth_field
            if source in ("truth", "single")
            else dependent_field
        )
        if field and field not in fields:
            fields.append(field)
    return fields


def _review_card(app, refs, rows, source: str) -> QFrame:
    frame = widgets.card()
    frame.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 12)
    layout.setSpacing(8)

    fields = _card_fields(rows, source)
    header = QHBoxLayout()
    title = QLabel(" / ".join(fields) or "Unmapped fields")
    title.setObjectName("cardTitle")
    source_label = {
        "truth": "Truth",
        "dependent": "Dependent",
        "single": "Review",
    }[source]
    row_word = "row" if len(refs) == 1 else "rows"
    header.addWidget(title)
    header.addStretch()
    header.addWidget(
        widgets.badge(
            f"{source_label} · {len(refs)} {row_word}",
            muted=source == "dependent",
        )
    )
    layout.addLayout(header)

    if not refs:
        empty = QLabel("No rows in this section")
        empty.setObjectName("muted")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(empty, 1)
        frame.review_height = 190
        frame.setFixedHeight(frame.review_height)
        frame.review_table = QTableWidget(frame)
        frame.review_table.hide()
        return frame

    table = QTableWidget(len(rows) + 1, len(refs))
    table.setObjectName("reviewTable")
    table.horizontalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setShowGrid(True)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setHorizontalScrollMode(
        QAbstractItemView.ScrollMode.ScrollPerPixel
    )
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAsNeeded
    )
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    table.setSizeAdjustPolicy(
        QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored
    )
    visible_fields = max(1, min(len(rows), 6))
    table_height = (
        HEADER_HEIGHT + FIELD_ROW_HEIGHT * visible_fields + 22
    )
    table.setFixedHeight(table_height)

    show_field_labels = len(rows) > 1
    table.verticalHeader().setVisible(show_field_labels)
    if show_field_labels:
        labels = [""]
        for _role, _position, truth_field, dependent_field in rows:
            labels.append(
                (
                    truth_field
                    if source in ("truth", "single")
                    else dependent_field
                )
                or "Not mapped"
            )
        table.setVerticalHeaderLabels(labels)
        table.verticalHeader().setMinimumWidth(105)

    table.setRowHeight(0, HEADER_HEIGHT)
    for row_index in range(1, len(rows) + 1):
        table.setRowHeight(row_index, FIELD_ROW_HEIGHT)
    for column, ref in enumerate(refs):
        table.setColumnWidth(column, RECORD_WIDTH)
        table.setCellWidget(0, column, _record_header(app, ref))
        for row_index, row in enumerate(rows, 1):
            field = row[2] if source in ("truth", "single") else row[3]
            table.setCellWidget(
                row_index,
                column,
                _review_cell(app, ref, field),
            )

    layout.addWidget(table, 1)
    frame.review_table = table
    frame.review_height = table_height + 64
    frame.setFixedHeight(frame.review_height)
    return frame


def _record_header(app, ref: RecordRef) -> QWidget:
    host = QWidget()
    layout = QHBoxLayout(host)
    layout.setContentsMargins(12, 4, 12, 4)
    control = QCheckBox(f"ROW {ref.index + 2}")
    control.setChecked(ref == app.default_review_ref)
    control.toggled.connect(lambda: _selection_changed(app))
    app.keep_checks[ref] = control
    layout.addWidget(control)
    layout.addStretch()
    return host


def _review_cell(app, ref: RecordRef, field: str | None) -> QWidget:
    host = QWidget()
    layout = QHBoxLayout(host)
    layout.setContentsMargins(10, 7, 10, 7)
    layout.setSpacing(8)
    if field is None:
        label = QLabel("Not mapped")
        label.setObjectName("muted")
        layout.addWidget(label)
        return host

    choice = QRadioButton()
    choice.setChecked(app.field_choices[field] == ref)
    choice.toggled.connect(
        lambda checked, field=field, ref=ref: (
            app.field_choices.__setitem__(field, ref) if checked else None
        )
    )
    app.field_groups[field].addButton(choice)
    app.field_buttons[field][ref] = choice

    value = QLineEdit(app._row_for(ref).get(field, ""))
    value.setReadOnly(not app._review_field_editable(ref, field))
    app.edit_inputs[(ref, field)] = value
    layout.addWidget(choice)
    layout.addWidget(value, 1)
    return host


def _selection_changed(app) -> None:
    _refresh_field_choices(app)
    _update_selection_status(app)


def _ui_value(app, ref: RecordRef, field: str) -> str:
    control = app.edit_inputs.get((ref, field))
    if control is not None:
        return control.text()
    return app._row_for(ref).get(field, "")


def _refresh_field_choices(app) -> None:
    selected = [
        ref for ref, control in app.keep_checks.items() if control.isChecked()
    ]
    selected_refs = set(selected)
    for field, controls in app.field_buttons.items():
        for ref, control in controls.items():
            control.setEnabled(ref in selected_refs)
    if not selected:
        return

    preferred = next(
        (ref for ref in selected if ref.source == "truth"),
        selected[0],
    )
    for field, current in list(app.field_choices.items()):
        valid_controls = app.field_buttons.get(field, {})
        candidates = [ref for ref in selected if ref in valid_controls]
        if not candidates:
            continue
        valued = next(
            (ref for ref in candidates if _ui_value(app, ref, field)),
            None,
        )
        current_valid = current in candidates
        current_has_value = current_valid and bool(
            _ui_value(app, current, field)
        )
        if current_has_value or (current_valid and valued is None):
            continue
        fallback = valued or (
            preferred if preferred in candidates else candidates[0]
        )
        app.field_choices[field] = fallback
        valid_controls[fallback].setChecked(True)


def _update_selection_status(app) -> None:
    selected = sum(
        control.isChecked() for control in app.keep_checks.values()
    )
    if selected == 0:
        message = "No rows selected."
    elif selected == 1:
        message = "1 row selected. Merge uses values from that row."
    else:
        message = (
            f"{selected} rows selected. Keep retains all; Merge combines "
            "their field choices."
        )
    app.selection_status_label.setText(message)


def _review_actions(app, outer: QVBoxLayout) -> None:
    actions = QHBoxLayout()
    app.selection_status_label = QLabel()
    app.selection_status_label.setObjectName("muted")
    actions.addWidget(app.selection_status_label)
    actions.addWidget(
        widgets.button(
            "Not duplicates",
            lambda: app.resolve("not_duplicate"),
            "ghost",
        )
    )
    actions.addStretch()
    actions.addWidget(
        widgets.button(
            "Merge selected rows",
            lambda: app.resolve("merge"),
            "primary",
        )
    )
    actions.addWidget(
        widgets.button(
            "Keep selected rows",
            lambda: app.resolve("keep"),
            "secondary",
        )
    )
    outer.addLayout(actions)
