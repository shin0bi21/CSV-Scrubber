"""Reusable PySide6 widgets for the desktop interface."""

from collections.abc import Callable, Iterable

from PySide6.QtCore import QEvent, QPoint, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
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


def slider_row(
    title: str,
    value: int,
    minimum: int,
    maximum: int,
    *,
    suffix: str = "",
) -> tuple[QWidget, QSlider]:
    """Create a labeled integer slider with a live value badge."""

    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)
    label = QLabel(title)
    label.setObjectName("muted")
    label.setFixedWidth(210)
    control = QSlider(Qt.Orientation.Horizontal)
    control.setRange(minimum, maximum)
    control.setSingleStep(1)
    control.setValue(value)
    current = badge(f"{value}{suffix}")
    current.setMinimumWidth(64)
    control.valueChanged.connect(
        lambda new_value: current.setText(f"{new_value}{suffix}")
    )
    layout.addWidget(label)
    layout.addWidget(control, 1)
    layout.addWidget(current)
    return row, control


def source_picker(
    title: str,
    path_value: str,
    on_browse: Callable[[], None],
) -> QWidget:
    """Create a file-source row with a native file chooser."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    label = QLabel(title)
    label.setObjectName("sectionTitle")
    label.setFixedWidth(150)
    path = QLineEdit(path_value)
    path.setReadOnly(True)
    path.setPlaceholderText("Choose a CSV file")
    browse = button("Browse…", on_browse, "secondary")

    layout.addWidget(label)
    layout.addWidget(path, 1)
    layout.addWidget(browse)
    return row


class PopoverCard(QFrame):
    """Reusable anchored popup frame with a customizable content layout."""

    def __init__(
        self,
        owner: QWidget,
        *,
        width: int,
        height: int | None = None,
        window_type: Qt.WindowType = Qt.WindowType.Popup,
    ) -> None:
        super().__init__(owner, window_type)
        self.owner = owner
        self.setObjectName("popoverCard")
        self.setFixedWidth(width)
        if height is not None:
            self.setFixedHeight(height)
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(18, 16, 18, 16)
        self.content_layout.setSpacing(12)

    def show_below_owner(self, *, align_right: bool = False) -> None:
        self.adjustSize()
        x_offset = self.owner.width() - self.width() if align_right else 0
        below = self.owner.mapToGlobal(
            QPoint(x_offset, self.owner.height() + 6)
        )
        above = self.owner.mapToGlobal(QPoint(x_offset, -self.height() - 6))
        screen = self.owner.screen().availableGeometry()
        x = min(max(screen.left(), below.x()), screen.right() - self.width())
        y = (
            above.y()
            if below.y() + self.height() > screen.bottom()
            else below.y()
        )
        self.move(x, max(screen.top(), y))
        self.show()
        self.raise_()


class ColumnOption(QCheckBox):
    """A full-row checkbox with a clear selected state."""

    def __init__(self, column_name: str, checked: bool) -> None:
        super().__init__()
        self.column_name = column_name
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(46)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

    def hitButton(self, position: QPoint) -> bool:  # noqa: N802 - Qt API
        return self.rect().contains(position)

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().leaveEvent(event)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_row(painter)
        self._paint_checkbox(painter)
        self._paint_label(painter)

    def _paint_row(self, painter: QPainter) -> None:
        row = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        selected = self.isChecked()
        background = (
            COLORS["green_light"]
            if selected
            else COLORS["panel_subtle"]
            if self.underMouse()
            else COLORS["paper"]
        )
        border = COLORS["green"] if selected or self.hasFocus() else COLORS["line"]
        painter.setPen(QPen(QColor(border), 1))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(row, 9, 9)

    def _paint_checkbox(self, painter: QPainter) -> None:
        selected = self.isChecked()
        box = QRectF(15, (self.height() - 20) / 2, 20, 20)
        border = COLORS["green"] if selected else COLORS["line"]
        fill = COLORS["green"] if selected else COLORS["paper"]
        painter.setPen(QPen(QColor(border), 1.5))
        painter.setBrush(QColor(fill))
        painter.drawRoundedRect(box, 5, 5)
        if selected:
            self._paint_checkmark(painter, box)

    @staticmethod
    def _paint_checkmark(painter: QPainter, box: QRectF) -> None:
        check = QPainterPath()
        check.moveTo(box.left() + 5, box.center().y())
        check.lineTo(box.left() + 9, box.bottom() - 5)
        check.lineTo(box.right() - 4, box.top() + 5)
        check_pen = QPen(QColor(COLORS["paper"]), 2.2)
        check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(check_pen)
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )
        painter.drawPath(check)

    def _paint_label(self, painter: QPainter) -> None:
        selected = self.isChecked()
        font = self.font()
        font.setBold(selected)
        painter.setFont(font)
        painter.setPen(
            QColor(COLORS["green"] if selected else COLORS["ink"])
        )
        text_rect = QRectF(50, 0, self.width() - 64, self.height())
        text = painter.fontMetrics().elidedText(
            self.column_name,
            Qt.TextElideMode.ElideRight,
            int(text_rect.width()),
        )
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            text,
        )


class ColumnSelectionPopover(PopoverCard):
    """Anchored column selector built on the shared popover skeleton."""

    def __init__(
        self,
        owner: QWidget,
        title: str,
        headers: Iterable[str],
        selected: Iterable[str],
        on_apply: Callable[[list[str]], None],
    ) -> None:
        super().__init__(owner, width=500, height=520)
        self.setObjectName("columnPopover")
        self.on_apply = on_apply
        self.initial_selected = set(selected)
        layout = self.content_layout
        layout.addLayout(self._header(title))

        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter columns…")
        layout.addWidget(self.search)

        self.options: list[ColumnOption] = []
        layout.addWidget(self._options_panel(headers), 1)
        layout.addLayout(self._footer())
        self.search.textChanged.connect(self._filter_options)
        self._update_selection_count()

    def _header(self, title: str) -> QHBoxLayout:
        header = QHBoxLayout()
        prompt = QLabel(title)
        prompt.setObjectName("cardTitle")
        self.selection_count = QLabel()
        self.selection_count.setObjectName("badgeMuted")
        header.addWidget(prompt)
        header.addStretch()
        header.addWidget(self.selection_count)
        return header

    def _options_panel(self, headers: Iterable[str]) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        option_host = QWidget()
        option_layout = QVBoxLayout(option_host)
        option_layout.setContentsMargins(2, 2, 2, 2)
        option_layout.setSpacing(7)
        for header in headers:
            option = ColumnOption(header, header in self.initial_selected)
            option.toggled.connect(
                lambda _checked: self._update_selection_count()
            )
            self.options.append(option)
            option_layout.addWidget(option)
        option_layout.addStretch()
        scroll.setWidget(option_host)
        return scroll

    def _footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()
        footer.addWidget(button("Select all", self._select_all, "ghost"))
        footer.addWidget(button("Clear", self._clear, "ghost"))
        footer.addStretch()
        footer.addWidget(button("Cancel", self.hide, "secondary"))
        footer.addWidget(button("Apply columns", self._apply, "primary"))
        return footer

    def open(self) -> None:
        self.search.clear()
        self.show_below_owner(align_right=True)
        self.search.setFocus()

    def hideEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().hideEvent(event)
        for option in self.options:
            option.setChecked(option.column_name in self.initial_selected)

    def _filter_options(self, query: str) -> None:
        query = query.strip().casefold()
        for option in self.options:
            option.setVisible(query in option.column_name.casefold())

    def _select_all(self) -> None:
        for option in self.options:
            option.setChecked(True)

    def _clear(self) -> None:
        for option in self.options:
            option.setChecked(False)

    def _apply(self) -> None:
        selected = self.selected_columns()
        self.initial_selected = set(selected)
        self.hide()
        self.on_apply(selected)

    def _update_selection_count(self) -> None:
        selected = sum(option.isChecked() for option in self.options)
        self.selection_count.setText(
            f"{selected} of {len(self.options)} selected"
        )

    def selected_columns(self) -> list[str]:
        return [
            option.column_name
            for option in self.options
            if option.isChecked()
        ]


def column_picker(
    title: str,
    headers: Iterable[str],
    selected: Iterable[str],
    on_apply: Callable[[list[str]], None],
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
    headers = list(headers)
    selected = list(selected)
    current = QLabel(", ".join(selected) or "None selected")
    current.setObjectName("muted")
    current.setWordWrap(True)

    control = button(button_text, variant="secondary")
    control.setEnabled(bool(headers))
    popover = ColumnSelectionPopover(
        control,
        title,
        headers,
        selected,
        on_apply,
    )
    control.popover = popover
    control.clicked.connect(lambda _checked=False: popover.open())
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


class MatchInfoPopover(PopoverCard):
    def __init__(self, owner: QWidget, text: str) -> None:
        super().__init__(
            owner,
            width=620,
            window_type=Qt.WindowType.ToolTip,
        )
        self.pinned = False
        self.setObjectName("matchPopover")
        self.setMaximumWidth(720)

        layout = self.content_layout
        title = QLabel("Match details")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        details = QPlainTextEdit(text)
        details.setReadOnly(True)
        details.setMinimumHeight(140)
        details.setMaximumHeight(260)
        layout.addWidget(details)

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
