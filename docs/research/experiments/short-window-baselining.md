# Short-window like-for-like baselining: exploratory experiment space

Status: **executed and analyzed**, 2026-09-17. All 360 core cells, controlled checks, and the frozen-policy replay over 57 windows are complete. See the [execution report](../../../data/experiments/short-window-baselining-v1/final-report.md) and [decision table](../../../data/experiments/short-window-baselining-v1/decision-table.csv) (local generated artifacts, not source-controlled). The predeclared protocol below is retained. Dataset: `data/track-1` (the requested `data/trace-1` does not exist locally). This is a bounded reference-selection, qualification, and comparison study under [contextual baselining](../contextual-baselining.md) and E1–E3 of the [phase-isolated protocol](../phase-isolated-experimentation.md).

## Decision to make

**For which observed request classes can a recent 5–30 minute reference support a useful duration comparison, how much context must match, and when must the system abstain or use a longer reference?** Include 60 minutes as a longer comparator, not as the definition of short duration.

“Short duration” here describes the reference lookback and comparison horizon, not a filter selecting fast requests. “Like-for-like” means matching on declared observable context, with unknown workload/configuration retained as qualifications. It does not establish identical inputs or verified health.

The output is a scope map: request class × replica policy × minimum supported lookback × supported comparison. A single globally optimal window is not required. A useful answer may be “10–15 minutes for common classes, 30–60 minutes or unavailable for rare classes; median/excess only, no tail claim.” That is an example of the desired answer format, not a finding.

## What the local evidence permits

The [trace audit](../track-1-trace-audit.md) reports 9,132,857 March 20 records, 29 raw operation names, and unsorted, noncontiguous trace storage. March 21 is also present, but the full-day audit findings must not be assumed to apply to it. The trace schema contains operation, recording component, parent relation, timestamp, duration, type, and raw status; it does not contain explicit route, request payload, deployment version, or offered demand.

The [case-25 demonstration](../examples/track-1-case-25-anomaly-discovery.md) found 2,568 frontend reference roots in 30 minutes, nine operation-count signatures across reference and query, and 102 references for one selected signature. All 2,729 query roots passed that demonstration's support rule. This establishes feasibility for one exposed example only. It does not establish coverage for other windows, replicas, or shorter lookbacks. Its reference also contained a 6,746.740 ms request and was not certified healthy.

Start with **frontend root duration**, keeping a parallel record of direct-child structure. This has an inspected precedent and avoids mixing caller/receiver spans or interpreting unknown status semantics. Defer service-span duration, metrics, logs, error rates, cross-service score fusion, seasonality, online adaptation, and RCA accuracy. No LLM is needed for this study.

## Observation and retrieval contract

- One observation is a blank-parent frontend span, identified by `(trace_id, span_id)`, with raw operation and type retained. Freeze the observed frontend component allowlist after the inventory; do not infer arbitrary service equivalence by stripping suffixes.
- Retrieve candidate roots by event time, then recover their recorded traces across both available daily files. Scan complete files or use a validated index; never stop at an out-of-range CSV row. A fixed time buffer alone does not establish trace closure.
- Audit duplicate identities, ambiguous roots/parents, cycles, unresolved ancestry, cross-file boundaries, and direct-child retrieval. Ambiguous observations remain in coverage denominators with a reason; do not silently count duplicated records as requests. Report raw root records and resolved distinct requests separately.
- Build signatures from recorded direct children of the root, using raw `(operation_name, type)` pairs. Preserve component bindings outside the signature. Use an explicit `unknown_structure` state when retrieval is unresolved; an empty recorded child set is a separate, qualified state, not proof of no work.
- Use epoch milliseconds and UTC+8 calendar anchors. Preserve raw duration; conversion to milliseconds uses the provisional microsecond interpretation from the audit. Do not assert sub-millisecond ordering or authoritative producer units.
- Do not filter by latency, interpreted success, benchmark fault label, or future behavior. Raw statuses may be inventoried but cannot define healthy references.

