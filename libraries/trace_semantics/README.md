# Deterministic trace semantics

A standalone domain library for traces that a caller has already selected as
fault related. It separates facts that can be described deterministically from
items requiring additional evidence or interpretation, then constructs a
versioned description set. It does not decide which traces are fault related.

## Run the demo

From the repository root, without installation or network access:

```sh
PYTHONPATH=libraries/trace_semantics/src python3 -m trace_semantics.demo
```

Expected result: `PASS`, two selected traces, three described occurrences, one
unknown operation returned before description construction, retained raw
evidence and deterministic output. After installation, use
`python3 -m trace_semantics.demo` directly.

The demo reads bundled, inspectable fixtures from
[`src/trace_semantics/fixtures/demo/`](src/trace_semantics/fixtures/demo/README.md):
`traces.json`, `policy.json` and `expected.json`. Expectations are checked by
the demo verifier and never passed to the encoder.

To save the intermediate and final artifacts into a new directory:

```sh
PYTHONPATH=libraries/trace_semantics/src python3 -m trace_semantics.demo \
  --out /tmp/trace-domain-demo
```

The result contains `partition.json`, `deferred.json`, `description.json` and
`summary.json`. An existing output directory is rejected to preserve earlier
runs. For a different authored case, copy the three fixture JSON files, edit
the evidence, policy and expectations, and pass `--fixture-dir YOUR_DIRECTORY`.

This checkpoint is ready for the authored happy path: complete Track-1-shaped
records, string identifiers, `""` as the root parent marker, and a caller-scoped
operation/unit policy. Broader hardening remains explicit in
[`review.md`](../../specs/011-deterministic-trace-domain/review.md); this is not
full acceptance of the original robustness specification.

The runtime uses the Python standard library. Its input is supplied evidence;
it does not retrieve telemetry, call models or import the SymbolicRCA runtime.

## Evidence boundaries

Raw operation names, component identities, parent references, timestamps,
durations, statuses and source locators remain evidence. A caller-supplied
operation definition can give an observation a semantic symbol. Unmapped
meanings remain deferred and distinguishable by their original values.

Deferral is local: unknown status meaning does not prevent retention of the
span's operation, identity or parent reference. Missing or conflicting ancestry
does not become an invented edge. Repeated operation occurrences preserve their
membership and measurements; repetition alone does not establish retries.

Recorded components are recording identities. Parent relationships are recorded
ancestry. Neither proves the target service or a causal relationship. Supplied
fault association does not verify request failure or business outcome.

## Installation

From the repository root:

```sh
python3 -m pip install ./libraries/trace_semantics
```

This directory can also be copied out and installed independently. Python 3.10
or newer is required. Packaging uses setuptools; runtime dependencies are empty.

## Development

```sh
cd libraries/trace_semantics
python3 -m pytest -q
```

The authored controls test representation and deferral behavior. They do not
establish compression savings, diagnostic accuracy or real-data generalization.

## Public API

The two stages let callers hand off unresolved items before constructing the
description set:

```python
from trace_semantics import EncodingPolicy, partition_traces, describe

traces = [{
    "trace_id": "selected-trace",
    "deployment": "example",
    "recorded_recovery": "complete_relative_to_snapshot",
    "spans": [{
        "raw": {
            "trace_id": "selected-trace", "span_id": "root", "parent_span": "",
            "cmdb_id": "frontend-1", "operation_name": "GET /cart", "type": "http",
            "timestamp": "1000", "duration": "25", "status_code": "200",
        },
        "locator": {"path": "traces.csv", "record": 2, "source_digest": "example"},
    }],
}]
policy = EncodingPolicy(
    version="example-operations-v1",
    operation_mappings={"GET /cart": "cart.request"},
    timestamp_unit="ms",
    duration_unit="ms",
)

partition = partition_traces(traces, policy)
deferred = partition["deferred"]  # Available to your downstream processor now.
description = describe(partition)
```

`encode_traces(traces, policy)` runs both stages in one call. No downstream
processor is invoked by the package. The selected trace in this example has a
known operation mapping; its status meaning remains unresolved even though the
raw status looks like an HTTP success code.

Input records use the recovered-trace shape shown above. Whole source traces
are retained in each output trace's `raw` field, including extra fields and
context. A source locator is supplied evidence; the library does not read that
path or verify its digest. Malformed JSON-shaped evidence is deferred locally.
Inputs outside finite JSON (such as arbitrary Python objects or numeric NaN)
are caller errors. A string such as `"NaN"` is retained as raw evidence.

The policy supplies a versioned exact-name operation mapping. It is the caller's
responsibility to establish where that mapping applies; the package does not
certify the mapping's meaning. Unit declarations apply to the supplied
collection. Use separate policies for sources with incompatible units. Unknown
units are allowed, with unresolved timing interpretation deferred.

The result distinguishes physical record count from unambiguous span occurrence
count. Exact raw duplicates retain all locators but contribute one occurrence.
Different raw rows for the same scoped span identity are conflicting evidence,
not additional known occurrences. Neither record order nor sorted serialization
establishes execution order.

Determinism means the same supplied evidence and policy produce the same
serialized result. It does not assert structural equivalence after renaming
identifiers, changing source locators or reordering raw arrays. Status meaning,
business outcome, retry behavior, target service and causation require separate
evidence or processing.
