# Semantic theme tokens
COLORS = {
    "nav": "#12261d",
    "nav_active": "#203a2e",
    "green": "#246c4a",
    "green_light": "#e8f3ed",
    "bg": "#f5f7f5",
    "paper": "#ffffff",
    "line": "#dfe5e1",
    "ink": "#17201b",
    "muted": "#727b75",
    "amber": "#a46313",
    "text_on_dark": "#ffffff",
    "brand_bg": "#d7f0df",
    "brand_fg": "#174e36",
    "brand_muted": "#94aa9f",
    "nav_label": "#789286",
    "nav_text": "#afc4b9",
    "privacy_dot": "#5ed38b",
    "privacy_muted": "#819a8e",
    "primary_active": "#195b3d",
    "entry_bg": "#f8faf8",
    "progress_trough": "#e8ece9",
    "panel_header": "#f6f9f7",
    "panel_subtle": "#fafbfa",
    "panel_alt": "#eef0ef",
    "truth_header": "#eaf4ee",
    "warning": "#fff4df",
    "field_active": "#f2f8f4",
}

# Typography
FONTS = {
    "title": ("Segoe UI Semibold", 22),
    "brand_icon": ("Segoe UI", 16),
    "brand": ("Segoe UI Semibold", 12),
    "section": ("Segoe UI Semibold", 8),
    "body": ("Segoe UI", 9),
    "body_small": ("Segoe UI", 8),
    "body_tiny": ("Segoe UI", 7),
    "body_large": ("Segoe UI", 10),
    "progress": ("Segoe UI Semibold", 13),
    "success_icon": ("Segoe UI", 24),
    "card_title": ("Segoe UI Semibold", 14),
    "label": ("Segoe UI Semibold", 9),
    "button": ("Segoe UI Semibold", 10),
    "button_small": ("Segoe UI Semibold", 9),
}

# Button recipes
_FLAT = {
    "relief": "flat",
    "bd": 0,
}

BUTTON_STYLES = {
    "primary": {
        "bg": COLORS["green"],
        "fg": COLORS["text_on_dark"],
        "font": FONTS["button"],
        "activebackground": COLORS["primary_active"],
        "activeforeground": COLORS["text_on_dark"],
    },
    "primary_small": {
        "bg": COLORS["green"],
        "fg": COLORS["text_on_dark"],
        "font": FONTS["button_small"],
        "activebackground": COLORS["primary_active"],
        "activeforeground": COLORS["text_on_dark"],
    },
    "secondary": {
        "bg": COLORS["paper"],
        "fg": COLORS["green"],
        "relief": "solid",
        "bd": 1,
        "font": FONTS["button_small"],
    },
    "ghost": {
        **_FLAT,
        "bg": COLORS["bg"],
        "fg": COLORS["muted"],
        "font": FONTS["button_small"],
    },
    "ghost_green": {
        **_FLAT,
        "bg": COLORS["bg"],
        "fg": COLORS["green"],
        "font": FONTS["button_small"],
    },
    "link": {
        **_FLAT,
        "bg": COLORS["paper"],
        "fg": COLORS["green"],
        "font": FONTS["button_small"],
    },
    "link_muted": {
        **_FLAT,
        "bg": COLORS["paper"],
        "fg": COLORS["muted"],
        "font": FONTS["button_small"],
    },
    "nav": {
        **_FLAT,
        "font": FONTS["button"],
    },
}

# Navigation state recipes
NAV_BUTTON_STATES = {
    "active": {
        "bg": COLORS["nav_active"],
        "fg": COLORS["text_on_dark"],
        "activebackground": COLORS["nav_active"],
        "activeforeground": COLORS["text_on_dark"],
    },
    "inactive": {
        "bg": COLORS["nav"],
        "fg": COLORS["nav_text"],
        "activebackground": COLORS["nav_active"],
        "activeforeground": COLORS["text_on_dark"],
    },
}
