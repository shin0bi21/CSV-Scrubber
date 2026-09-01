"""Reusable PySide6 widgets for the desktop interface."""

from collections.abc import Callable, Iterable

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.styles import COLORS


def clear_layout(layout) -> None:
    """Delete every widget and nested layout from a layout."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget() is not None:
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())


def button(
    text: str,
    command: Callable | None = None,
    variant: str = "secondary",
    *,
    checkable: bool = False,
) -> QPushButton:
    control = QPushButton(text)
    control.setProperty("variant", variant)
    control.setCursor(Qt.CursorShape.PointingHandCursor)
    control.setCheckable(checkable)
    if command is not None:
        control.clicked.connect(lambda _checked=False: command())
    return control


def page(app, title: str, subtitle: str = "") -> QVBoxLayout:
    """Replace the page host contents and return the new page layout."""
    clear_layout(app.body_layout)
    host = QWidget()
    host.setObjectName("page")
    layout = QVBoxLayout(host)
    layout.setContentsMargins(34, 28, 34, 24)
    layout.setSpacing(14)

    title_label = QLabel(title)
    title_label.setObjectName("pageTitle")
    layout.addWidget(title_label)
    if subtitle:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
    layout.addSpacing(8)
    app.body_layout.addWidget(host)
    return layout


def card(parent: QWidget | None = None) -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName("card")
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return frame


def badge(text: str, *, muted: bool = False) -> QLabel:
    label = QLabel(text)
    label.setObjectName("badgeMuted" if muted else "badge")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return label


def source_picker(app, source, title: str) -> QWidget:
    """Create a file-source row with a native file chooser."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    label = QLabel(title)
    label.setObjectName("sectionTitle")
    label.setFixedWidth(150)
    path = QLineEdit(source.path or "")
    path.setReadOnly(True)
    path.setPlaceholderText("Choose a CSV file")
    browse = button("Browse…", lambda: app.load_source(source), "secondary")

    layout.addWidget(label)
    layout.addWidget(path, 1)
    layout.addWidget(browse)
    return row


class ColumnSelectionDialog(QDialog):
    """Small reusable dialog for choosing CSV columns."""

    def __init__(
        self,
        parent: QWidget,
        title: str,
        headers: Iterable[str],
        selected: Iterable[str],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(440, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        prompt = QLabel("Select one or more columns.")
        prompt.setObjectName("muted")
        layout.addWidget(prompt)

        selected_set = set(selected)
        self.list_widget = QListWidget()
        for header in headers:
            item = QListWidgetItem(header)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if header in selected_set
                else Qt.CheckState.Unchecked
            )
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget, 1)

        controls = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        controls.rejected.connect(self.reject)
        controls.accepted.connect(self.accept)
        layout.addWidget(controls)

    def selected_columns(self) -> list[str]:
        return [
            self.list_widget.item(index).text()
            for index in range(self.list_widget.count())
            if self.list_widget.item(index).checkState() == Qt.CheckState.Checked
        ]


def choose_columns(
    parent: QWidget,
    title: str,
    headers: Iterable[str],
    selected: Iterable[str],
) -> list[str] | None:
    dialog = ColumnSelectionDialog(parent, title, headers, selected)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.selected_columns()


def column_picker(
    app,
    source,
    title: str,
    attribute: str,
    *,
    button_text: str = "Choose columns",
) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    label = QLabel(title)
    label.setObjectName("sectionTitle")
    label.setFixedWidth(150)
    current = QLabel(", ".join(getattr(source, attribute)) or "None selected")
    current.setObjectName("muted")
    current.setWordWrap(True)

    def open_dialog() -> None:
        chosen = choose_columns(
            app,
            title,
            source.headers,
            getattr(source, attribute),
        )
        if chosen is not None:
            app.apply_column_selection(source, attribute, chosen)

    control = button(button_text, open_dialog, "secondary")
    control.setEnabled(bool(source.headers))
    layout.addWidget(label)
    layout.addWidget(current, 1)
    layout.addWidget(control)
    return row


def progress_dialog(parent: QWidget, text: str) -> QProgressDialog:
    dialog = QProgressDialog(text, "", 0, 0, parent)
    dialog.setWindowTitle("CSV Scrubber")
    dialog.setCancelButton(None)
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    dialog.show()
    return dialog


class MatchInfoPopover(QFrame):
    def __init__(self, owner: QWidget, text: str) -> None:
        super().__init__(owner, Qt.WindowType.ToolTip)
        self.owner = owner
        self.pinned = False
        self.setObjectName("matchPopover")
        self.setMinimumWidth(520)
        self.setMaximumWidth(720)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        title = QLabel("Match details")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        details = QPlainTextEdit(text)
        details.setReadOnly(True)
        details.setMinimumHeight(140)
        details.setMaximumHeight(260)
        layout.addWidget(details)

    def show_below_owner(self) -> None:
        point = self.owner.mapToGlobal(QPoint(0, self.owner.height() + 6))
        screen = self.owner.screen().availableGeometry()
        self.adjustSize()
        x = min(point.x(), screen.right() - self.width())
        y = min(point.y(), screen.bottom() - self.height())
        self.move(max(screen.left(), x), max(screen.top(), y))
        self.show()
        self.raise_()

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().leaveEvent(event)
        if not self.pinned:
            QTimer.singleShot(120, self.hide_if_unhovered)

    def hide_if_unhovered(self) -> None:
        if not self.pinned and not self.underMouse() and not self.owner.underMouse():
            self.hide()


class MatchInfoButton(QPushButton):
    """A hover card that can be pinned open with a click."""

    def __init__(self, text: str, details: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("variant", "link")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.popover = MatchInfoPopover(self, details)
        self.clicked.connect(self.toggle_popover)

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().enterEvent(event)
        self.popover.show_below_owner()

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().leaveEvent(event)
        if not self.popover.pinned:
            QTimer.singleShot(120, self.popover.hide_if_unhovered)

    def toggle_popover(self) -> None:
        if self.popover.isVisible() and self.popover.pinned:
            self.popover.pinned = False
            self.popover.hide()
        else:
            self.popover.pinned = True
            self.popover.show_below_owner()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Hide:
            self.popover.pinned = False
            self.popover.hide()
        return super().event(event)
