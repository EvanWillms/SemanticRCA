# Frontend blind v1 harness API

The harness consumes only `scope.csv`, the public query file, and trace CSVs.
It never opens `data/track-1/dev/query_dev.csv`, scoring points, record files,
or diagnosis reports.

`build_index.TraceIndex` is the reusable label-free data boundary:

```python
from experiments.frontend_blind_v1.build_index import TraceIndex
index = TraceIndex()
frontend_rows = index.get_frontend(start_ms, end_ms)
traces = index.get_traces(["trace-id"])
```

Each returned row preserves the source columns as strings and adds
`source_file` (repository-relative when possible) and `source_record` (CSV
record number including the header as record 1). `get_frontend` is half-open;
`get_traces` returns every recorded span for each requested trace across both
days, grouped by trace ID.

`run_case.prepare_case(row_id)` builds one ignored private case directory. It
writes `scope.json`, `rankings.json`, `trace_evidence.json`, `run_inputs.json`,
and `run.json`. `run_case.inspect_case(case_dir)` returns a compact, safe
investigator view containing the requested prompt, coverage, top-1/3/5/10
prefixes for duration/MAD/Isolation Forest, and per-trace root timing,
reference comparisons, immediate attribution, reachability paths, interval
unions, uncovered time, flags, and provenance. It intentionally leaves out
unselected raw traces.

The ranking JSON preserves every query root and its arm eligibility. Arm A is
raw duration over all roots. Arm B is PyOD MAD per direct-child operation-count
cohort, with at least 20 reference roots, positive median, and nonzero MAD;
only positive signed departures enter its inspection ranking. Arm C fits one
PyOD Isolation Forest (100 trees, seed 42, `max_samples="auto"`, one worker)
to pooled signed reference MAD scores and ranks positive query departures.
All tie ranges are `[first_rank, last_rank]`; ordering breaks ties by trace ID
and span ID.

`trace_evidence.build_evidence` audits parent links, duplicate IDs, missing
parents, roots, cycles, depth-eight traversal, duplicate-safe path retention,
direct-child interval unions clipped to parent/root intervals, and uncovered
time. Immediate attribution and dependency reachability are separate fields.

