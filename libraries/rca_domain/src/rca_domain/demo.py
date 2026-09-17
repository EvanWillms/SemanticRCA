"""Offline completion-aware investigation demo.

Run from the repository checkout with both source packages on ``PYTHONPATH``::

    PYTHONPATH=libraries/rca_domain/src:libraries/trace_semantics/src \
        python -m rca_domain.demo

The trace encoder is imported inside :func:`run_demo` so the core domain
package does not acquire a runtime dependency on the producer.
"""

from __future__ import annotations

import json
from typing import Any


def _span(
    *,
    trace_id: str,
    span_id: str,
    component: str,
    operation: str,
    status: str,
    record: int,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span": "",
        "cmdb_id": component,
        "operation_name": operation,
        "type": "rpc",
        "status_code": status,
        "timestamp": "1000",
        "duration": "25",
    }
    if details:
        raw.update(details)
    return {
        "raw": raw,
        "locator": {"source": "synthetic-demo", "record": record},
    }


def run_demo() -> dict[str, Any]:
    """Run one scripted assessment, one useful operation and reassessment.

    This is intentionally authored synthetic evidence.  It does not call an
    LLM and does not claim diagnosis accuracy for real incidents.
    """
    # The producer is a standalone package.  Keeping these imports local
    # allows the domain API to remain installable without that package.
    from trace_semantics import EncodingPolicy, encode_traces

    from .ingestion import from_semantic_traces
    from .investigation import investigate

    scope = {
        "case_id": "demo-case",
        "deployment": "demo-deployment",
        "incident_count": 1,
        "projection": ["component", "reason"],
    }
    policy = EncodingPolicy(
        version="synthetic-demo-v1",
        operation_mappings={
            "HandleRequest": "frontend.request",
            "InspectWorker": "worker.inspect",
        },
        timestamp_unit="ms",
        duration_unit="ms",
    )

    frontend_trace = {
        "trace_id": "demo-frontend-trace",
        "deployment": scope["deployment"],
        "spans": [
            _span(
                trace_id="demo-frontend-trace",
                span_id="frontend-root",
                component="frontend-1",
                operation="HandleRequest",
                status="unknown-status",
                record=1,
            )
        ],
    }
    worker_trace = {
        "trace_id": "demo-worker-trace",
        "deployment": scope["deployment"],
        "spans": [
            _span(
                trace_id="demo-worker-trace",
                span_id="worker-root",
                component="worker-1",
                operation="InspectWorker",
                status="unknown-status",
                record=2,
                details={
                    "queue_depth": 64,
                    "queue_capacity": 64,
                    "resource_state": "saturated",
                },
            )
        ],
    }
    frontend_description = encode_traces([frontend_trace], policy)
    worker_description = encode_traces([worker_trace], policy)

    initial = from_semantic_traces(
        envelopes=[
            {
                "packet_id": "demo-frontend-packet",
                "source_snapshot_id": "demo-snapshot",
                "description": frontend_description,
            }
        ],
        scope=scope,
    )

    def assessor(state: dict[str, Any]) -> dict[str, Any]:
        observations = state["evidence"].get("observations", {})
        worker_ids = [
            observation_id
            for observation_id, observation in observations.items()
            if observation.get("recording_component") == "worker-1"
        ]
        if not worker_ids:
            return {
                "decision": "continue",
                "evidence_revision": state["evidence"]["revision"],
                "incidents": [],
                "gaps": ["worker evidence"],
                "rationale": "The authored frontend observation needs one worker inspection.",
                "action": {
                    "name": "inspect_worker",
                    "arguments": {},
                    "gap": "worker evidence",
                },
            }
        support_id = worker_ids[0]
        return {
            "decision": "complete",
            "evidence_revision": state["evidence"]["revision"],
            "incidents": [
                {
                    "component": "worker-1",
                    "reason": "resource saturation",
                    "support": [support_id],
                    "explanation": (
                        "The scripted assessor maps the authored saturated resource state "
                        "to the requested reason."
                    ),
                }
            ],
            "gaps": [],
            "rationale": "The requested component and reason are supported by the follow-up evidence.",
        }

    def inspect_worker(arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        if arguments != {}:
            raise ValueError("inspect_worker takes no arguments")
        return from_semantic_traces(
            envelopes=[
                {
                    "packet_id": "demo-worker-packet",
                    "source_snapshot_id": "demo-snapshot",
                    "description": worker_description,
                }
            ],
            scope=state["evidence"]["scope"],
        )

    result = investigate(
        initial,
        assessor,
        {"inspect_worker": inspect_worker},
        {"components": ["worker-1", "frontend-1"], "reasons": ["resource saturation"]},
    )
    result["demo"] = {
        "mode": "synthetic",
        "live_llm": False,
        "real_diagnosis_accuracy_claim": False,
    }
    return result


def main() -> None:
    """Print the demo result as one JSON object."""
    print(json.dumps(run_demo(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
