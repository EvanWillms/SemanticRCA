"""Pretrial exposed-control verification; never supplied to investigators."""
from pathlib import Path
import json
import math


def main():
    root = Path(__file__).resolve().parents[4]
    case = root / "data/experiments/frontend-blind-v1/cases/25"
    previous = json.loads((root / "docs/research/examples/track-1-case-25-pyod-results/summary.json").read_text())
    rankings = json.loads((case / "rankings.json").read_text())
    evidence = json.loads((case / "trace_evidence.json").read_text())
    assert rankings["reference_roots"] == previous["reference_roots"] == 2568
    assert rankings["query_roots"] == previous["query_roots"] == 2729
    assert rankings["eligible"] == 2729
    winner = rankings["leaders"]["mad"]["1"][0]
    old = previous["leaders"]["mad_score"][0]
    assert winner["trace_id"] == old["trace_id"]
    assert math.isclose(winner["mad_score"], old["mad_score"], rel_tol=1e-10)
    record = next(r for r in evidence["traces"] if r["trace_id"] == winner["trace_id"])
    assert math.isclose(record["root"]["duration_ms"], 428.249, abs_tol=1e-9)
    attribution = record["immediate_attribution"]
    child = attribution["largest_direct_child"]
    assert child["parent_span"] == winner["span_id"]
    assert math.isclose(child["duration_ms"], 386.142, abs_tol=1e-9)
    receivers = attribution["linked_receivers"]
    assert len(receivers) == 1
    assert receivers[0]["parent_span"] == child["span_id"]
    assert receivers[0]["cmdb_id"] == "checkoutservice-2"
    assert record["recorded_span_count"] == 37
    assert not record["flags"]["missing_parents"]
    print("PASS exposed-control counts, winner/score, millisecond conversion, parent links, and complete 37-span trace")


if __name__ == "__main__":
    main()