Existing retrieval code in `experiments/frontend_blind_v1` is a reuse candidate, not a validated implementation of this protocol. In particular, validate source hashes, both-day coverage, composite identities, provenance conventions, and retrieval completeness before reuse. Keep this study's configuration and outputs separate from that experiment.

## Core experiment matrix

At anchor `T`, freeze references from `[T − L, T)` and compare roots starting in `[T, T + 5 minutes)`. Exclude reference executions whose recorded root or recovered span endpoints reach or exceed `T`; count these boundary exclusions. This avoids knowingly using unfinished reference executions. Export arrival times are absent, so the study is retrospective event-time replay, not a proof of online availability.

Completion-based exclusion can preferentially remove long executions near `T`. Report that fraction and the excluded duration distribution separately for every lookback; a material boundary effect qualifies the comparison and may rule out a short window. Query roots may complete after their five-minute start interval; recover those records and report unresolved completions rather than truncating their durations.

| Factor | Values | Question |
| --- | --- | --- |
| Reference lookback `L` | 5, 10, 15, 30, 60 minutes | How short can the reference be before support or stability fails? |
| Context `C0` | Root operation + raw type | Broad comparison control; how much variation is mixed together? |
| Context `C1` | C0 + set of direct-child operation/type pairs | Does observed operation presence help without requiring exact multiplicity? |
| Context `C2` | C0 + multiset of direct-child operation/type pairs, including counts | Does stricter observed-shape matching help enough to justify fragmentation? |
| Replica policy | Same frontend `cmdb_id`; pooled explicit frontend allowlist | Does pooling increase support while introducing between-replica differences? |

This is **5 × 3 × 2 = 30 policies**. Pooling is always qualified because deployment, input balance, and capacity equivalence are unverified. C1 and C2 are conditional comparisons on observed behavior, not independently known request types. C1 can hide added/removed operation types; C2 can additionally hide changed call counts.

For every policy, retain a structural comparison over C0: observed child sets/counts, reference frequencies, novel signatures, and unknown retrieval state. An unmatched C1/C2 request remains visible in this channel. Do not give it a zero anomaly score or route it silently to a broader latency cohort.

Use twelve predeclared exploratory anchors: **01:00, 05:00, 09:00, 13:00, 17:00, and 21:00 UTC+8 on each of March 20 and March 21**. These give separated 90-minute maximum supports, `[T − 60 minutes, T + 30 minutes)`, without choosing times from fault answers. Verify actual data availability; retain missing anchors as unavailable rather than replacing them with favorable times. Evaluate all observed frontend classes at every anchor.

The core produces **360 policy–anchor evaluations**, each with per-cohort rows. Evaluate each frozen reference against six consecutive five-minute slices through `T + 30 minutes` as a secondary aging check. No reference refresh occurs during those slices; the first slice is the primary result. This adds comparison rows, not independently selected baselines or independent experimental replicates.

Case 25 may be reproduced separately as an exposed sanity check; it is not a thirteenth independent validation anchor. All twelve anchors are exploratory, including known exposed periods. Do not label them held out.

## Qualification and measurements

Begin with a **provisional support rule**, identical for all core policies:

- At least 20 resolved reference requests.
- At least `max(3, ceil(L / 2))` occupied one-minute bins across the lookback.
- No one minute contributes more than half the cohort's reference requests.
- No unresolved identity or retrieval ambiguity in observations used to compute a shape-conditioned reference. Keep excluded and unmatched observations visible in coverage.

These are testable exploration settings, not statistical guarantees. Record sensitivity to minimum counts of 50 and 100 from the same summaries; do not multiply these into another detector search. Occupied bins measure observation support, not collector uptime or independent samples. Support failures produce **unavailable** comparisons; supported empirical references remain **qualified** because health and relevant context are unverified.

Retain `n`, occupied minutes, first/last observation, largest inter-observation gap, concentration by minute/replica, excluded counts, median, quartiles, and MAD. Emit observed duration, signed absolute excess, ratio when the median is positive, and standardized departure when MAD is positive. Zero MAD does not invalidate a median comparison; it makes that standardized score unavailable. A zero median leaves the ratio unavailable. Do not promote a tiny absolute difference to high priority solely because its relative score is large.

