# Source grounding and adoption boundaries

Prepared 2026-09-17 for [the specification](spec.md) and [ADR 0009](../../docs/adr/0009-track1-trace-extraction.md). This records documentation inspection and prior evidence; it is not a new dataset run or an implementation result.

## Governing Track-1 inputs

The user supplied these local official documents from checkout revision `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`:

| Source | Content identity and relevant sections |
|---|---|
| [track-1/docs/data.md](/Users/nonadmin/Development/mantisgrid-hackathon/hackathon-2026-official/track-1/docs/data.md) | SHA256 `c3813bb8447c28af56940027da3521c54d8b1b9fed6882f3235c01c998c24bda`; bundle layout, cases/task projections, telemetry columns, units, large-file and naming traps, unseen deployment. |
| [track-1/docs/scoring.md](/Users/nonadmin/Development/mantisgrid-hackathon/hackathon-2026-official/track-1/docs/scoring.md) | SHA256 `3fbbe6f435139d243453dcf5cceed55f19add04c987a4b5fda740a65dadbc6af`; accuracy/evidence/cost, unseen deployment, incident count, exact names, field order, time tolerance, best guesses, isolation. |

These paths locate the inspected documentation only. They are not runtime dependencies. The revision, official repository-relative paths, and hashes identify the source even if the checkout moves. The participant agreement governs scoring weights; this feature does not set them.

### Dataset contract used here

- The supplied development bundle is `Market-cloudbed-1`; this repository stores its data under `data/track-1`. Runtime accepts its mounted dataset location rather than either basename.
- Discover `telemetry/<date>/trace/trace_span.csv` files. Required trace fields are `timestamp,cmdb_id,span_id,trace_id,duration,type,status_code,operation_name,parent_span`. Header compatibility is validated; field order is not a substitute for field identity. Extra columns may be retained as raw extensions if required fields remain unambiguous; missing/duplicate required fields or changed meanings require explicit incompatibility.
- `query.csv` supplies public instructions/task types, while `dev/query_dev.csv` adds answers. The local public header is `row_id,task_index,instruction`; the data guide's abbreviated example names only task index and instruction. Preserve actual case IDs from the runner contract rather than manufacturing IDs by row position.
- Logical source record numbering includes the header as record 1 and starts data at record 2, matching the trace audit and research index. Embedded newlines do not increment the logical record counter; optional physical line locators are separate.
- Trace timestamps are milliseconds since epoch; metric/log timestamps are seconds. UTC+8 applies to prompt clock times and answer interpretation. This does not establish units for `duration` or clock synchronization across components.
- Raw `cmdb_id` identifies a recording entity. Names can contain topology clues, but suffix stripping or an operation name does not establish a particular target replica. Component identities for exact-match downstream answers must come from the mounted data and justified relationship mapping.

### Scoring consequences for the extraction boundary

| Official requirement | Extraction consequence | Downstream owner |
|---|---|---|
| Different deployment and unfamiliar components | Discover source dates/identities; test renaming and cache isolation. | Extraction plus integration |
| Exact failure count and requested task projection | Preserve public scope and all case associations; never equate incident count with selected trace count. | Diagnosis/answer formatting |
| Exact component/reason strings | Preserve raw component identity; invent no fault reason from a status or child operation. | Diagnosis/vocabulary mapping |
| UTC+8, 60-second answer tolerance | Correct unit/timezone conversion and precision qualifications; no fabricated exact fault time. | Onset inference and formatter |
| Best guess plus honest explanation | Return explicit missing/unsupported evidence; do not change extraction uncertainty into blank prediction policy. | Diagnoser under ADR 0008 |
| Cost and elapsed time matter | Charge cold preparation, validation and reuse to the run; no hidden developer index. | Extraction receipts plus runner accounting |
| Evidence and explanation | Source-linked facts, coverage, exclusions and ambiguous relationships must survive compaction. | Extraction plus evidence writer |

The data guide recommends chronological incidents; the scoring guide says the evaluator tries permutations. A chronological downstream representation remains valid, but retrieval order and trace ordering are not incident ordering. Fixed answer key order and best-guess behavior remain in existing downstream specifications.

