"""CSV and filesystem preflight for the offline harness."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path

from .contracts import QueryRow


class InputValidationError(ValueError):
    """A safe, user-facing preflight error."""


@dataclass(frozen=True)
class InputBundle:
    """Validated inputs in deterministic source order."""

    dataset_dir: Path
    query_path: Path
    out_dir: Path
    rows: tuple[QueryRow, ...]


def _resolved(path: str | os.PathLike[str]) -> Path:
    try:
        return Path(path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise InputValidationError("path could not be resolved") from exc


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _overlaps(first: Path, second: Path) -> bool:
    return first == second or _is_within(first, second) or _is_within(second, first)


def _read_query_rows(query_path: Path) -> tuple[QueryRow, ...]:
    rows: list[QueryRow] = []
    seen: set[int] = set()
    try:
        with query_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle, strict=True)
            try:
                header = next(reader)
            except StopIteration:
                raise InputValidationError("query CSV is empty; row_id and instruction headers are required")
            if len(header) != len(set(header)):
                raise InputValidationError("query CSV contains duplicate headers")
            required = {"row_id", "instruction"}
            missing = sorted(required.difference(header))
            if missing:
                raise InputValidationError(
                    "query CSV is missing required header(s): " + ", ".join(missing)
                )
            row_id_index = header.index("row_id")
            instruction_index = header.index("instruction")
            for line_number, values in enumerate(reader, start=2):
                if len(values) != len(header):
                    raise InputValidationError(
                        f"query CSV row {line_number} has the wrong number of fields"
                    )
                raw_id = values[row_id_index].strip()
                if not raw_id:
                    raise InputValidationError(f"query CSV row {line_number} has an invalid row_id")
                try:
                    row_id = int(raw_id, 10)
                except ValueError as exc:
                    raise InputValidationError(
                        f"query CSV row {line_number} has an invalid row_id"
                    ) from exc
                if row_id in seen:
                    raise InputValidationError(f"query CSV row {line_number} repeats row_id {row_id}")
                seen.add(row_id)
                rows.append(QueryRow(row_id=row_id, instruction=values[instruction_index]))
    except InputValidationError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise InputValidationError("query CSV could not be read as valid UTF-8 CSV") from exc
    return tuple(rows)


def _validate_output(out_dir: Path, dataset_dir: Path, query_path: Path) -> None:
    if _overlaps(out_dir, dataset_dir) or _overlaps(out_dir, query_path):
        raise InputValidationError("output path overlaps a supplied input path")
    if out_dir.exists():
        if not out_dir.is_dir():
            raise InputValidationError("output path must be a directory")
        try:
            has_entries = next(out_dir.iterdir(), None) is not None
        except OSError as exc:
            raise InputValidationError("output directory could not be inspected") from exc
        if has_entries:
            raise InputValidationError("output directory must be empty")
        if not os.access(out_dir, os.W_OK | os.X_OK):
            raise InputValidationError("output directory is not writable")
        return

    parent = out_dir.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if not parent.is_dir() or not os.access(parent, os.W_OK | os.X_OK):
        raise InputValidationError("output parent is missing or not writable")


def preflight_inputs(
    dataset_dir: str | os.PathLike[str],
    query_path: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
) -> InputBundle:
    """Validate all paths and query rows before the run writes any artifact."""

    dataset = _resolved(dataset_dir)
    queries = _resolved(query_path)
    output = _resolved(out_dir)
    if not dataset.is_dir():
        raise InputValidationError("dataset path must be an existing directory")
    if not queries.is_file():
        raise InputValidationError("query path must be an existing CSV file")
    rows = _read_query_rows(queries)
    _validate_output(output, dataset, queries)
    return InputBundle(dataset_dir=dataset, query_path=queries, out_dir=output, rows=rows)
