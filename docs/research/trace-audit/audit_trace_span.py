#!/usr/bin/env python3
"""Streaming, read-only schema audit for a trace_span.csv export.

Usage: python3 audit_trace_span.py INPUT.csv OUTPUT.json
"""
import csv
import hashlib
import json
from datetime import datetime, timezone
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED = ["timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type",
            "status_code", "operation_name", "parent_span"]
INT_RE = re.compile(r"^[+-]?\d+$")
FLOAT_RE = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?$|^[+-]?\d+[eE][+-]?\d+$")
HEX_RE = re.compile(r"^[0-9a-f]+$")
TARGET_TRACE = "9451fd8fdf746a80687451dae4c4e984"

def initial_column():
    return {"empty": 0, "integer_lexemes": 0, "float_lexemes": 0,
            "other_lexemes": 0, "integer_min": None, "integer_max": None,
            "float_min": None, "float_max": None, "lengths": Counter(),
            "examples": []}

def update_lexical(stat, value, numeric_classification=True):
    if value == "":
        stat["empty"] += 1
        return
    stat["lengths"][str(len(value))] += 1
    if len(stat["examples"]) < 5 and value not in stat["examples"]:
        stat["examples"].append(value)
    if not numeric_classification:
        stat["other_lexemes"] += 1
    elif INT_RE.fullmatch(value):
        stat["integer_lexemes"] += 1
        number = int(value)
        stat["integer_min"] = number if stat["integer_min"] is None else min(stat["integer_min"], number)
        stat["integer_max"] = number if stat["integer_max"] is None else max(stat["integer_max"], number)
    elif FLOAT_RE.fullmatch(value):
        stat["float_lexemes"] += 1
        number = float(value)
        stat["float_min"] = number if stat["float_min"] is None else min(stat["float_min"], number)
        stat["float_max"] = number if stat["float_max"] is None else max(stat["float_max"], number)
    else:
        stat["other_lexemes"] += 1

