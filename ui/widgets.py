from __future__ import annotations

from collections.abc import Callable
import tkinter as tk

import customtkinter as ctk

from .styles import BUTTON_STYLES, COLORS, FONTS


# ============================================================================
# Shared layout widgets
# Purpose: provide reusable modern frames, cards, buttons, and scrolling.
# Ownership: layout and widget construction only; no navigation or app state.
# ============================================================================
def clear_body(app):
    for child in app.body.winfo_children():
        child.destroy()


def page(app, title: str, subtitle: str) -> ctk.CTkFrame:
    """Clear the body and create a standard titled view container."""
    clear_body(app)
    outer = ctk.CTkFrame(app.body, fg_color="transparent", corner_radius=0)
    outer.pack(fill="both", expand=True, padx=40, pady=32)
    ctk.CTkLabel(outer, text=title, text_color=COLORS["ink"], font=FONTS["title"], anchor="w").pack(fill="x", anchor="w")
    ctk.CTkLabel(outer, text=subtitle, text_color=COLORS["muted"], font=FONTS["body_large"], anchor="w").pack(fill="x", anchor="w", pady=(6, 24))
    return outer


def card(parent) -> ctk.CTkFrame:
    """Create a rounded, bordered content card."""
    frame = ctk.CTkFrame(
        parent,
        fg_color=COLORS["paper"],
        border_color=COLORS["line"],
        border_width=1,
        corner_radius=14,
    )
    frame.pack(fill="x", pady=(0, 16))
    frame.grid_columnconfigure(1, weight=1)
    return frame


def section_label(parent, text: str, bg: str, fg: str, **grid_kwargs):
    label = ctk.CTkLabel(
        parent,
        text=text,
        fg_color=bg,
        text_color=fg,
        font=FONTS["section"],
        height=26,
        corner_radius=7,
    )
    label.grid(**grid_kwargs)
    return label


def button(parent, text: str, command, style: str = "secondary", **kwargs):
    """Create a consistently sized CustomTkinter button."""
    options = dict(BUTTON_STYLES[style])
    horizontal_padding = kwargs.pop("padx", 0)
    vertical_padding = kwargs.pop("pady", 0)
    options.update(kwargs)
    options.setdefault("width", 196 if style == "nav" else max(92, len(text) * 8 + 28 + horizontal_padding))
    if vertical_padding:
        options["height"] = max(options.get("height", 34), vertical_padding * 2 + 20)
    return ctk.CTkButton(parent, text=text, command=command, **options)


def scrollable_frame(parent) -> ctk.CTkScrollableFrame:
    """Create a modern scrollable content frame."""
    frame = ctk.CTkScrollableFrame(
        parent,
        fg_color=COLORS["paper"],
        corner_radius=0,
        scrollbar_fg_color=COLORS["paper"],
        scrollbar_button_color=COLORS["line"],
        scrollbar_button_hover_color=COLORS["muted"],
    )
    frame.pack(fill="both", expand=True, padx=2, pady=2)
    return frame


# ============================================================================
# Input controls
# Purpose: build file, column, threshold, and progress controls for views.
# Events: callbacks are supplied by app/events; widgets do not own workflows.
# ============================================================================
def source_picker(app, frame, source, label: str, row: int):
    """Render a CSV path field and its browse action."""
    ctk.CTkLabel(frame, text=label, text_color=COLORS["muted"], font=FONTS["label"], anchor="w").grid(row=row, column=0, sticky="w", padx=(22, 14), pady=15)
    path_var = tk.StringVar(value=source.path)
    entry = ctk.CTkEntry(
        frame,
        textvariable=path_var,
        state="disabled",
        fg_color=COLORS["entry_bg"],
        border_color=COLORS["line"],
        text_color=COLORS["ink"],
        font=FONTS["body"],
        height=40,
        corner_radius=9,
    )
    entry.grid(row=row, column=1, sticky="ew", pady=15)
    button(frame, "Browse…", lambda: app.load_source(source, path_var), "secondary").grid(row=row, column=2, padx=18, pady=15)


def column_picker(
    frame,
    label: str,
    row: int,
    columns: list[str],
    selected_columns: list[str],
    popup_title: str,
    popup_subtitle: str,
    on_apply: Callable[[list[str]], None],
):
    """Render a reusable selected-column picker populated by the calling view."""
    ctk.CTkLabel(frame, text=label, text_color=COLORS["muted"], font=FONTS["label"], anchor="w").grid(row=row, column=0, sticky="w", padx=(22, 14), pady=15)
    picker = ctk.CTkFrame(frame, fg_color="transparent", corner_radius=0)
    picker.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 18), pady=10)
    picker.grid_columnconfigure(0, weight=1)

    if not columns:
        ctk.CTkLabel(picker, text="Load a CSV to choose columns.", text_color=COLORS["muted"], font=FONTS["body_small"], anchor="w").grid(row=0, column=0, sticky="ew")
        return

    selected = ", ".join(selected_columns) if selected_columns else f"No {label.lower()} selected"
    ctk.CTkLabel(
        picker,
        text=selected,
        text_color=COLORS["ink"] if selected_columns else COLORS["muted"],
        font=FONTS["body"],
        anchor="w",
        justify="left",
        wraplength=430,
    ).grid(row=0, column=0, sticky="ew", padx=(0, 12))
    button(
        picker,
        "Choose columns…",
        lambda: column_selection_popup(
            picker.winfo_toplevel(),
            title=popup_title,
            subtitle=popup_subtitle,
            columns=columns,
            selected_columns=selected_columns,
            on_apply=on_apply,
        ),
        "secondary",
    ).grid(row=0, column=1, sticky="e")


