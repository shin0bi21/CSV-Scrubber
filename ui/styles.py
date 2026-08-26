"""Shared visual tokens for the CustomTkinter interface."""

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
    "brand_muted": "#92AA9E",
    "nav_label": "#789286",
    "nav_text": "#B5C8BE",
    "privacy_dot": "#5ED38B",
    "privacy_muted": "#819A8E",
    "entry_bg": "#F8FAF8",
    "progress_trough": "#DFE8E2",
    "panel_header": "#F4F8F5",
    "panel_subtle": "#F8FAF9",
    "panel_alt": "#EDF1EF",
    "truth_header": "#E7F3EC",
    "warning": "#FFF4DF",
    "field_active": "#F0F7F3",
}

FONTS = {
    "title": ("Segoe UI", 28, "bold"),
    "brand_icon": ("Segoe UI", 18, "bold"),
    "brand": ("Segoe UI", 15, "bold"),
    "section": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 13),
    "body_small": ("Segoe UI", 12),
    "body_tiny": ("Segoe UI", 11),
    "body_large": ("Segoe UI", 15),
    "progress": ("Segoe UI", 17, "bold"),
    "success_icon": ("Segoe UI", 30, "bold"),
    "card_title": ("Segoe UI", 18, "bold"),
    "label": ("Segoe UI", 13, "bold"),
    "button": ("Segoe UI", 14, "bold"),
    "button_small": ("Segoe UI", 13, "bold"),
}

BUTTON_STYLES = {
    "primary": {
        "fg_color": COLORS["green"], "hover_color": COLORS["green_hover"],
        "text_color": COLORS["text_on_dark"], "font": FONTS["button"],
        "height": 44, "corner_radius": 10,
    },
    "primary_small": {
        "fg_color": COLORS["green"], "hover_color": COLORS["green_hover"],
        "text_color": COLORS["text_on_dark"], "font": FONTS["button_small"],
        "height": 38, "corner_radius": 9,
    },
    "secondary": {
        "fg_color": COLORS["paper"], "hover_color": COLORS["panel_subtle"],
        "text_color": COLORS["green"], "border_color": COLORS["line"],
        "border_width": 1, "font": FONTS["button_small"], "height": 38,
        "corner_radius": 9,
    },
    "ghost": {
        "fg_color": "transparent", "hover_color": COLORS["panel_alt"],
        "text_color": COLORS["muted"], "font": FONTS["button_small"],
        "height": 38, "corner_radius": 9,
    },
    "ghost_green": {
        "fg_color": "transparent", "hover_color": COLORS["green_light"],
        "text_color": COLORS["green"], "font": FONTS["button_small"],
        "height": 38, "corner_radius": 9,
    },
    "link": {
        "fg_color": "transparent", "hover_color": COLORS["green_light"],
        "text_color": COLORS["green"], "font": FONTS["button_small"],
        "height": 34, "corner_radius": 8,
    },
    "link_muted": {
        "fg_color": "transparent", "hover_color": COLORS["panel_alt"],
        "text_color": COLORS["muted"], "font": FONTS["button_small"],
        "height": 34, "corner_radius": 8,
    },
    "nav": {
        "fg_color": "transparent", "hover_color": COLORS["nav_active"],
        "text_color": COLORS["nav_text"], "font": FONTS["button"],
        "height": 44, "corner_radius": 9,
    },
}

NAV_BUTTON_STATES = {
    "active": {
        "fg_color": COLORS["nav_active"], "text_color": COLORS["text_on_dark"],
        "hover_color": COLORS["nav_active"],
    },
    "inactive": {
        "fg_color": "transparent", "text_color": COLORS["nav_text"],
        "hover_color": COLORS["nav_active"],
    },
}
