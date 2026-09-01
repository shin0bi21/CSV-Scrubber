"""Setup view for selecting CSV sources and matching columns."""

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui import widgets


def render_workspace(app, mode: str) -> None:
    app.crumb.setText(
        f"Setup  ›  {'Single file' if mode == 'single' else 'Multi-file'}"
    )
    outer = widgets.page(
        app,
        "Setup",
        "Choose the files and columns for this duplicate scan.",
    )

    mode_row = QHBoxLayout()
    mode_row.setSpacing(8)
    mode_label = QLabel("SCAN MODE")
    mode_label.setObjectName("navSection")
    mode_row.addWidget(mode_label)
    group = QButtonGroup(app)
    group.setExclusive(True)
    for value, label in (("single", "Single file"), ("multi", "Multi-file")):
        control = widgets.button(
            label,
            lambda _checked=False, value=value: app.show_workspace(value),
            "segment",
            checkable=True,
        )
        control.setChecked(value == mode)
        group.addButton(control)
        mode_row.addWidget(control)
    mode_row.addStretch()
    outer.addLayout(mode_row)
    outer.addSpacing(2)

    if mode == "single":
        _render_single(app, outer)
    else:
        _render_multi(app, outer)
    outer.addStretch()


def _source_contents(app, source, file_label: str) -> QWidget:
    content = QWidget()
    layout = QVBoxLayout(content)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(14)
    layout.addWidget(widgets.source_picker(app, source, file_label))
    layout.addWidget(
        widgets.column_picker(
            app,
            source,
            "Match columns",
            "match_columns",
        )
    )
    layout.addWidget(
        widgets.column_picker(
            app,
            source,
            "Reference columns",
            "reference_columns",
        )
    )
    return content


def _render_single(app, outer: QVBoxLayout) -> None:
    title = QLabel("Find duplicates in one CSV")
    title.setObjectName("cardTitle")
    outer.addWidget(title)
    frame = widgets.card()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(_source_contents(app, app.single, "CSV file"))
    actions = QHBoxLayout()
    actions.setContentsMargins(20, 0, 20, 20)
    actions.addStretch()
    actions.addWidget(
        widgets.button(
            "Scan for duplicates",
            lambda: app.start_scan("single"),
            "primary",
        )
    )
    layout.addLayout(actions)
    outer.addWidget(frame)


def _source_card(app, source, title: str, file_label: str):
    frame = widgets.card()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    header = QHBoxLayout()
    header.setContentsMargins(20, 18, 20, 0)
    label = QLabel(title)
    label.setObjectName("cardTitle")
    header.addWidget(label)
    header.addStretch()
    layout.addLayout(header)
    layout.addWidget(_source_contents(app, source, file_label))
    return frame


def _render_multi(app, outer: QVBoxLayout) -> None:
    title = QLabel("Reconcile two CSV sources")
    title.setObjectName("cardTitle")
    outer.addWidget(title)
    cards = QHBoxLayout()
    cards.setSpacing(14)
    cards.addWidget(
        _source_card(app, app.truth, "Source of truth", "Truth CSV"),
        1,
    )
    cards.addWidget(
        _source_card(app, app.dependent, "Dependent source", "Dependent CSV"),
        1,
    )
    outer.addLayout(cards)
    actions = QHBoxLayout()
    actions.addStretch()
    actions.addWidget(
        widgets.button(
            "Scan for duplicates",
            lambda: app.start_scan("multi"),
            "primary",
        )
    )
    outer.addLayout(actions)
