# CSV Scrubber

A local Windows desktop application for reviewing fuzzy duplicate matches and creating clean, auditable CSV exports.

## Features

- Single-file mode: choose one CSV, matching columns, and reference columns.
- Multi-file mode: choose a source-of-truth CSV, a dependent CSV, and matching/reference columns in each.
- Modern CustomTkinter interface with scalable controls and a focused Setup, Analyze, Review, and Settings workflow.
- Match and reference column selections start empty; at least one match column is required to scan, while reference columns are optional.
- Soft token-level fuzzy matching using RapidFuzz, with automatic frequency weighting and no hard-coded company, region, or abbreviation rules.
- Analyze frequent tokens from the selected matching columns on the Analyze page and manually adjust their influence; reference columns never affect scoring.
- Generic normalization for Unicode, case, punctuation, and whitespace.
- Review groups with confidence scores.
- Edit values during review, then keep selected rows, merge selected rows into one record, or explicitly mark the group as not duplicated.
- Review editing is limited to matching fields on main rows; dependent rows and reference fields are read-only.
- Source-of-truth values are preferred by default in multi-file mode; missing truth values fall back to the dependent source.
- Export a cleaned UTF-8 CSV and a companion audit CSV. Input files are never overwritten.
- All processing is local; the app does not call an LLM or upload CSV data.

## Project Structure

- `app.py` initializes the application and owns shared state.
- `engine/__init__.py` is the stable public interface used by the application.
- `csv_io.py` contains CSV reading and writing at the project root.
- `engine/stage_00_models.py` defines rules, record references, evidence, and groups.
- `engine/stage_01_normalization.py` prepares selected values without crossing column boundaries.
- `engine/stage_02_weights.py` analyzes token frequency and builds token weights.
- `engine/stage_03_candidates.py` generates exhaustive or blocked candidate pairs.
- `engine/stage_04_scoring.py` scores candidates and records match evidence.
- `engine/stage_05_grouping.py` creates connected review groups and reason labels.
- `engine/stage_06_scans.py` orchestrates single-file and cross-file scans.
- `ui/styles.py` contains colors, fonts, and button styles.
- `ui/shell.py` builds the application-level sidebar, topbar, and navigation.
- `ui/widgets.py` contains reusable controls, including the shared column picker and selection popup.
- `ui/views.py` builds the application screens and hydrates shared widgets with view-specific data and roles.
- `ui/events.py` handles user actions, maps UI roles to engine state, and rehydrates views.

## Run on Windows

1. Install Python 3.11 or newer from https://www.python.org/downloads/windows/ and select **Add Python to PATH** during installation.
2. Double-click `run_windows.bat`.

The launcher installs the required Python packages and starts the app from source.

## Build the standalone EXE

Double-click `build_windows_exe.bat`. The finished executable will be:

`dist\CSV-Scrubber\CSV-Scrubber.exe`

Python is required only to perform the build. Copy the complete `dist\CSV-Scrubber` folder to run the application on another Windows computer without installing Python.

## Workflow

The application follows the same high-level flow for every scan type:

1. **Setup** — choose Single file or Multi-file, load CSVs, and select match/reference columns.
2. **Analyze** — inspect common tokens and adjust their influence before scanning.
3. **Review** — resolve the groups found by the scan.
4. **Settings** — configure matching behavior before scanning.

Single-file and multi-file modes share the same column-selection UI. The picker receives the available columns, current selections, and a role (`match` or `reference`); the event layer maps that role to the appropriate engine field.

## Settings

The Settings screen deliberately does not select columns or review common tokens. It controls only:

- algorithm selection and description,
- similarity review threshold,
- minimum common-token row count,
- lowercase conversion,
- punctuation removal.

Matching is column-agnostic. It applies only generic text normalization to the selected match columns and does not assume that a column contains company names, addresses, or any other specific kind of data. Selected match columns are compared by position, so tokens from different columns cannot match each other. Reference columns never contribute to the score.

The matching algorithm compares normalized values per selected column through a token-level fuzzy-similarity flow, then combines column scores using optional column weights. Small scans can use exhaustive comparison; larger scans automatically use generic token and n-gram blocking before fuzzy scoring. Tokens that occur often contribute less, while rare tokens contribute more; a configured weight of zero excludes that token from scoring. Manual weights adjust a token's relative influence. Each accepted candidate retains token matches, unmatched tokens, coverage, and a reason for review; exact normalized values are distinguished from high-scoring non-identical values.