def column_selection_popup(parent, *, title: str, subtitle: str, columns: list[str], selected_columns: list[str], on_apply: Callable[[list[str]], None]):
    """Render a generic column-selection popup from supplied view data."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("560x620")
    dialog.minsize(460, 420)
    dialog.configure(fg_color=COLORS["bg"])
    dialog.transient(parent)
    dialog.grab_set()
    dialog.after(50, dialog.focus_force)

    ctk.CTkLabel(dialog, text=title, text_color=COLORS["ink"], font=FONTS["card_title"], anchor="w").pack(fill="x", padx=28, pady=(26, 4))
    ctk.CTkLabel(dialog, text=subtitle, text_color=COLORS["muted"], font=FONTS["body"], anchor="w", justify="left", wraplength=500).pack(fill="x", padx=28, pady=(0, 18))

    body = ctk.CTkFrame(dialog, fg_color=COLORS["paper"], border_color=COLORS["line"], border_width=1, corner_radius=14)
    body.pack(fill="both", expand=True, padx=28)
    columns_frame = scrollable_frame(body)
    columns_frame.grid_columnconfigure(0, weight=1)
    variables = {}
    for index, column in enumerate(columns):
        variable = tk.BooleanVar(value=column in selected_columns)
        variables[column] = variable
        ctk.CTkCheckBox(
            columns_frame,
            text=column,
            variable=variable,
            text_color=COLORS["ink"],
            fg_color=COLORS["green"],
            hover_color=COLORS["green_hover"],
            border_color=COLORS["line"],
            font=FONTS["body"],
            corner_radius=6,
        ).grid(row=index, column=0, sticky="w", padx=18, pady=8)

    actions = ctk.CTkFrame(dialog, fg_color="transparent", corner_radius=0)
    actions.pack(fill="x", padx=28, pady=20)

    def apply_columns():
        on_apply([column for column in columns if variables[column].get()])
        dialog.destroy()

    button(actions, "Cancel", dialog.destroy, "ghost").pack(side="right", padx=(9, 0))
    apply_columns_button(actions, apply_columns).pack(side="right")


def apply_columns_button(parent, command):
    """Render the standard column-selection apply button."""
    return button(parent, "Apply columns", command, "primary_small")


def scale_row(frame, label: str, var: tk.IntVar, row: int, minimum: int = 60, maximum: int = 100):
    """Render a labeled threshold slider and its current value."""
    ctk.CTkLabel(frame, text=label, text_color=COLORS["muted"], font=FONTS["label"], anchor="w").grid(row=row, column=0, sticky="w", padx=22, pady=16)
    scale = ctk.CTkSlider(
        frame,
        from_=minimum,
        to=maximum,
        number_of_steps=maximum - minimum,
        variable=var,
        fg_color=COLORS["progress_trough"],
        progress_color=COLORS["green"],
        button_color=COLORS["green"],
        button_hover_color=COLORS["green_hover"],
        height=18,
    )
    scale.grid(row=row, column=1, sticky="ew", pady=16)
    ctk.CTkLabel(
        frame,
        textvariable=var,
        fg_color=COLORS["green_light"],
        text_color=COLORS["green"],
        font=FONTS["label"],
        width=58,
        height=32,
        corner_radius=8,
    ).grid(row=row, column=2, padx=22)


def progress_overlay(app):
    """Create and start the indeterminate scan-progress overlay."""
    overlay = ctk.CTkFrame(
        app.body,
        fg_color=COLORS["paper"],
        border_color=COLORS["line"],
        border_width=1,
        corner_radius=16,
    )
    overlay.place(relx=.5, rely=.45, anchor="center")
    ctk.CTkLabel(overlay, text="Finding likely matches…", text_color=COLORS["ink"], font=FONTS["progress"]).pack(padx=44, pady=(28, 16))
    bar = ctk.CTkProgressBar(
        overlay,
        mode="indeterminate",
        width=320,
        height=8,
        fg_color=COLORS["progress_trough"],
        progress_color=COLORS["green"],
        corner_radius=6,
    )
    bar.pack(padx=44, pady=(0, 30))
    bar.start()
    return overlay
