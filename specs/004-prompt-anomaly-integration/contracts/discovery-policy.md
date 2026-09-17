# Initial deterministic discovery policy

**Version**: `track1-discovery-v1`, design only. These are project defaults for
R3–R6, not requirements or calibrated detectors supplied by the official docs.
Changing a rule changes the policy identity and invalidates derived caches.
Promotion requires the feature acceptance matrix, including renamed inventories,
isolated spikes, multiplicity changes and missing-reference fixtures.

## Trace observation and reference membership

An observation is a resolved recorded frontend root and its recovered execution,
identified by snapshot/deployment/trace/root-span. Discover frontend recording
identities from the current trace inventory: the initial shop adapter recognizes
`frontend` and `frontend-<decimal replica number>`, with blank `parent_span` as
the root convention. This is an explicit service-role naming assumption, not a
fixed replica allowlist. Preserve its qualification. Unknown names or ambiguous
roots remain available as generic trace evidence but cannot be silently assigned
the frontend role. A different service-role naming scheme needs a versioned
adapter rule and fixtures, not guessed substring matching.

Query root starts lie in `[window_start, window_end)`. Reference root starts lie
in `[window_start - 5 minutes, window_start)`. Recover available records across
the declared snapshot. Reference eligibility requires complete recorded recovery
and every required interpreted endpoint strictly before window_start under
feature 005; unknown/conflicted timing is excluded with a reason. Preserve
provisional duration-unit qualifications. Query traces may finish after window_end.

Conditional duration context is raw root operation/type plus the sorted unique
set of direct-child `(operation_name, type)` pairs (C1). Multiplicity is deliberately
excluded from that conditioning key and retained separately. Pool only observed
frontend replicas with the same context in the same deployment/snapshot; replica
equivalence is unverified and qualified. Require 20 eligible logical reference
observations, without inflating support from duplicate source rows. Compare each
valid query-root duration to the reference median. Positive signed excess is a
duration candidate; retain nonpositive findings without claiming normality.

The structural channel retains each root's direct-child multiset, including
counts. Compare against the distinct resolved reference multisets for the same
root operation/type, independently of the C1 latency match. A query multiset not
present in a nonempty resolved reference set is an unmatched-structure candidate;
report added/removed pairs and count differences against each retained reference
shape, with shape frequencies and any truncation. With no resolved reference,
structure comparison is unavailable. Unknown structure is unknown, never novelty.

## Metric observations and candidates

Support long-format container/node/mesh/runtime rows and wide service rows from
the official schema. Treat each service field `rr`, `sr`, `mrt`, `count` as a
separate recorded KPI; do not invent its unit or infer success/error meaning from
its abbreviation. Preserve source-family identity. A context is deployment,
source family, exact resource identity, KPI and declared unit/conversion identity.
Unknown units remain explicitly raw/unknown and cannot be pooled across contexts.

One observation is one valid recorded sample, not a window average. Historical
samples use the same five-minute interval; query samples use the 30-minute scope.
Require 20 valid nonconflicting logical reference samples and preserve counts,
time coverage, gaps and exclusions. Duplicate rows do not increase support;
conflicting values at the same context/timestamp are retained as ambiguity and
excluded from numerical comparison. Compare every inspected query sample to the
reference median; every nonzero signed difference is a descriptive candidate,
with both directions retained. This deliberately has no statistical alarm
threshold or fault-sensitivity claim. Zero differences remain findings.

Constant/zero references support only qualified raw absolute differences. Do not
divide by zero, standardize by zero spread, interpolate missing samples or infer
rates from cumulative counters. Unknown counter semantics, units, history health
and workload comparability remain qualifications; malformed/nonfinite values or
insufficient support yield unavailable numerical comparisons. No observed change
is automatically a labelled failure, and sampled onset is not injected fault time.

## Ordering, packets and coverage

Scan eligible source records in bounded batches with deadline checks; never stop
at an out-of-window row in an unsorted file. Within a completed context, order
duration candidates by descending positive excess, metric candidates by descending
absolute difference, then timestamp and stable source identity. Structural
candidates sort by timestamp and identity. Keep channels separate; report ties.
No cross-KPI/unit score fusion or failure-count-based pruning is permitted.

Initial source selection is deterministic: root start/trace/root-span for traces,
source-family/resource/KPI/unit for metric series, timestamp/source locator for
logs. Response pages contain at most 30 recovered traces, 50 metric series or 200
targeted log records. These are response limits, not a claim that the first page
exhausts the scope. Explicit continuation and withheld counts accompany a bounded
selection; unknown withheld counts must be marked unknown. Trace pages expose a
nonnegative `offset` into the stable root-start/trace-ID order, `returned_count`,
`selected_count` for the complete selection, `withheld_count` after this page,
and `next_offset` (`null` when exhausted). Offsets apply only to the same immutable
source snapshot and selection arguments. The discovery executor journals each
page and compares completed pages before requesting the next, preserving those
comparisons if a later page exhausts the budget. If required discovery
cannot consume remaining pages within its work budget, report partial coverage.

Metric comparisons use all inspected samples, before display reduction. For a
series of n time/source-sorted query samples, display all when n <= 120; otherwise
display indices `floor(i * (n - 1) / 119)` for i=0..119. Candidate records retain
their exact sample value, timestamp and locator even if omitted from the display
sample. Sampling therefore cannot silently remove an isolated candidate spike.
Raw indexed observations remain addressable. Packet limits do not redefine the
20-sample reference support criterion or certify complete retrieval.

## Replay and acceptance

Completed discovery reproduces findings under identical input, policy and work
limits. Live wall-clock stops may change coverage. Journal last completed batches,
continuations and stop decisions; replay partial work with those boundaries or a
controlled clock. Never reuse partial results as a completed case. Validate
deterministic selection, candidate retention and provenance independently from
runtime fit and diagnostic accuracy. The official docs provide no evidence that
these project defaults diagnose faults effectively.
