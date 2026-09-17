"""Run the authored, offline happy path: python -m trace_semantics.demo."""

import json
from collections import Counter

from . import EncodingPolicy, canonical_json, describe, encode_traces, partition_traces


def main() -> None:
    """Demonstrate an early handoff followed by deterministic descriptions."""
    def span(trace_id: str, span_id: str, parent: str, operation: str, record: int) -> dict:
        return {
            "raw": {
                "trace_id": trace_id, "span_id": span_id, "parent_span": parent,
                "cmdb_id": "example-worker", "operation_name": operation,
                "type": "rpc", "status_code": "0",
                "timestamp": "1000", "duration": "25",
            },
            "locator": {"path": "authored-demo.csv", "record": record},
        }

    traces = [
        {"trace_id": "selected-1", "deployment": "authored-demo", "spans": [
            span("selected-1", "root", "", "HandleRequest", 2),
            span("selected-1", "child", "root", "UnmappedOperation", 3),
        ]},
        {"trace_id": "selected-2", "deployment": "authored-demo", "spans": [
            span("selected-2", "root", "", "HandleRequest", 4),
        ]},
    ]
    policy = EncodingPolicy(
        version="authored-demo-v1",
        operation_mappings={"HandleRequest": "request.handle"},
        timestamp_unit="ms", duration_unit="ms",
    )
    partition = partition_traces(traces, policy)
    deferred = partition["deferred"]  # Ready for another processor before describe().
    assert sum(item["reason"] == "unknown_operation" for item in deferred) == 1

    result = describe(partition)
    assert [trace["raw"] for trace in result["traces"]] == traces
    assert sum(trace["coverage"]["occurrence_count"] for trace in result["traces"]) == 3
    assert canonical_json(result) == canonical_json(encode_traces(traces, policy))
    print(json.dumps({
        "result": "PASS",
        "selected_traces": len(traces),
        "described_occurrences": 3,
        "deferred_before_description": dict(sorted(Counter(item["reason"] for item in deferred).items())),
        "operations": result["meaning_dictionary"]["operations"],
        "raw_evidence_preserved": True,
        "deterministic": True,
    }, indent=2))


if __name__ == "__main__":
    main()
