"""Run the bundled, offline happy path: ``python -m trace_semantics.demo``."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from importlib import resources
from pathlib import Path
from typing import Any

from . import EncodingPolicy, canonical_json, describe, partition_traces


def _load_json(path: Any) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant is not allowed: {value}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _load_fixture(fixture_dir: Any) -> tuple[list[dict[str, Any]], EncodingPolicy, dict[str, Any]]:
    traces = _load_json(fixture_dir.joinpath("traces.json"))
    policy_data = _load_json(fixture_dir.joinpath("policy.json"))
    expected = _load_json(fixture_dir.joinpath("expected.json"))
    if not isinstance(traces, list) or not isinstance(policy_data, dict) or not isinstance(expected, dict):
        raise TypeError("demo fixture files have the wrong JSON shape")
    try:
        policy = EncodingPolicy(
            version=policy_data["version"],
            operation_mappings=policy_data["operation_mappings"],
            timestamp_unit=policy_data.get("timestamp_unit"),
            duration_unit=policy_data.get("duration_unit"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("demo policy fixture is invalid") from exc
    return traces, policy, expected


def _summary(traces: list[dict[str, Any]], policy: EncodingPolicy, partition: dict[str, Any], description: dict[str, Any]) -> dict[str, Any]:
    recovered_raw = [
        raw
        for trace in description["traces"]
        for raw in trace.get("raw_envelopes", [trace["raw"]])
    ]
    return {
        "result": "PASS",
        "selected_traces": len(traces),
        "described_occurrences": sum(trace["coverage"].get("occurrence_count", 0) or 0 for trace in description["traces"]),
        "deferred_before_description": dict(sorted(Counter(item["reason"] for item in partition["deferred"]).items())),
        "operations": description["meaning_dictionary"]["operations"],
        "raw_evidence_preserved": sorted(_json_text(raw) for raw in recovered_raw) == sorted(_json_text(raw) for raw in traces),
        "deterministic": canonical_json(description) == canonical_json(describe(partition_traces(traces, policy))),
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    """Verify the fixture through partition and description, optionally writing artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path, help="directory containing traces.json, policy.json, expected.json")
    parser.add_argument("--out", type=Path, help="new directory for partition/deferred/description/summary JSON")
    args = parser.parse_args(argv)
    if args.out is not None and args.out.exists():
        raise FileExistsError(f"output directory already exists: {args.out}")
    fixture_dir = args.fixture_dir or resources.files("trace_semantics").joinpath("fixtures", "demo")
    traces, policy, expected = _load_fixture(fixture_dir)
    partition = partition_traces(traces, policy)
    deferred = partition["deferred"]
    description = describe(partition)
    summary = _summary(traces, policy, partition, description)
    if not summary["raw_evidence_preserved"] or not summary["deterministic"]:
        raise ValueError(f"computed demo invariants failed: {summary!r}")
    if canonical_json(summary) != canonical_json(expected):
        raise ValueError(f"expected summary mismatch: expected {expected!r}, computed {summary!r}")
    if args.out is not None:
        try:
            args.out.mkdir(parents=True)
        except FileExistsError as exc:
            raise FileExistsError(f"output directory already exists: {args.out}") from exc
        for name, value in (
            ("partition.json", partition), ("deferred.json", deferred),
            ("description.json", description), ("summary.json", summary),
        ):
            args.out.joinpath(name).write_text(_json_text(value), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return summary


if __name__ == "__main__":
    main()