| Measurement | Definition and purpose |
| --- | --- |
| Request coverage | Supported query requests / all resolved query requests, with raw-record and unresolved-identity counts alongside it. Report per anchor, class, and replica as well as volume-weighted totals. |
| Class coverage | Supported observed query cohorts / all observed query cohorts under that policy. Also report by C0 and C2 strata so changing the key cannot manufacture better coverage. |
| Fragmentation | Cohort counts, sample-count distribution, singleton/rare cohorts, unmatched fraction, and unknown-structure fraction. |
| Center uncertainty | Resample one-minute time blocks of the reference, 200 replicates, seed 42; report the median's 5th–95th percentile interval and failed/empty replicates. These are exploratory intervals, not calibrated guarantees with few blocks. |
| Temporal sensitivity | Compare centers from the earlier/later halves, leave-one-minute-out centers, and adjacent lookbacks. Report signed changes; drift is evidence to qualify, not a reason to trim inconvenient observations. |
| Pooling sensitivity | Compare pooled and same-replica centers/coverage for the same query observations; display replica contributions. A pooled median can conceal a minority replica's shift. |
| Reference aging | Coverage and differences by five-minute offset through 30 minutes. Changes may reflect query behavior as well as reference aging; natural telemetry alone cannot distinguish those causes. |
| Review sensitivity | Within each policy/anchor, rank positive absolute excess and inspect top 5, tying by trace/span ID. Report overlap on common supported observations and on the full query population separately. No overlap score is a correctness label. |
| Cost | Rows scanned/retrieved, trace closure failures, elapsed time, index/artifact bytes, and reproducible membership hashes. |

Do not claim p95/p99 reliability from these small cohorts. Tail estimation requires a separately scoped support and uncertainty study. Natural query-window differences and top-five churn are descriptive observations, not false positives; the dataset supplies no independently verified healthy controls for this study.

## Controlled checks: can matching conceal the thing we want to see?

Run these on copied observations, with source-linked originals preserved and an explicit intervention manifest. Independently specify expected facts before running the selector/comparator. These are contract checks, not simulated evidence of real faults.

| Intervention | Required result |
| --- | --- |
| Reorder records and consistently rename trace/span IDs | Same memberships and numerical comparisons after mapping IDs back; provenance remains resolvable. |
| Increase query duration by 25%, 50%, and 100%, holding declared context fixed | Membership unchanged; absolute excess increases by exactly the planted amount, within raw-unit rounding. Changes in score are not causal diagnoses. |
| Add/remove a direct child; separately change multiplicity only | C0 structural channel preserves the exact change. C1/C2 rematching or nonmatching is reported explicitly; no request disappears. |
| Thin references to 10, 20, 50, and 100 observations, where available; separately concentrate them in one minute | Support decisions follow count and time rules independently. Repeat thinning with seeds 1–5; insufficient original support stays unavailable. |
| Set reference durations constant, then set them to zero | Median/excess remain inspectable; unavailable MAD/ratio are explicit, with no infinite scores. |
| Shift 10%, 30%, and 60% of reference durations by 2×, selecting membership with seed 42 | Quantify contamination-induced center/score changes, including comparisons lost or weakened. Never certify the altered reference as healthy. |
| Shift one replica, then all replicas, in copied query observations | Preserve historical departures and pooling qualifications. Agreement among shifted replicas cannot erase the historical comparison. |
| Remove recorded children and mark retrieval incomplete | Emit unknown structure, distinct from a known recorded structural change. Natural missing instrumentation may remain indistinguishable and must be qualified. |

Require zero silent losses, invented matches, incorrect deterministic differences, or incorrect undefined-value handling on these checks before selecting a scope. A passing fixture suite establishes the contracted behavior only, not benchmark incident sensitivity.

## Selection rule and staged expansion

