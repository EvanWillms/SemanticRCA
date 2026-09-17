# RCA domain demo

A small domain library that takes semantic encoded traces into an investigation
loop. It preserves source-linked observations and unknowns, asks an injected
assessor whether another operation is useful, and returns an answer with an
explicit reason for stopping.

## Quick demo

From the repository root:

```sh
PYTHONPATH=libraries/rca_domain/src:libraries/trace_semantics/src python3 -m rca_domain.demo
```

The authored demo uses the actual `trace_semantics.encode_traces` producer, a
scripted assessor and one deterministic follow-up. It exercises the handoff and
loop; it is not live-model diagnosis or a benchmark-accuracy result. The producer
is a demo dependency; the domain package itself consumes JSON-compatible data
and does not import it.

## Public interface

```python
from rca_domain import from_semantic_traces, investigate

evidence = from_semantic_traces(
    [{"packet_id": "case-traces", "source_snapshot_id": "snapshot-1",
      "description": encoded_trace_description}],
    {"case_id": "case-1", "deployment": "demo", "incident_count": 1,
     "projection": ["component", "reason"]},
)
result = investigate(
    evidence, assessor, {"inspect_worker": inspect_worker},
    {"components": ["frontend-1", "worker-1"],
     "reasons": ["resource saturation"]},
)
```

`description` is the producer's versioned `trace-description-v1` output.
The assessor receives a detached state containing evidence, feedback and attempt
history. An operation receives its arguments and the detached state, and returns
a new evidence packet for the same case. See `demo.py` for concrete callbacks.

Results separate the answer, evidence adequacy, execution status and investigation
stop reason. Legal best guesses remain qualified when evidence or attempts run
out. Unknown status codes are retained; semantic operation names do not establish
business success, retries or root cause.

## Core checks

```sh
PYTHONPATH=libraries/rca_domain/src:libraries/trace_semantics/src python3 -m pytest libraries/rca_domain/tests -q
```

Runtime domain code uses the Python standard library. Packaging metadata supports
`python3 -m pip install ./libraries/rca_domain` with setuptools available; source
checkout demo execution is the immediate handoff target.

## Demo limitations

This is the user-requested minimal happy path. Callback attempts are bounded;
callbacks run in-process and **cannot be forcibly interrupted** by this library.
Do not mistake the attempt cap for a hard time or dollar limit. Live provider
integration must enforce those limits separately before use.

S01 compatibility, exhaustive onset/projection checks, subprocess isolation,
cost enforcement, advanced retry/progress rules, full L01–L18 acceptance,
standalone installation verification and runner persistence integration remain
follow-up work. A demo-ready interface is not full feature acceptance.
