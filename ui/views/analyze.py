"""Common-token analysis view."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
)

from ui import widgets


def render_analyze(app) -> None:
    mode_name = "Single-file" if app.scan_mode == "single" else "Multi-file"
    app.crumb.setText(f"Analyze  ›  {mode_name}")
    outer = widgets.page(
        app,
        "Analyze",
        "Review common tokens and tune how strongly they influence matching.",
    )

    note = QLabel(
        "Reference columns appear during review but never affect matching. "
        f"Analyzing: {_matching_columns_text(app)}."
    )
    note.setObjectName("muted")
    note.setWordWrap(True)
    outer.addWidget(note)

    app.token_weight_inputs = {}
    if not app.token_stats:
        frame = widgets.card()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(22, 22, 22, 22)
        empty = QLabel(
            "No token analysis yet. Load files and choose match columns in Setup, "
            "then run Analyze."
        )
        empty.setObjectName("muted")
        empty.setWordWrap(True)
        layout.addWidget(empty)
        outer.addWidget(frame)
    else:
        headings = ("Token", "Rows", "Share", "Auto", "Examples", "Weight")
        table = QTableWidget(len(app.token_stats), len(headings))
        table.setHorizontalHeaderLabels(headings)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setMinimumHeight(300)
        table.horizontalHeader().setStretchLastSection(False)
        table.setColumnWidth(0, 160)
        table.setColumnWidth(1, 70)
        table.setColumnWidth(2, 80)
        table.setColumnWidth(3, 80)
        table.setColumnWidth(4, 420)
        table.setColumnWidth(5, 110)
        for row, stat in enumerate(app.token_stats):
            values = (
                stat.token,
                str(stat.count),
                f"{stat.percentage:.1f}%",
                f"{stat.automatic_weight:.2f}",
                " | ".join(stat.examples),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row, column, item)
            default_weight = (
                f"{stat.weight:.2f}"
                if stat.token in app.rules.token_weights
                else "auto"
            )
            draft = app.token_weight_drafts.get(stat.token, default_weight)
            app.token_weight_drafts[stat.token] = draft
            weight = QLineEdit(draft)
            weight.setAlignment(Qt.AlignmentFlag.AlignRight)
            weight.textChanged.connect(
                lambda text, token=stat.token: app.token_weight_drafts.__setitem__(
                    token,
                    text,
                )
            )
            app.token_weight_inputs[stat.token] = weight
            table.setCellWidget(row, 5, weight)
            table.setRowHeight(row, 46)
        outer.addWidget(table, 1)

    actions = QHBoxLayout()
    actions.addWidget(
        widgets.button("Back to Setup", app.show_workspace, "ghost")
    )
    actions.addStretch()
    actions.addWidget(
        widgets.button("Run analysis", app.analyze_common_tokens, "primary")
    )
    outer.addLayout(actions)
    outer.addStretch()


def _matching_columns_text(app) -> str:
    if app.scan_mode == "single":
        return ", ".join(app.single.match_columns) or "no columns selected"
    truth = ", ".join(app.truth.match_columns) or "none"
    dependent = ", ".join(app.dependent.match_columns) or "none"
    return f"{truth} + {dependent}"