def clean(obj):
    if isinstance(obj, Counter):
        return dict(sorted(obj.items()))
    if isinstance(obj, dict):
        return {key: clean(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [clean(value) for value in obj]
    return obj

def main(input_path, output_path):
    source_path = Path(input_path).resolve()
    source_stat = source_path.stat()
    digest = hashlib.sha256()
    with open(source_path, "rb") as raw:
        for chunk in iter(lambda: raw.read(1024 * 1024), b""):
            digest.update(chunk)
    columns = {name: initial_column() for name in EXPECTED}
    type_counts, status_counts, type_status = Counter(), Counter(), Counter()
    zero_duration_by_type = Counter()
    cmdb_counts, operation_counts = Counter(), Counter()
    cmdb_operations, operation_cmdbs = defaultdict(Counter), defaultdict(Counter)
    id_shapes = {name: Counter() for name in ("span_id", "trace_id", "parent_span")}
    parent_sentinels = Counter()
    selected = {"row_count": 0, "rows": []}
    row_count = malformed_count = 0
    timestamp = {"parseable": 0, "min": None, "max": None, "adjacent_non_decreasing": 0,
                 "adjacent_decreasing": 0, "equal_adjacent": 0, "first_decrease": None}
    previous_timestamp = None

    with open(input_path, "r", encoding="utf-8", newline="") as source:
        reader = csv.reader(source)
        header = next(reader, None)
        for line_number, row in enumerate(reader, start=2):
            row_count += 1
            if len(row) != len(EXPECTED):
                malformed_count += 1
                continue
            record = dict(zip(EXPECTED, row))
            for name, value in record.items():
                update_lexical(columns[name], value,
                               numeric_classification=name not in {"span_id", "trace_id", "parent_span"})

            kind, status = record["type"], record["status_code"]
            type_counts[kind] += 1
            status_counts[status] += 1
            type_status[(kind, status)] += 1
            if record["duration"] == "0":
                zero_duration_by_type[kind] += 1
            cmdb, operation = record["cmdb_id"], record["operation_name"]
            cmdb_counts[cmdb] += 1
            operation_counts[operation] += 1
            cmdb_operations[cmdb][operation] += 1
            operation_cmdbs[operation][cmdb] += 1

            for name in id_shapes:
                value = record[name]
                if value == "":
                    shape = "empty"
                elif HEX_RE.fullmatch(value):
                    shape = f"lower_hex_length_{len(value)}"
                else:
                    shape = f"non_lower_hex_length_{len(value)}"
                id_shapes[name][shape] += 1
            parent = record["parent_span"]
            if parent == "":
                parent_sentinels["empty"] += 1
            elif parent == record["span_id"]:
                parent_sentinels["self_reference"] += 1
            elif parent == "0":
                parent_sentinels["literal_0"] += 1

            value = record["timestamp"]
            if INT_RE.fullmatch(value):
                current = int(value)
                timestamp["parseable"] += 1
                timestamp["min"] = current if timestamp["min"] is None else min(timestamp["min"], current)
                timestamp["max"] = current if timestamp["max"] is None else max(timestamp["max"], current)
                if previous_timestamp is not None:
                    if current < previous_timestamp:
                        timestamp["adjacent_decreasing"] += 1
                        if timestamp["first_decrease"] is None:
                            timestamp["first_decrease"] = {"line": line_number, "previous": previous_timestamp, "current": current}
                    else:
                        timestamp["adjacent_non_decreasing"] += 1
                        if current == previous_timestamp:
                            timestamp["equal_adjacent"] += 1
                previous_timestamp = current
            if record["trace_id"] == TARGET_TRACE:
                selected["row_count"] += 1
                if len(selected["rows"]) < 50:
                    selected["rows"].append(record)

    output = {
        "source": str(source_path),
        "source_fingerprint": {"sha256": digest.hexdigest(), "bytes": source_stat.st_size,
                               "mtime_utc": datetime.fromtimestamp(source_stat.st_mtime, timezone.utc).isoformat()},
        "scan_scope": {"input": "entire CSV, excluding one header row", "csv_parser": "Python stdlib csv.reader",
                       "memory": "single-row iteration plus bounded categorical counters and up to 50 selected-trace rows"},
        "method": "Python csv.reader streaming scan; no source mutation",
        "header": header, "expected_header": EXPECTED, "header_matches_expected": header == EXPECTED,
        "row_count_excluding_header": row_count, "rows_with_unexpected_width": malformed_count,
        "columns": columns,
        "opaque_identifier_columns": ["span_id", "trace_id", "parent_span"],
        "timestamp_order": timestamp,
        "categorical_counts": {"type": type_counts, "status_code": status_counts,
                               "type_by_status_code": {f"{a}|{b}": n for (a,b), n in type_status.items()}},
        "zero_duration": {"total": sum(zero_duration_by_type.values()), "by_type": zero_duration_by_type},
        "cmdb_id": {"distinct": len(cmdb_counts), "counts": cmdb_counts,
                    "operations_by_cmdb": cmdb_operations},
        "operation_name": {"distinct": len(operation_counts), "counts": operation_counts,
                           "cmdbs_by_operation": operation_cmdbs},
        "id_shapes": id_shapes, "parent_span_sentinels": parent_sentinels,
        "selected_trace_id": {"value": TARGET_TRACE, **selected},
        "scope_limitations": ["CSV-only lexical/profile audit; values are not joined to logs, metrics, or other telemetry.",
                              "No graph reconstruction, root inference beyond literal parent sentinels, or causal/fault analysis.",
                              "Timestamp ordering measures adjacent file order only; it does not establish trace-level ordering."]
    }
    with open(output_path, "w", encoding="utf-8") as dest:
        json.dump(clean(output), dest, indent=2, sort_keys=True, allow_nan=False)
        dest.write("\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_trace_span.py INPUT.csv OUTPUT.json")
    main(sys.argv[1], sys.argv[2])
