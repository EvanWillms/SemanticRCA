"""Small offline source-to-descriptor demonstration of the public domain API.

This is a demo receipt, not the full versioned artifact bundle from the plans.
No telemetry, labels, model credentials or runner policy are modified.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from rca.baselining import (
    BaselinePolicy, SourceLocator, SourceSnapshot, assign_queries,
    collect_requests, freeze_baselines, prepare_sources,
)
from rca.comparisons import ComparisonDefinition, describe
from rca.telemetry.inventory import inventory
from rca.telemetry.trace_index import TRACE_PARSER_VERSION, TRACE_EXTRACTION_VERSION


def run_demo(dataset_dir: Path, deployment: str, anchor_ms: int,
             output_dir: Path) -> dict:
    """Run one fixed reference policy and expose every query outcome."""
    view = prepare_sources(dataset_dir, inventory(dataset_dir, deployment), output_dir)
    policy = BaselinePolicy(normalization_id="provisional-us-to-ms-v1")
    batch = collect_requests(view, deployment, anchor_ms, policy)
    snapshot = SourceSnapshot(
        snapshot_id=view.snapshot_id, deployment=deployment,
        sources=tuple(SourceLocator(view.snapshot_id, source["sha256"],
                                    selector=source["path"]) for source in view.sources),
        parser_version=TRACE_PARSER_VERSION,
        extraction_version=TRACE_EXTRACTION_VERSION,
    )
    baseline_set = freeze_baselines(batch, snapshot, anchor_ms, policy)
    assignments = assign_queries(batch, baseline_set)
    by_id = {item.observation_id: item for item in batch.observations}
    definition = ComparisonDefinition(diagnostics=("ratio", "mad"))
    descriptors = tuple(describe(by_id[item.observation_id], item, item.baseline,
                                 item.structural_population, definition)
                        for item in assignments.assignments)
    return {
        "schema_version": "baseline-comparison-demo-v1",
        "snapshot_id": view.snapshot_id,
        "baseline_set_id": baseline_set.set_id,
        "policy_id": policy.policy_id,
        "status": baseline_set.status,
        "source_inventory": list(view.sources),
        "observation_count": len(batch.observations),
        "assignment_count": len(assignments.assignments),
        "unresolved_count": len(assignments.unresolved),
        "baselines": [{"baseline_id": item.baseline_id,
                       "context": item.c1_key,
                       "support": item.support.status,
                       "reasons": item.support.reasons,
                       "member_count": len(item.member_ids),
                       "median_ms": item.statistics.median,
                       "stability": item.stability.state,
                       "qualifications": item.qualifications}
                      for item in baseline_set.baselines],
        "descriptors": [item.to_dict() for item in descriptors],
        "acceptance_gaps": [
            "Formal baseline/descriptor artifact bundle build and validation CLIs are deferred.",
            "This demo constructs descriptors; it does not certify the full semantic evidence graph or publish trusted review rankings.",
            "The full B01–B12/D01–D12 acceptance matrices and large-dataset performance measurements remain deferred.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True, type=Path)
    parser.add_argument("--scope-file", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        scope = json.loads(args.scope_file.read_text())
        if set(scope) != {"schema_version", "deployment", "anchor"} or scope["schema_version"] != "baseline-scope-v1":
            raise ValueError("invalid baseline scope")
        anchor = datetime.fromisoformat(scope["anchor"])
        if anchor.utcoffset() is None:
            raise ValueError("anchor requires an explicit UTC offset")
        report_path = args.output_dir / "demo.json"
        if report_path.exists():
            raise ValueError("demo output already exists; use a fresh output directory")
        report = run_demo(args.dataset_dir, scope["deployment"], int(anchor.timestamp() * 1000), args.output_dir)
        report_path.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"status": report["status"], "assignments": report["assignment_count"],
                          "baselines": len(report["baselines"]), "report": str(report_path)}))
        return 0 if report["status"] == "completed" else 4
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