## Observed evidence and discrepancies

The [trace audit](../../docs/research/track-1-trace-audit.md) records 3,059,987 adjacent timestamp decreases in the March 20 file. One 37-span example is distributed across logical records 3–1,203,024. The guide's advice to filter the window first therefore means bounded candidate selection, not stopping a scan at an out-of-range row or discarding out-of-window records belonging to selected traces.

The guide lists 27 operations and four statuses as illustrative daily counts; the inspected March 20 source has 29 raw operations and eight statuses. Blank type, zero duration, textual `OK`/`Ok`, numeric strings, and same-emitter parent relations are real observations. None is a sufficient error, retry, network-delay, or target-binding rule.

The audit's timing consistency evidence favors microsecond duration units, but lacks authoritative exporter metadata for every producer/day. Preserve raw duration and a versioned provisional interpretation. Integer endpoint arithmetic avoids float loss while retaining millisecond start precision; it does not justify sub-millisecond causal ordering. A child outside a zero-duration parent's interval does not itself invalidate the recorded parent link.

## Prior experiment: evidence, not production certification

The [executed protocol](../../docs/research/experiments/short-window-baselining.md) and [local final report](../../data/experiments/short-window-baselining-v1/final-report.md) retain these measured results:

- Two-day source inventory: 18,160,322 records; 9,132,857 on March 20 and 9,027,465 on March 21. These counts and hashes identify a development snapshot, not the expected size of another deployment.
- Core study: 360 policy-anchor cells, 180,850 recovered frontend observations, 75 recorded closure failures, source-linked memberships, and 200 verified source-pointer samples. Synthetic and natural controls each passed 216 intervention-policy cells; the package suite passed 34 tests.
- Frozen C1 pooled five-minute replay: 57 windows, 342 slices, 98.89% primary request support. The worst window is only 54.19% supported; 449 comparisons in another window fail the reference-median uncertainty screen. Support does not establish health: another supported cohort has an approximately 60-second median.
- Research index preparation took 321.956 seconds and produced a 13,441,196,032-byte index; core execution took 901.386 seconds and replay 516.984 seconds on the development machine. These do not establish fit on the judging machine, cold-start budget, peak-memory limit, or unseen deployment.
- The development inventory's 70 prompt rows/57 windows and five connected exposure groups are exploratory context. Do not copy them into production invariants or describe them as independent held-out validation.

## Reuse assessment and required changes

| Candidate | Reusable evidence/behavior | Required feature-specific work |
|---|---|---|
| [Research index](../../experiments/short_window_baselining_v1/index.py) | Full-file CSV ingestion, source hashes/counts, preserved raw fields, source locators, time/trace access. | Replace fixed expected days and developer defaults with a declared deployment snapshot; prove safe interrupted-build publication, invalid-field accounting, schema compatibility, and cold/warm budgets. |
| [Observation reconstruction](../../experiments/short_window_baselining_v1/observations.py) | Composite trace/span identities, graph checks, raw recording bindings, root/direct-child facts, integer endpoint derivation. | Add snapshot/deployment scope; separate timing validity from structure/identity quality; retain arbitrary selected executions and explicit bounded coverage. Existing combined unresolved flags are not the desired final contract. |
| [Research runner](../../experiments/short_window_baselining_v1/runner.py) | Frozen memberships, reference completion exclusions, separate structural channel, source-linked artifacts. | Keep reference windows, C0/C1/C2 choices, pooling, support thresholds and scores in the comparison consumer. Do not embed the selected five-minute policy inside extraction. |
| [Runner input boundary](../../rca/inputs.py) | Caller-supplied locations, CSV parsing, original query IDs, guarded output location. | Integrate extraction without weakening answer isolation, case associations, read-only supplied inputs, or resource accounting. |

No source adapter, parser, extractor, or scorer was executed or changed by this documentation task. Existing research results remain under their original source and code identities. A later implementation must satisfy [T01–T16](acceptance.md), then separately demonstrate integration; it cannot inherit acceptance merely from this table.
