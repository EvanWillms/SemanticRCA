# Data model: Qualified short-window baselines

This is the planned implementation model for [spec.md](spec.md), governed by [baseline.md](contracts/baseline.md). Python values are immutable dataclasses with tuple-based collections at the pure boundary; JSON artifacts use explicit schema versions. Missing/unavailable values carry reasons, never fabricated zeros.

## Identity and source evidence

| Entity | Required fields and relationships | Validation |
| --- | --- | --- |
| SourceSnapshot | snapshot_id, deployment, sources, parser_version, extraction_version, completion state | Sources identify dataset-relative path, SHA-256, schema/header, logical record count and known unavailable partitions. Absolute mount paths are resolver configuration, not identity. |
| SourceLocator | snapshot_id, source_id/digest, representation, record selector, field selector | CSV selector uses one-based logical record with header=1; JSON selector uses an actual document/array-member path. Resolve within the declared dataset, never arbitrary paths. |
| ObservationIdentity | snapshot_id, deployment, trace_id, root_span_id | Original IDs remain strings. Trace scope is deployment; span scope is trace. An unresolved root identity stays in a raw-outcome record, not an invented request ID. |
| Measurement | raw_text, raw_unit, normalized_ms, normalization_id, availability/reasons, source locator | Finite nonnegative duration for numerical use. Original timestamp text and exact parsed start/end values are retained separately from normalized binary64 statistics. |
| RecordedRequest | observation_id, root operation/type, exact component, start_ms, measurement, child occurrences, C0/C1/C2 keys, identity/structure/completion states, all source locators | Blank-parent root and allowlist membership are explicit. C1 is unavailable for unknown structure. C2 counts retain multiplicity. |
| RetrievalReceipt | source inventory ID, selected/resolved/unresolved counts, scanned/recovered records, missing sources, cursors, completed batches, status/reason, timings | Complete means exhausted declared available source selection/recovery, not complete instrumentation. Partial counts cannot be relabeled complete. |

Identical duplicate records for the same scoped span identity collapse into one logical observation while all locators and duplicate counts remain. Different content at the same identity is a conflict; affected execution identity/structure/completion becomes unresolved as appropriate. This declared `logical-span-dedup-v1` policy must not inflate support and has its own extraction version. Compare against research membership explicitly because the study may conservatively reject duplicates instead.

## Reference entities

| Entity | Required fields and relationships | Validation |
| --- | --- | --- |
| BaselinePolicy | policy_id/version, allowlist, context C1, pooled deployment scope, lookback_ms, horizon/slice_ms, support settings, estimator/normalization IDs, no-fallback flag | Initial values: 300000 ms lookback and slice; 1800000 ms horizon; n≥20, ≥3 occupied absolute-minute bins, largest bin≤n/2; seed 42 and 200 replicates. Changed settings require a new policy identity. |
| BaselineSet | set_id, snapshot_id, deployment, anchor_ms, policy, extraction version, baseline IDs, structural population IDs, publication state | Immutable once completed. Identity includes source/policy/extraction/estimator meanings and membership; timings and output directory are excluded. |
| ReferenceCohort | cohort_id, set_id, C1 key, member IDs, candidate/exclusion references | Members start in `[T−300000,T)` and all recovered execution endpoints are strictly before T. Unknown identity/structure/timing cannot enter duration membership. |
| FrozenBaseline | baseline_id, cohort_id, membership_hash, statistics, support, stability, qualifications, evidence references | Hash sorted scoped member IDs for membership; full baseline ID additionally covers snapshot, normalization, policies and derived definition versions. The catalog is derived from reference candidates only; query-only contexts use MissingContext outcomes rather than catalog entries. |
| SupportAssessment | status, n, occupied/minimum bins, largest-bin count/fraction, all failure reasons | Tests are independent; do not stop after first failing rule. Unsupported audit summaries are distinct from eligible median fields. |
| CenterStability | state, block keys, seed/RNG/runtime version, draw indexes, replicate medians, usable/failed counts, p05/p95/full width, relative width availability | Finite nonnegative reference values only. Unsupported cohorts have not_assessed with reason. Supported zero-center has inapplicable relative width; otherwise <190 usable is inconclusive; ≥190 uses width≤0.40×median. Preserve replicate counts even when relative width is inapplicable. |
| BaselineStatistics | count, median/q1/q3/raw MAD, first/last/gap, per-minute/per-replica counts, half-window centers, leave-one-minute-out values | Each statistic has definition and member/subset references. Empty subsets return unavailable with reason. No rounding before decisions. |
| Exclusion | scoped observation or raw record ID, stage, reason codes, known duration/end values, locators | Reasons can overlap; retain deduplicated excluded totals. Completion-excluded duration summaries reference their own population. |

