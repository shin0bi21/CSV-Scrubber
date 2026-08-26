# CSV Scrubber V1

A local Windows desktop application for reviewing fuzzy duplicate matches and creating clean, auditable CSV exports.

## V1 features

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

## Project structure

- `app.py` initializes the application and owns shared state.
- `engine.py` contains CSV and matching logic.
- `ui/styles.py` contains colors, fonts, and button styles.
- `ui/shell.py` builds the application-level sidebar, topbar, and navigation.
- `ui/widgets.py` contains reusable controls.
- `ui/views.py` builds the application screens.
- `ui/events.py` handles user actions and event callbacks.

## Run on Windows

1. Install Python 3.11 or newer from https://www.python.org/downloads/windows/ and select **Add Python to PATH** during installation.
2. Double-click `run_windows.bat`.

The launcher ensures RapidFuzz is available and starts the app from source.

## Build the standalone EXE

Double-click `build_windows_exe.bat`. The finished executable will be:

`dist\CSV-Scrubber.exe`

Python is required only to perform the build. The resulting EXE can be copied to another Windows computer without installing Python.

## Workflow

### Single-file

1. Open **Single file**.
2. Choose a CSV.
3. Open **Choose columns…** for Match columns and select at least one column. Optionally choose Reference columns for review context.
4. Optionally open **Analyze common tokens…** and set token weights in its separate window.
5. Scan and manually resolve every resulting group using the matching and reference columns.
6. Keep one or more selected rows or merge selected rows into one record; mark intentional separate records as not duplicates.
7. Export the clean file and audit log.

### Multi-file

1. Open **Multi-file**.
2. Choose the truth CSV and select its matching and reference columns.
3. Choose the dependent CSV and select its corresponding match and reference columns. The headers may differ.
4. Optionally open **Analyze common tokens…** and set token weights in its separate window.
5. Manually resolve every cross-file match using the matching and reference columns. Truth values are preselected when present.
6. Keep one or more selected rows or create one merged golden record from them; mark intentional separate records as not duplicates.
7. Export the reconciled file and audit log.

## Ruleset

The Ruleset screen deliberately does not select columns or review common tokens. It controls only:

- algorithm selection and description,
- review threshold,
- lowercase conversion,
- punctuation removal.

Matching is column-agnostic. It applies only generic text normalization to the selected match columns and does not assume that a column contains company names, addresses, or any other specific kind of data. Reference columns never contribute to the score.

The matching algorithm pairs individual tokens using fuzzy similarity, then combines those token scores with frequency-based weights. Tokens that occur often contribute less, while rare tokens contribute more; no token is removed solely because it belongs to a presumed business category. Manual weights adjust a token's relative influence. Exact normalized values still match exactly.

## Notes and V1 limits

- Match columns are combined per row for matching and common-token analysis; reference columns are displayed for review only.
- Every detected group must receive an explicit review decision before export. “Keep selected rows” retains every checked original; “Merge selected rows” removes the duplicate group and creates one merged record from field choices among the checked rows; “Not duplicates” retains the group intentionally.
- The audit CSV is written beside the cleaned CSV with `_audit.csv` appended to the filename. It records each group’s number, score, action, and original source/row references.
- Large generic columns with little text variation may produce many candidates. V1 is targeted at files under 10,000 rows.
- The EXE is unsigned. Windows SmartScreen may warn when it is first opened. Production distribution should use a code-signing certificate.