Use the following **proposed screening gates**, declared before execution. They express a research preference for coverage and stable centers; they are not universal quality thresholds:

1. Pass the controlled contract checks.
2. At least 90% request coverage overall and at least 80% in at least 10 of the 12 primary five-minute windows. Missing windows count against this gate. Report rare-class and per-replica failures even if aggregate gates pass.
3. For at least 80% of supported query observations with positive reference medians, the block-resampled interval's full width is no more than 40% of that median. Report the zero-median population separately; do not silently remove it from the scope statement. Require at least 190 usable bootstrap replicates per assessed cohort, otherwise mark this check inconclusive.
4. Report temporal and pooling sensitivity alongside these gates. An independent review must narrow or qualify a scope showing material regime/replica differences; passing coverage and interval-width gates alone cannot establish context compatibility.

First identify the coverage–uncertainty–context tradeoff across all 30 policies. Within each declared request class, prefer the **shortest passing lookback**; at the same lookback prefer same-replica over pooled if both pass. Choose between C0/C1/C2 using the observed fragmentation, mixture, and structural-change results, documenting why added conditioning is useful. Do not choose by largest anomaly score or later RCA accuracy. C0 remains a broad qualified control when workload equivalence cannot be supported.

If no 5–30 minute policy passes, say so. A passing 60-minute policy supports a longer reference, not a claim that short baselining worked. If no policy passes, retain descriptive durations and structural observations without a supported latency comparison. Do not silently expand history or lower gates. A revised exploration gets a new version.

For a concrete first implementation slice, start with **C1, same replica, 15-minute history, five-minute query, median and absolute excess**, plus C0 structural reporting; then run the full matrix before choosing defaults. This is a starting hypothesis, not the recommendation this experiment is intended to establish.

After selection, freeze one primary policy and at most one explicitly qualified fallback. Replay the label-free inventory of **57 distinct supplied 30-minute query windows**, grouping duplicate prompt rows and accounting for shared reference/query telemetry. Keep references frozen at each window start and report all six slices. This is descriptive confirmation over the benchmark windows, not automatically held-out validation: reconcile all prior exposure records, including `specs/001-candidate-recall-experiment/development-exposures.json`, and record this study's exposures. Overlapping support intervals must stay together or be purged for any later independent split. If that leaves too few independent groups, report the limitation.

Only afterward consider a separate service-operation study, with explicit recording-role/operation compatibility. Contemporaneous peers, guard gaps, additional workload proxies, and adaptive baselines are subsequent factors, not extra dimensions of this first sweep. Root-cause labels and `scoring_points` remain outside selection and comparison; any later diagnostic evaluation is a separate experiment.

## Deliverables and completion

Store generated artifacts under `data/experiments/short-window-baselining-v1/`, outside source documentation:

- A frozen manifest: source hashes, explicit anchors and intervals, component allowlist, matching rules, support gates, seeds, exclusions, provisional units, code version, and exposure ledger.
- Request/cohort reference membership with source pointers; per-policy/per-anchor coverage, uncertainty, structure, and cost tables; controlled-check results.
- A decision table with `request class`, `replica policy`, `lookback`, `supported statistic`, `coverage`, `qualifications`, and `unavailable reason`.
- A short report showing the full matrix, failure cases, selected scope or inconclusive result, and the exact claim permitted next. Keep raw telemetry out of the report and source commits.

Completion means the scoped matrix and checks are accounted for, failed/unavailable cells remain visible, and the scope decision follows the declared rules. It does not require finding a successful short baseline.

Governance: the initial definition was documentation-only. Subsequent explicit user authorization expanded this standalone research scope to implementation, execution, and analysis using Luna extra-high subagents with parent code review. It does not implement a production feature or expand the existing frontend blind trial. The full Spec Kit implementation sequence, model-routing evaluation, and submission packaging remain deferred for production integration. Follow-up owner: project maintainer, to create a separate feature specification before integrating a selected policy into the unattended agent. No benchmark labels or scoring points were used for this study.
