"""Completion and export view."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from ui import widgets


def render_complete(app) -> None:
    app.crumb.setText("Complete")
    outer = widgets.page(
        app,
        "Review complete",
        "Export the clean CSV and its companion audit log.",
    )
    frame = widgets.card()
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(18)

    icon = QLabel("✓")
    icon.setObjectName("badge")
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setFixedSize(60, 60)
    layout.addWidget(icon)

    copy = QVBoxLayout()
    title = QLabel(f"{len(app.decisions)} duplicate groups resolved")
    title.setObjectName("cardTitle")
    note = QLabel("Nothing is overwritten. Export creates new files.")
    note.setObjectName("muted")
    copy.addWidget(title)
    copy.addWidget(note)
    layout.addLayout(copy, 1)
    layout.addWidget(
        widgets.button("Export cleaned CSV", app.export_results, "primary")
    )
    outer.addWidget(frame)
    outer.addStretch()
