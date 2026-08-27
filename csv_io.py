from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


def read_csv(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a CSV using supported Windows-friendly encodings."""

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            with open(path, "r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    raise ValueError("The CSV has no header row.")
                headers = [str(header) for header in reader.fieldnames]
                rows = [
                    {header: (row.get(header) or "") for header in headers}
                    for row in reader
                ]
                return headers, rows
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"Unable to decode CSV: {last_error}")


def write_csv(
    path: str | Path,
    headers: list[str],
    rows: Iterable[dict[str, str]],
) -> None:
    """Write rows as a UTF-8 CSV with a BOM for Windows tools."""

    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
