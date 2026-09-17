# Label-free telemetry API

The prepared index contains only the two available days of telemetry. Every raw
record retains its CSV source fields, repo-relative `source_file`, and
`source_record` with the header counted as record 1. Span IDs remain strings.
Traces use epoch milliseconds; metric/log timestamps use epoch seconds and are
explicitly converted to `timestamp_ms` in returned evidence. Raw duration is
provisionally microseconds; see trace interval calculations in HARNESS_API.md.

Infrastructure only: `build_index.get_frontend(start_ms,end_ms)` returns just
frontend-* spans whose own start falls in the half-open interval. `get_traces(ids)`
returns all recorded spans for selected IDs across both dates. Investigators use
prepared case files and must not rebuild the index or scan other windows.

## Stage M calls

Metrics and logs are blocked until `trace_only.json` has a valid immutable seal.
Only the sealed trace stage's up to five `candidates` are initial components.
One expansion to up to five additional components with explicit adjacent
cross-component trace links is permitted. A global rescue (empty component list)
is allowed once only when trace discovery has no component shortlist and no
initial candidates. Subsequent rescue candidates must occur in that response.

```python
from experiments.frontend_blind_v1.retrieval import get_metrics, get_logs

m = get_metrics(case_dir, ["service-1"], sources=["container"])
# Narrow to exact returned KPI names if the response was truncated:
m2 = get_metrics(case_dir, ["service-1"], sources=["runtime"], kpis=["exact_kpi_name"])
logs = get_logs(case_dir, ["service-1"], contains="error", window="query")
```

There are **20 metric calls and 10 log calls total**, persistent across Python
processes. Each API invocation is one structured call, even if it requests
multiple sources. Budget exhaustion raises; no silent unlimited fallback.
Only the explicitly requested component subset is queried in each invocation.

Metric sources: `container`, `runtime`, `node`, `mesh`, `service`. Responses contain
at most 50 series, with at most 60 representative reference values and 60 query
values per series. Query/reference summaries contain count, median, MAD, range,
min/max source records, time bins, and observed cadence/coverage. Values retain
source row pointers and raw values. No epsilon is substituted for zero MAD;
unknown metric units and counter/gauge semantics remain explicit. If computing
rates, handle counter resets and explain the assumption.

`series` entries have `component` (the source identity), `source`, `kpi_name`,
`query`, `reference`, `signed_median_departure`, and `max_absolute_departure`.
The two numeric departures are null when reference MAD is zero/unavailable.
`query.values`/`reference.values` list objects with `timestamp_ms`, `value`, raw
source fields and provenance. Within each component, response series are ordered
by largest absolute reference-scaled departure; components are interleaved so
one component does not consume the cap. This descriptive retrieval ordering does
not change frozen frontend request rankings. `available_series`, truncation flags,
and exact KPI selection support bounded follow-up. Service-wide fields
`rr`, `sr`, `mrt`, and `count` are separate series; service aggregates are not
replica-level measurements.

The documented source identity `<node>.<pod>` provides a recorded pod/node
mapping. Passing a trace pod ID retrieves matching dotted source identities.
Requesting `sources=["node"]` for that pod retrieves its explicitly recorded
host's node metrics. The response exposes `explicit_mappings`. No node is inferred
from similar names, and no service/replica prefix mapping is invented. Missing
exact/mapped series remains visible as missing coverage.

Logs return at most 200 matched rows, balanced across requested periods/sources
and evenly sampled in timestamp order when truncated. Arguments: `contains`
(optional substring), `window="both"|"query"|"reference"`,
`sources=["service","proxy"]` (optional), and `limit` up to 200. Responses include
`records`, `available_count`, `count`, `truncated`, and the sampling policy.
Lack of a sampled matching event does not establish no event occurred.

Every successful API call automatically saves the full response to the case's
`retrieval_NN_get_metrics.json` or `retrieval_NN_get_logs.json` and appends filters,
component authorization, response path, truncation/counts, and timing to
`retrieval.jsonl`. The returned `response_file` points to that artifact. Run your
additional numerical analysis over these responses and preserve the output.
