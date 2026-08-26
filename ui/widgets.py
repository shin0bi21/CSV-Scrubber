from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .styles import BUTTON_STYLES, COLORS, FONTS


# ============================================================================
# Shared layout widgets
# Purpose: provide reusable frames, cards, buttons, labels, and scrolling.
# Ownership: layout and widget construction only; no navigation or app state.
# ============================================================================
def clear_body(app):
    for child in app.body.winfo_children():
        child.destroy()


def page(app, title: str, subtitle: str) -> tk.Frame:
    """Clear the body and create a standard titled view container."""
    clear_body(app)
    outer = tk.Frame(app.body, bg=COLORS["bg"])
    outer.pack(fill="both", expand=True, padx=36, pady=28)
    tk.Label(outer, text=title, bg=COLORS["bg"], fg=COLORS["ink"], font=FONTS["title"]).pack(anchor="w")
    tk.Label(outer, text=subtitle, bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["body_large"]).pack(anchor="w", pady=(5, 22))
    return outer


def card(parent) -> tk.Frame:
    """Create a bordered content card with the standard paper background."""
    frame = tk.Frame(parent, bg=COLORS["paper"], highlightbackground=COLORS["line"], highlightthickness=1)
    frame.pack(fill="x", pady=(0, 16))
    frame.grid_columnconfigure(1, weight=1)
    return frame


def section_label(parent, text: str, bg: str, fg: str, **grid_kwargs):
    label = tk.Label(parent, text=text, bg=bg, fg=fg, font=FONTS["section"], padx=9, pady=4)
    label.grid(**grid_kwargs)
    return label


def button(parent, text: str, command, style: str = "secondary", **kwargs):
    """Create a themed Tk button with optional layout-specific overrides."""
    options = dict(BUTTON_STYLES[style])
    options.update(kwargs)
    return tk.Button(parent, text=text, command=command, cursor="hand2", **options)


def scrollable_frame(parent) -> tk.Frame:
    """Create a scrollable frame and return its interior content frame."""
    canvas = tk.Canvas(parent, bg=COLORS["paper"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    table = tk.Frame(canvas, bg=COLORS["paper"])
    table.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    table_window = canvas.create_window((0, 0), window=table, anchor="nw")
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(table_window, width=event.width))
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return table


# ============================================================================
# Input controls
# Purpose: build file, column, threshold, and progress controls for views.
# Events: callbacks are supplied by app/events; widgets do not own workflows.
# ============================================================================
def source_picker(app, frame, source, label: str, row: int):
    """Render a CSV path field and its browse action."""
    tk.Label(frame, text=label, bg=COLORS["paper"], fg=COLORS["muted"], font=FONTS["label"]).grid(row=row, column=0, sticky="w", padx=(20, 12), pady=14)
    path_var = tk.StringVar(value=source.path)
    entry = tk.Entry(frame, textvariable=path_var, state="readonly", readonlybackground=COLORS["entry_bg"], relief="solid", bd=1, font=FONTS["body"])
    entry.grid(row=row, column=1, sticky="ew", pady=14, ipady=8)
    button(frame, "Browse…", lambda: app.load_source(source, path_var), "secondary", padx=12, pady=7).grid(row=row, column=2, padx=16, pady=14)


def column_picker(source, frame, label: str, row: int, attribute: str = "match_columns"):
    """Render a selected-column summary and its chooser action."""
    tk.Label(frame, text=label, bg=COLORS["paper"], fg=COLORS["muted"], font=FONTS["label"]).grid(row=row, column=0, sticky="w", padx=(20, 12), pady=14)
    picker = tk.Frame(frame, bg=COLORS["paper"])
    picker.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(0, 16), pady=10)
    picker.grid_columnconfigure(0, weight=1)
    source._column_pickers[attribute] = picker
    refresh_column_picker(source, attribute)


