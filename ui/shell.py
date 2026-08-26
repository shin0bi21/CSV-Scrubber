from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .styles import COLORS, FONTS, NAV_BUTTON_STATES
from .widgets import button


# ============================================================================
# Shell setup
# Purpose: configure shared ttk styles and build the application frame.
# Ownership: sidebar, topbar, navigation, and the body host for views.
# ============================================================================
def setup_styles(app):
    """Configure ttk styles used by the application shell and widgets."""
    style = ttk.Style(app)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TCombobox", padding=7, fieldbackground=COLORS["paper"], background=COLORS["paper"])
    style.configure("Horizontal.TProgressbar", troughcolor=COLORS["progress_trough"], background=COLORS["green"])


def build(app):
    """Build the persistent shell around the replaceable view body."""
    _build_sidebar(app)
    _build_topbar(app)
    app.body = tk.Frame(app.right, bg=COLORS["bg"])
    app.body.pack(fill="both", expand=True)


# ============================================================================
# Sidebar
# Purpose: build branding, workspace navigation, and privacy messaging.
# Events: navigation buttons call app.show_workspace(), app.show_analyze(), app.show_review(), or app.show_rules().
# ============================================================================
def _build_sidebar(app):
    app.sidebar = tk.Frame(app, bg=COLORS["nav"], width=220)
    app.sidebar.pack(side="left", fill="y")
    app.sidebar.pack_propagate(False)
    _build_brand(app.sidebar)
    _build_nav_buttons(app)
    _build_privacy_footer(app.sidebar)


def _build_brand(sidebar):
    brand = tk.Frame(sidebar, bg=COLORS["nav"])
    brand.pack(fill="x", padx=18, pady=(23, 30))
    tk.Label(brand, text="✦", bg=COLORS["brand_bg"], fg=COLORS["brand_fg"], font=FONTS["brand_icon"], width=2, pady=4).pack(side="left")
    brand_text = tk.Frame(brand, bg=COLORS["nav"])
    brand_text.pack(side="left", padx=10)
    tk.Label(brand_text, text="CSV Scrubber", bg=COLORS["nav"], fg=COLORS["text_on_dark"], font=FONTS["brand"]).pack(anchor="w")
    tk.Label(brand_text, text="Local workspace", bg=COLORS["nav"], fg=COLORS["brand_muted"], font=FONTS["body_small"]).pack(anchor="w")


def _build_nav_buttons(app):
    sidebar = app.sidebar
    tk.Label(sidebar, text="WORKSPACE", bg=COLORS["nav"], fg=COLORS["nav_label"], font=FONTS["section"]).pack(anchor="w", padx=22, pady=(0, 6))
    app.nav_buttons = {}
    workspace_button = button(sidebar, "Setup", app.show_workspace, "nav", anchor="w", padx=16, pady=11)
    workspace_button.pack(fill="x", padx=10, pady=2)
    app.nav_buttons["workspace"] = workspace_button

    analyze_button = button(sidebar, "Analyze", app.show_analyze, "nav", anchor="w", padx=16, pady=11)
    analyze_button.pack(fill="x", padx=10, pady=2)
    app.nav_buttons["analyze"] = analyze_button

    review_button = button(sidebar, "Review", app.show_review, "nav", anchor="w", padx=16, pady=11)
    review_button.pack(fill="x", padx=10, pady=2)
    app.nav_buttons["review"] = review_button

    tk.Label(sidebar, text="CONFIGURE", bg=COLORS["nav"], fg=COLORS["nav_label"], font=FONTS["section"]).pack(anchor="w", padx=22, pady=(22, 6))
    rules_button = button(sidebar, "Ruleset", app.show_rules, "nav", anchor="w", padx=16, pady=11)
    rules_button.pack(fill="x", padx=10, pady=2)
    app.nav_buttons["rules"] = rules_button


def _build_privacy_footer(sidebar):
    privacy = tk.Frame(sidebar, bg=COLORS["nav"])
    privacy.pack(side="bottom", fill="x", padx=20, pady=22)
    tk.Label(privacy, text="●", fg=COLORS["privacy_dot"], bg=COLORS["nav"], font=FONTS["body"]).pack(side="left", anchor="n")
    text = tk.Frame(privacy, bg=COLORS["nav"])
    text.pack(side="left", padx=8)
    tk.Label(text, text="Local processing", fg=COLORS["text_on_dark"], bg=COLORS["nav"], font=FONTS["label"]).pack(anchor="w")
    tk.Label(text, text="CSV data stays on this device", fg=COLORS["privacy_muted"], bg=COLORS["nav"], font=FONTS["body_tiny"]).pack(anchor="w")


# ============================================================================
# Top bar and navigation state
# Purpose: provide breadcrumbs, session reset, and active-nav styling.
# ============================================================================
def _build_topbar(app):
    app.right = tk.Frame(app, bg=COLORS["bg"])
    app.right.pack(side="left", fill="both", expand=True)
    app.topbar = tk.Frame(app.right, bg=COLORS["paper"], height=60, highlightbackground=COLORS["line"], highlightthickness=1)
    app.topbar.pack(fill="x")
    app.topbar.pack_propagate(False)
    app.crumb = tk.Label(app.topbar, text="Setup  ›  Single file", bg=COLORS["paper"], fg=COLORS["muted"], font=FONTS["label"])
    app.crumb.pack(side="left", padx=28)
    new_session = button(app.topbar, "New session", app.show_workspace, "link_muted")
    new_session.pack(side="right", padx=25)


def set_nav(app, active: str):
    """Apply the active style to the selected shell navigation button."""
    for key, nav_button in app.nav_buttons.items():
        state = NAV_BUTTON_STATES["active" if key == active else "inactive"]
        nav_button.configure(**state)
