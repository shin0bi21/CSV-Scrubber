from __future__ import annotations

import customtkinter as ctk

from .styles import COLORS, FONTS, NAV_BUTTON_STATES
from .widgets import button


# ============================================================================
# Shell setup
# Purpose: initialize CustomTkinter and build the application frame.
# Ownership: sidebar, topbar, navigation, and the body host for views.
# ============================================================================
def setup_styles(_app):
    """Use a consistent modern light appearance across the application."""
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")


def build(app):
    """Build the persistent shell around the replaceable view body."""
    _build_sidebar(app)
    _build_topbar(app)
    app.body = ctk.CTkFrame(app.right, fg_color=COLORS["bg"], corner_radius=0)
    app.body.pack(fill="both", expand=True)


# ============================================================================
# Sidebar
# Purpose: build branding, workspace navigation, and privacy messaging.
# Events: navigation buttons call the matching app view event.
# ============================================================================
def _build_sidebar(app):
    app.sidebar = ctk.CTkFrame(app, fg_color=COLORS["nav"], width=236, corner_radius=0)
    app.sidebar.pack(side="left", fill="y")
    app.sidebar.pack_propagate(False)
    _build_brand(app.sidebar)
    _build_nav_buttons(app)
    _build_privacy_footer(app.sidebar)


def _build_brand(sidebar):
    brand = ctk.CTkFrame(sidebar, fg_color="transparent", corner_radius=0)
    brand.pack(fill="x", padx=20, pady=(26, 34))
    ctk.CTkLabel(
        brand,
        text="✦",
        fg_color=COLORS["brand_bg"],
        text_color=COLORS["brand_fg"],
        font=FONTS["brand_icon"],
        width=42,
        height=42,
        corner_radius=12,
    ).pack(side="left")
    brand_text = ctk.CTkFrame(brand, fg_color="transparent", corner_radius=0)
    brand_text.pack(side="left", padx=12)
    ctk.CTkLabel(brand_text, text="CSV Scrubber", text_color=COLORS["text_on_dark"], font=FONTS["brand"], anchor="w").pack(fill="x", anchor="w")
    ctk.CTkLabel(brand_text, text="Local workspace", text_color=COLORS["brand_muted"], font=FONTS["body_tiny"], anchor="w").pack(fill="x", anchor="w", pady=(2, 0))


def _build_nav_buttons(app):
    sidebar = app.sidebar
    ctk.CTkLabel(sidebar, text="WORKFLOW", text_color=COLORS["nav_label"], font=FONTS["section"], anchor="w").pack(fill="x", padx=24, pady=(0, 8))
    app.nav_buttons = {}

    for key, label, command in (
        ("workspace", "Setup", app.show_workspace),
        ("analyze", "Analyze", app.show_analyze),
        ("review", "Review", app.show_review),
    ):
        nav_button = button(sidebar, label, command, "nav", anchor="w")
        nav_button.pack(fill="x", padx=12, pady=3)
        app.nav_buttons[key] = nav_button

    ctk.CTkLabel(sidebar, text="PREFERENCES", text_color=COLORS["nav_label"], font=FONTS["section"], anchor="w").pack(fill="x", padx=24, pady=(28, 8))
    settings_button = button(sidebar, "Settings", app.show_settings, "nav", anchor="w")
    settings_button.pack(fill="x", padx=12, pady=3)
    app.nav_buttons["settings"] = settings_button


def _build_privacy_footer(sidebar):
    privacy = ctk.CTkFrame(sidebar, fg_color=COLORS["nav_active"], corner_radius=12)
    privacy.pack(side="bottom", fill="x", padx=16, pady=20)
    ctk.CTkLabel(privacy, text="●", text_color=COLORS["privacy_dot"], font=FONTS["body_small"], width=16).pack(side="left", anchor="n", padx=(14, 4), pady=14)
    text = ctk.CTkFrame(privacy, fg_color="transparent", corner_radius=0)
    text.pack(side="left", fill="x", expand=True, padx=(4, 12), pady=12)
    ctk.CTkLabel(text, text="Local processing", text_color=COLORS["text_on_dark"], font=FONTS["label"], anchor="w").pack(fill="x")
    ctk.CTkLabel(text, text="CSV data stays on this device", text_color=COLORS["privacy_muted"], font=FONTS["body_tiny"], anchor="w").pack(fill="x", pady=(2, 0))


# ============================================================================
# Top bar and navigation state
# Purpose: provide breadcrumbs, session reset, and active-nav styling.
# ============================================================================
def _build_topbar(app):
    app.right = ctk.CTkFrame(app, fg_color=COLORS["bg"], corner_radius=0)
    app.right.pack(side="left", fill="both", expand=True)
    app.topbar = ctk.CTkFrame(
        app.right,
        fg_color=COLORS["paper"],
        height=68,
        corner_radius=0,
        border_color=COLORS["line"],
        border_width=1,
    )
    app.topbar.pack(fill="x")
    app.topbar.pack_propagate(False)
    app.crumb = ctk.CTkLabel(app.topbar, text="Setup  ›  Single file", text_color=COLORS["muted"], font=FONTS["label"], anchor="w")
    app.crumb.pack(side="left", padx=32)
    button(app.topbar, "New session", app.show_workspace, "link_muted").pack(side="right", padx=26, pady=14)


def set_nav(app, active: str):
    """Apply the active style to the selected shell navigation button."""
    for key, nav_button in app.nav_buttons.items():
        nav_button.configure(**NAV_BUTTON_STATES["active" if key == active else "inactive"])
