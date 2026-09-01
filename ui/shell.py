"""Application shell: sidebar navigation, top bar, and page host."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui import widgets
from ui.styles import APP_STYLESHEET


def setup_styles(app) -> None:
    app.setStyleSheet(APP_STYLESHEET)


def build(app) -> None:
    root = QWidget()
    root.setObjectName("appRoot")
    app.setCentralWidget(root)

    root_layout = QHBoxLayout(root)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    sidebar = QWidget()
    sidebar.setObjectName("sidebar")
    sidebar.setFixedWidth(224)
    side = QVBoxLayout(sidebar)
    side.setContentsMargins(18, 22, 18, 18)
    side.setSpacing(8)

    brand_row = QHBoxLayout()
    brand_row.setSpacing(10)
    mark = QLabel("✦")
    mark.setObjectName("brandMark")
    mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name = QLabel("CSV Scrubber")
    name.setObjectName("brandName")
    brand_row.addWidget(mark)
    brand_row.addWidget(name)
    brand_row.addStretch()
    side.addLayout(brand_row)
    side.addSpacing(28)

    navigation = QLabel("WORKFLOW")
    navigation.setObjectName("navSection")
    side.addWidget(navigation)

    app.nav_buttons: dict[str, QPushButton] = {}
    items = (
        ("setup", "Setup", app.show_workspace),
        ("analyze", "Analyze", app.show_analyze),
        ("review", "Review", app.show_review),
        ("complete", "Complete", app.show_complete),
        ("settings", "Settings", app.show_settings),
    )
    for key, label, callback in items:
        control = widgets.button(label, callback, "nav")
        app.nav_buttons[key] = control
        side.addWidget(control)

    side.addStretch()
    privacy = QLabel("●  Files stay on this computer")
    privacy.setObjectName("privacy")
    privacy.setWordWrap(True)
    side.addWidget(privacy)

    right = QWidget()
    right_layout = QVBoxLayout(right)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)

    topbar = QWidget()
    topbar.setObjectName("topbar")
    topbar.setFixedHeight(60)
    top = QHBoxLayout(topbar)
    top.setContentsMargins(32, 0, 32, 0)
    app.crumb = QLabel("Setup")
    app.crumb.setObjectName("crumb")
    top.addWidget(app.crumb)
    top.addStretch()
    status = QLabel("Local workspace")
    status.setObjectName("muted")
    top.addWidget(status)

    app.body = QWidget()
    app.body.setObjectName("pageHost")
    app.body_layout = QVBoxLayout(app.body)
    app.body_layout.setContentsMargins(0, 0, 0, 0)
    app.body_layout.setSpacing(0)

    right_layout.addWidget(topbar)
    right_layout.addWidget(app.body, 1)
    root_layout.addWidget(sidebar)
    root_layout.addWidget(right, 1)


def set_nav(app, active: str) -> None:
    for key, control in app.nav_buttons.items():
        control.setProperty("active", key == active)
        control.style().unpolish(control)
        control.style().polish(control)
    app.crumb.setText(active.capitalize())
