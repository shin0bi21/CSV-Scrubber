# CSV Scrubber

A local Windows desktop application for reviewing fuzzy duplicate matches and creating clean, auditable CSV exports.

## Features

- Single-file mode: choose one CSV, matching columns, and reference columns.
- Multi-file mode: choose a source-of-truth CSV, a dependent CSV, and matching/reference columns in each.
- Match and reference column selections start empty; at least one match column is required to scan, while reference columns are optional.
- Soft token-level fuzzy matching using RapidFuzz, with automatic frequency weighting and no hard-coded company, region, or abbreviation rules.
- Analyze frequent tokens from the selected matching columns in a separate workspace window and manually adjust their influence; reference columns never affect scoring.
- Generic normalization for Unicode, case, punctuation, and whitespace.
- Review groups with confidence scores.
- Manually resolve every detected group by keeping selected original rows, merging selected rows into one row, or explicitly marking it as not duplicated.
- Source-of-truth values are preferred by default in multi-file mode; missing truth values fall back to the dependent source.
- Export a cleaned UTF-8 CSV and a companion audit CSV. Input files are never overwritten.
- All processing is local; the app does not call an LLM or upload CSV data.

## Project Structure

- `app.py` initializes the application and owns shared state.
- `engine.py` contains CSV and matching logic.
- `ui/styles.py` contains colors, fonts, and button styles.
- `ui/shell.py` builds the application-level sidebar, topbar, and navigation.
- `ui/widgets.py` contains reusable controls, including the shared column picker and selection popup.
- `ui/views.py` builds the application screens and hydrates shared widgets with view-specific data and roles.
- `ui/events.py` handles user actions, maps UI roles to engine state, and rehydrates views.

## Run on Windows

1. Install Python 3.11 or newer from https://www.python.org/downloads/windows/ and select **Add Python to PATH** during installation.
2. Double-click `run_windows.bat`.

The launcher ensures RapidFuzz is available and starts the app from source.

## Build the standalone EXE

Double-click `build_windows_exe.bat`. The finished executable will be:

`dist\CSV-Scrubber.exe`

Python is required only to perform the build. The resulting EXE can be copied to another Windows computer without installing Python.

## Workflow

The application follows the same high-level flow for every scan type:

1. **Setup** — choose Single file or Multi-file, load CSVs, and select match/reference columns.
2. **Review** — resolve the groups found by the scan.
3. **Ruleset** — configure matching behavior before scanning.

Single-file and multi-file modes share the same column-selection UI. The picker receives the available columns, current selections, and a role (`match` or `reference`); the event layer maps that role to the appropriate engine field.

## Ruleset

The Ruleset screen deliberately does not select columns or review common tokens. It controls only:

- algorithm selection and description,
- review threshold,
- lowercase conversion,
- punctuation removal.

Matching is column-agnostic. It applies only generic text normalization to the selected match columns and does not assume that a column contains company names, addresses, or any other specific kind of data. Reference columns never contribute to the score.

The matching algorithm pairs individual tokens using fuzzy similarity, then combines those token scores with frequency-based weights. Tokens that occur often contribute less, while rare tokens contribute more; no token is removed solely because it belongs to a presumed business category. Manual weights adjust a token's relative influence. Exact normalized values still match exactly.