def refresh_column_picker(source, attribute: str = "match_columns"):
    """Refresh a selected-column summary after source state changes."""
    picker = source._column_pickers.get(attribute)
    if picker is None:
        return
    for child in picker.winfo_children():
        child.destroy()

    if not source.headers:
        tk.Label(picker, text="Load a CSV to choose columns.", bg=COLORS["paper"], fg=COLORS["muted"], font=FONTS["body_small"]).pack(anchor="w")
        return

    selected_columns = getattr(source, attribute)
    selected = ", ".join(selected_columns) if selected_columns else f"No {attribute.replace('_', ' ')} selected"
    tk.Label(picker, text=selected, bg=COLORS["paper"], fg=COLORS["ink"] if selected_columns else COLORS["muted"], font=FONTS["body"], anchor="w", justify="left", wraplength=430).grid(row=0, column=0, sticky="ew", padx=(0, 12))
    button(picker, "Choose columns…", lambda: choose_columns(source, attribute), "secondary", padx=12, pady=7).grid(row=0, column=1, sticky="e")


def choose_columns(source, attribute: str = "match_columns"):
    """Open the reusable match or reference column selection dialog."""
    picker = source._column_pickers[attribute]
    parent = picker.winfo_toplevel()
    is_match_picker = attribute == "match_columns"
    dialog = tk.Toplevel(parent)
    dialog.title("Choose match columns" if is_match_picker else "Choose reference columns")
    dialog.geometry("520x560")
    dialog.minsize(420, 360)
    dialog.configure(bg=COLORS["bg"])
    dialog.transient(parent)
    dialog.grab_set()

    title = "Choose columns used for matching" if is_match_picker else "Choose columns shown as review reference"
    subtitle = "Selected values are combined per row before fuzzy matching." if is_match_picker else "These columns provide supporting context but do not affect the match score."
    tk.Label(dialog, text=title, bg=COLORS["bg"], fg=COLORS["ink"], font=FONTS["card_title"]).pack(anchor="w", padx=24, pady=(22, 4))
    tk.Label(dialog, text=subtitle, bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["body"]).pack(anchor="w", padx=24, pady=(0, 16))

    body = tk.Frame(dialog, bg=COLORS["paper"], highlightbackground=COLORS["line"], highlightthickness=1)
    body.pack(fill="both", expand=True, padx=24)
    columns_frame = scrollable_frame(body)
    variables = {}
    selected_columns = getattr(source, attribute)
    for index, column in enumerate(source.headers):
        variable = tk.BooleanVar(value=column in selected_columns)
        variables[column] = variable
        tk.Checkbutton(columns_frame, text=column, variable=variable, bg=COLORS["paper"], activebackground=COLORS["paper"], selectcolor=COLORS["paper"], font=FONTS["body"], anchor="w").grid(row=index, column=0, sticky="w", padx=16, pady=5)

    actions = tk.Frame(dialog, bg=COLORS["bg"])
    actions.pack(fill="x", padx=24, pady=18)

    def apply_selection():
        setattr(source, attribute, [column for column in source.headers if variables[column].get()])
        refresh_column_picker(source, attribute)
        dialog.destroy()

    button(actions, "Cancel", dialog.destroy, "ghost", padx=14, pady=8).pack(side="right", padx=(9, 0))
    button(actions, "Apply columns", apply_selection, "primary_small", padx=14, pady=8).pack(side="right")


def scale_row(frame, label: str, var: tk.IntVar, row: int):
    """Render a labeled threshold slider and its current value."""
    tk.Label(frame, text=label, bg=COLORS["paper"], fg=COLORS["muted"], font=FONTS["label"]).grid(row=row, column=0, sticky="w", padx=20, pady=14)
    scale = tk.Scale(frame, from_=60, to=100, orient="horizontal", variable=var, showvalue=False, bg=COLORS["paper"], fg=COLORS["green"], highlightthickness=0, troughcolor=COLORS["line"])
    scale.grid(row=row, column=1, sticky="ew", pady=14)
    tk.Label(frame, textvariable=var, bg=COLORS["green_light"], fg=COLORS["green"], font=FONTS["label"], width=5, pady=5).grid(row=row, column=2, padx=20)


def progress_overlay(app):
    """Create and start the indeterminate scan-progress overlay."""
    overlay = tk.Frame(app.body, bg=COLORS["bg"])
    overlay.place(relx=.5, rely=.45, anchor="center")
    tk.Label(overlay, text="Finding likely matches…", bg=COLORS["bg"], fg=COLORS["ink"], font=FONTS["progress"]).pack(pady=10)
    bar = ttk.Progressbar(overlay, mode="indeterminate", length=300)
    bar.pack()
    bar.start(10)
    return overlay