Canonical context keys encode operation/type strings as structured tuples/arrays, not delimiter concatenation. C0 is root operation/type; C1 adds sorted unique child pairs; C2 adds sorted positive multiplicities. Known empty maps encode `[]`; unknown encodes an explicit state with null context, never `[]`.

## Parallel structural populations

`StructuralPopulation` contains set_id, C0 key, candidate IDs, common time/completion-eligible IDs, known_structure_count, unknown_structure_count, eligibility-unknown/excluded counts, pattern IDs and full provenance. All counts are local to this C0 key.

A `StructuralPattern` is an exact sorted multiset with pattern_id, member IDs, count, known denominator and frequency. Known empty is a valid pattern. Sum of pattern counts equals known_structure_count. Unknown structure never contributes to that denominator.

Common time/completion eligibility is assessed before structural knowledge. If an observation's completion is unresolved, it belongs to excluded/eligibility-unknown counts, not the eligible unknown-structure count. Retain raw C0-candidate unknown counts too, so exclusion cannot conceal retrieval gaps. Structural frequencies describe eligible known records; the duration n≥20/time-concentration screen is not applied as a structural-frequency gate.

## Query assignment and coverage

`MissingContext` is an immutable lookup outcome derived from baseline-set ID, requested context and lookup kind (`C1_duration` or `C0_structure`). It carries `unavailable`, a missing-context reason and a deterministic outcome ID. It is not a new catalog member and never changes the frozen set ID. A missing C0 lookup has an empty known population and unavailable frequency, with the completed selection receipt as evidence that no matching reference context was recorded; partial selection instead carries unresolved-coverage reasons.

The frozen catalogs depend only on reference candidates and policy, never on query contents or future slices. Assignments can link either to a catalog object or to a typed MissingContext outcome. This preserves the same set identity when a previously unseen C1 or C0 arrives late in the horizon.

`QueryAssignment` contains occurrence_id, observation_id, set_id, slice_index (0…5), C1 baseline outcome reference, C0 population reference, qualification/reasons and duration-comparison eligibility. Eligibility is qualified only when the query measurement/context and matching supported baseline are compatible. Supported instability remains qualified.

Occurrence identity includes baseline-set identity and slice index; observation identity does not. A query belongs to one slice by root start within a set. Overlapping sets may repeat an observation, so an aggregate retains both unique-observation and occurrence counts.

`CoverageStatement` includes resolved query denominator, supported/unavailable assignments, unresolved raw identities, unknown structures, out-of-scope/duplicate/conflict records, class incidences and per-anchor/slice/replica/C0/C2 breakdowns. Empty denominators have null ratio and a reason. Inspection coverage and comparison support are separate: partial selection with unknown withheld count cannot produce a complete population denominator.

## Lifecycle

1. Source snapshot: discovered → preparing → verified, or failed/partial. Only verified completed preparation can be reused as complete; changed sources create a new snapshot.
2. Baseline set: collecting → evaluating → completed, or partial/failed. Freeze members before evaluating queries. Incomplete affected reference populations produce unavailable outcomes; never certify a sampled prefix as the selected cohort.
3. Cohort: candidate → member or excluded; support then evaluates independently of center stability. Query observations never enter frozen membership.
4. Query assignment: raw selection → resolved occurrence or unresolved raw outcome → qualified/unavailable comparison assignment.
5. New source/policy/normalization/estimator versions create new sets; old objects remain immutable. Reuse after T+30 minutes is unavailable under this profile.

No lifecycle transition sets a baseline to healthy, a comparison to anomalous, or a request to a diagnosed incident.
