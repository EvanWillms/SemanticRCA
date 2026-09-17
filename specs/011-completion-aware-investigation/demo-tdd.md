# Completion-aware investigation demo

The authored demo is a synthetic, offline happy path. It encodes one frontend
trace with the standalone `trace_semantics` producer, ingests it into the RCA
evidence packet, executes one declared `inspect_worker` operation, and
reassesses the merged evidence before returning a supported component/reason
answer. It makes no live LLM call and makes no real diagnosis-accuracy claim.

From the repository checkout, run it with the producer source package visible
for this demo command:

```sh
PYTHONPATH=libraries/rca_domain/src:libraries/trace_semantics/src \
  python -m rca_domain.demo
```

`trace_semantics` is a producer dependency of this demo only. The standalone
`rca_domain` package keeps its public ingestion and investigation APIs
independent of that producer package.
