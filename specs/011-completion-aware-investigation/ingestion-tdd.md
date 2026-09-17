# Ingestion TDD slice

The first vertical slice fixes the public boundary
`rca_domain.ingestion.from_semantic_traces(envelopes, scope)`.

The tests use a tiny independently authored `trace-description-v1` fixture. The
fixture exercises the native policy and meaning dictionary, one trace and node,
one physical evidence row with an opaque locator, trace raw recovery/context,
and one deferred item. The assertions cover:

- a detached `rca-evidence-v1` packet with a stable observation identity and
  preserved raw, locator, coverage, and deferred data;
- duplicate views collapsing to one observation while repeated calls retain the
  same identity, and changed content under that identity being rejected; and
- rejection of an unsupported description schema and a node occurrence that
  points at missing evidence.

The stable observation ID is the canonical SHA-256 identity of
`[source_snapshot_id, deployment, trace_id, producer_evidence_id]`. Producer
IDs remain available as aliases in each packet definition so deferred native
references can be resolved after ingestion.

Focused execution:

```text
PYTHONPATH=libraries/rca_domain/src pytest -q libraries/rca_domain/tests/test_ingestion.py
3 passed
```
