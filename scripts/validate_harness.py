#!/usr/bin/env python3
"""Validate the empty-output runner's on-disk scaffold.

This validator checks I/O shape only.  Passing it is not benchmark validation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path


class ValidationError(Exception):
    """An expected, user-actionable validation failure."""


_EVIDENCE_HEADINGS = ["## Answer", "## Confidence", "## Evidence", "## Ruled out"]
_USAGE_COUNTERS = ("prompt_tokens", "completion_tokens", "calls")


def _validate_evidence_content(content: str) -> None:
    headings = [line for line in content.splitlines() if line.startswith("## ")]
    if headings != _EVIDENCE_HEADINGS:
        raise ValidationError("evidence artifact has the wrong sections")

    sections: dict[str, str] = {}
    lines = content.splitlines()
    heading_positions = [index for index, line in enumerate(lines) if line.startswith("## ")]
    for index, heading in enumerate(_EVIDENCE_HEADINGS):
        start = heading_positions[index] + 1
        end = heading_positions[index + 1] if index + 1 < len(_EVIDENCE_HEADINGS) else len(lines)
        body = "\n".join(lines[start:end]).strip()
        if not body:
            raise ValidationError("evidence artifact contains an empty section")
        sections[heading] = body.lower()

    answer = sections["## Answer"]
    if "diagnosis" not in answer or not any(word in answer for word in ("not implemented", "unimplemented")):
        raise ValidationError("evidence Answer does not identify the unimplemented diagnosis")
    confidence = sections["## Confidence"]
    if "confidence" not in confidence or not any(
        phrase in confidence for phrase in ("not measured", "no confidence", "not available", "not implemented")
    ):
        raise ValidationError("evidence Confidence does not identify an unmeasured placeholder")
    evidence = sections["## Evidence"]
    if "evidence" not in evidence or not any(
        phrase in evidence for phrase in ("no evidence", "not assessed", "does not read telemetry", "no telemetry")
    ):
        raise ValidationError("evidence Evidence does not identify unavailable evidence")
    ruled_out = sections["## Ruled out"]
    if "alternative" not in ruled_out or not any(
        phrase in ruled_out for phrase in ("no alternative", "not assessed", "not implemented")
    ):
        raise ValidationError("evidence Ruled out does not identify unassessed alternatives")


def _csv_rows(path: Path, kind: str) -> tuple[list[str], list[list[str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            header = next(reader, None)
            if header is None:
                raise ValidationError(f"{kind} CSV is empty")
            if len(set(header)) != len(header):
                raise ValidationError(f"{kind} CSV contains duplicate headers")
            rows = []
            for row in reader:
                if len(row) != len(header):
                    raise ValidationError(f"{kind} CSV contains a malformed row")
                rows.append(row)
            return header, rows
    except FileNotFoundError:
        raise ValidationError(f"{kind} CSV is unavailable") from None
    except (OSError, UnicodeError, csv.Error):
        raise ValidationError(f"{kind} CSV cannot be read") from None


def _query_ids(path: Path) -> list[int]:
    header, rows = _csv_rows(path, "query")
    if "row_id" not in header:
        raise ValidationError("query CSV is missing the row_id header")
    if "instruction" not in header:
        raise ValidationError("query CSV is missing the instruction header")

    id_index = header.index("row_id")
    ids: list[int] = []
    for row in rows:
        try:
            row_id = int(row[id_index])
        except (TypeError, ValueError):
            raise ValidationError("query CSV contains an invalid row_id") from None
        ids.append(row_id)
    if len(ids) != len(set(ids)):
        raise ValidationError("query CSV contains duplicate row_ids")
    return ids


def _prediction_ids(path: Path) -> list[int]:
    header, rows = _csv_rows(path, "predictions")
    if "row_id" not in header:
        raise ValidationError("predictions.csv is missing the row_id header")
    if "prediction" not in header:
        raise ValidationError("predictions.csv is missing the prediction header")

    id_index = header.index("row_id")
    prediction_index = header.index("prediction")
    ids: list[int] = []
    for row in rows:
        try:
            row_id = int(row[id_index])
        except (TypeError, ValueError):
            raise ValidationError("predictions.csv contains an invalid row_id") from None
        if row[prediction_index] != "":
            raise ValidationError("predictions.csv contains a nonblank prediction")
        ids.append(row_id)
    return ids


def _usage_ids(path: Path) -> list[int]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        raise ValidationError("usage.jsonl is unavailable") from None
    except (OSError, UnicodeError):
        raise ValidationError("usage.jsonl cannot be read") from None

    ids: list[int] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            raise ValidationError("usage.jsonl contains invalid JSON") from None
        if not isinstance(record, dict):
            raise ValidationError("usage.jsonl contains a non-object record")
        try:
            row_id = record["row_id"]
            wall_s = record["wall_s"]
            models = record["models"]
        except KeyError:
            raise ValidationError("usage.jsonl record is missing a required field") from None
        if not isinstance(row_id, int) or isinstance(row_id, bool):
            raise ValidationError("usage.jsonl contains an invalid row_id")
        if not isinstance(wall_s, (int, float)) or isinstance(wall_s, bool):
            raise ValidationError("usage.jsonl contains an invalid wall_s")
        try:
            finite_wall = math.isfinite(wall_s)
        except (OverflowError, ValueError):
            finite_wall = False
        if not finite_wall or wall_s < 0:
            raise ValidationError("usage.jsonl contains an invalid wall_s")
        if models != {}:
            raise ValidationError("usage.jsonl contains model usage")
        for counter in _USAGE_COUNTERS:
            value = record.get(counter)
            if not isinstance(value, int) or isinstance(value, bool) or value != 0:
                raise ValidationError("usage.jsonl contains a nonzero or invalid usage counter")
        ids.append(row_id)
    return ids


def _evidence_ids(path: Path) -> list[int]:
    evidence_dir = path / "evidence"
    if not evidence_dir.is_dir():
        raise ValidationError("evidence directory is unavailable")
    try:
        entries = list(evidence_dir.iterdir())
    except OSError:
        raise ValidationError("evidence directory cannot be read") from None

    ids: list[int] = []
    for entry in entries:
        if entry.suffix != ".md":
            raise ValidationError("evidence directory contains an unexpected artifact")
        try:
            row_id = int(entry.stem)
        except ValueError:
            raise ValidationError("evidence directory contains an invalid row_id") from None
        if entry.name != f"{row_id}.md":
            raise ValidationError("evidence directory contains a noncanonical row_id")
        try:
            content = entry.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise ValidationError("evidence artifact cannot be read") from None
        _validate_evidence_content(content)
        ids.append(row_id)
    return ids


def _validate_root_artifacts(out: Path) -> None:
    try:
        names = {entry.name for entry in out.iterdir()}
    except OSError:
        raise ValidationError("output directory cannot be read") from None
    if names != {"predictions.csv", "usage.jsonl", "evidence"}:
        raise ValidationError("output directory contains unexpected artifacts")


def validate(queries: Path, out: Path) -> None:
    if not out.is_dir():
        raise ValidationError("output directory is unavailable")
    _validate_root_artifacts(out)
    expected = _query_ids(queries)
    prediction_ids = _prediction_ids(out / "predictions.csv")
    usage_ids = _usage_ids(out / "usage.jsonl")
    evidence_ids = _evidence_ids(out)
    expected_set = set(expected)
    for actual in (prediction_ids, usage_ids, evidence_ids):
        if len(actual) != len(set(actual)) or set(actual) != expected_set:
            raise ValidationError("output artifacts do not exactly cover query row_ids")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate empty-output harness artifacts")
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        validate(args.queries, args.out)
    except ValidationError as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 1
    print("Harness scaffold-only validation passed; this is not official benchmark validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
