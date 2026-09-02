"""Shared visual tokens and stylesheet for the PySide6 interface."""

COLORS = {
    "nav": "#10231B",
    "nav_active": "#254437",
    "green": "#267A55",
    "green_hover": "#1F6848",
    "green_light": "#E6F3EC",
    "bg": "#F3F6F4",
    "paper": "#FFFFFF",
    "line": "#DDE5E0",
    "ink": "#17221C",
    "muted": "#68756D",
    "amber": "#A46313",
    "text_on_dark": "#FFFFFF",
    "brand_bg": "#D7F0DF",
    "brand_fg": "#174E36",
    "nav_text": "#B5C8BE",
    "privacy_dot": "#5ED38B",
    "entry_bg": "#F8FAF8",
    "panel_header": "#F4F8F5",
    "panel_subtle": "#F8FAF9",
    "panel_alt": "#EDF1EF",
    "truth_header": "#E7F3EC",
    "warning": "#FFF4DF",
    "field_active": "#F0F7F3",
}

APP_STYLESHEET = """
QMainWindow, QWidget#appRoot, QWidget#pageHost {
    background: #F3F6F4;
    color: #17221C;
    font-family: "Segoe UI";
    font-size: 13px;
}
QWidget#sidebar {
    background: #10231B;
}
QWidget#topbar {
    background: #FFFFFF;
    border-bottom: 1px solid #DDE5E0;
}
QLabel#brandMark {
    min-width: 34px;
    min-height: 34px;
    border-radius: 9px;
    background: #D7F0DF;
    color: #174E36;
    font-size: 18px;
    font-weight: 700;
}
QLabel#brandName {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 700;
}
QLabel#navSection {
    color: #789286;
    font-size: 11px;
    font-weight: 700;
}
QLabel#privacy {
    color: #819A8E;
    font-size: 11px;
}
QLabel#crumb {
    color: #68756D;
    font-size: 12px;
}
QLabel#pageTitle {
    color: #17221C;
    font-size: 28px;
    font-weight: 700;
}
QLabel#pageSubtitle {
    color: #68756D;
    font-size: 13px;
}
QLabel#cardTitle {
    color: #17221C;
    font-size: 18px;
    font-weight: 700;
}
QLabel#sectionTitle {
    color: #17221C;
    font-size: 13px;
    font-weight: 700;
}
QLabel#muted {
    color: #68756D;
}
QLabel#badge {
    background: #E6F3EC;
    color: #267A55;
    border-radius: 10px;
    padding: 5px 11px;
}
QLabel#badgeMuted {
    background: #EDF1EF;
    color: #68756D;
    border-radius: 10px;
    padding: 5px 11px;
}
QFrame#card {
    background: #FFFFFF;
    border: 1px solid #DDE5E0;
    border-radius: 14px;
}
QFrame#summary {
    background: #FFFFFF;
    border: 1px solid #DDE5E0;
    border-radius: 12px;
}
QPushButton {
    min-height: 36px;
    border-radius: 9px;
    padding: 0 16px;
    font-weight: 600;
}
QPushButton[variant="primary"] {
    min-height: 42px;
    background: #267A55;
    color: #FFFFFF;
    border: 1px solid #267A55;
}
QPushButton[variant="primary"]:hover {
    background: #1F6848;
}
QPushButton[variant="secondary"] {
    background: #FFFFFF;
    color: #267A55;
    border: 1px solid #DDE5E0;
}
QPushButton[variant="secondary"]:hover,
QPushButton[variant="link"]:hover {
    background: #E6F3EC;
}
QPushButton[variant="ghost"] {
    background: transparent;
    color: #68756D;
    border: 0;
}
QPushButton[variant="link"] {
    background: transparent;
    color: #267A55;
    border: 0;
}
QPushButton[variant="nav"] {
    min-height: 42px;
    background: transparent;
    color: #B5C8BE;
    border: 0;
    text-align: left;
    padding-left: 16px;
}
QPushButton[variant="nav"]:hover,
QPushButton[variant="nav"][active="true"] {
    background: #254437;
    color: #FFFFFF;
}
QPushButton[variant="segment"] {
    background: #F8FAF9;
    color: #68756D;
    border: 1px solid #DDE5E0;
}
QPushButton[variant="segment"]:checked {
    background: #E6F3EC;
    color: #267A55;
    border-color: #267A55;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QListWidget, QPlainTextEdit {
    min-height: 36px;
    background: #F8FAF8;
    color: #17221C;
    border: 1px solid #DDE5E0;
    border-radius: 8px;
    padding: 0 10px;
    selection-background-color: #267A55;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QListWidget:focus, QPlainTextEdit:focus {
    border: 1px solid #267A55;
}
QCheckBox, QRadioButton {
    color: #17221C;
    spacing: 8px;
}
QSlider::groove:horizontal {
    height: 8px;
    background: #DDE5E0;
    border-radius: 4px;
}
QSlider::sub-page:horizontal {
    background: #267A55;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    width: 20px;
    margin: -6px 0;
    background: #267A55;
    border: 2px solid #FFFFFF;
    border-radius: 10px;
}
QSlider::handle:horizontal:hover {
    background: #1F6848;
}
QSlider::sub-page:horizontal:disabled,
QSlider::handle:horizontal:disabled {
    background: #AEBBB4;
}
QTableWidget {
    background: #FFFFFF;
    alternate-background-color: #F8FAF9;
    gridline-color: #DDE5E0;
    border: 0;
    selection-background-color: #E6F3EC;
}
QTableWidget#reviewTable {
    border: 1px solid #DDE5E0;
    border-radius: 8px;
    gridline-color: #E7EDE9;
}
QHeaderView::section {
    background: #F4F8F5;
    color: #68756D;
    border: 0;
    border-right: 1px solid #DDE5E0;
    border-bottom: 1px solid #DDE5E0;
    padding: 8px;
    font-weight: 600;
}
QScrollBar:horizontal {
    height: 10px;
    background: #F3F6F4;
    margin: 1px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    min-width: 32px;
    background: #CAD8D0;
    border-radius: 5px;
}
QScrollBar:vertical {
    width: 10px;
    background: #F3F6F4;
    margin: 1px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    min-height: 32px;
    background: #CAD8D0;
    border-radius: 5px;
}
QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}
QFrame#popoverCard,
QFrame#columnPopover,
QFrame#matchPopover {
    background: #FFFFFF;
    border: 1px solid #DDE5E0;
    border-radius: 12px;
}
QFrame#columnPopover QScrollArea,
QFrame#columnPopover QScrollArea > QWidget > QWidget {
    background: transparent;
    border: 0;
}
QSplitter::handle {
    background: #F3F6F4;
}
QToolTip {
    background: #17221C;
    color: #FFFFFF;
    border: 0;
    padding: 7px;
}
"""
