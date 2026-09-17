> Deferred integration experiment. Superseded as the first experiment by [the assertion plan](plan.md). Its thresholds and implementation sequence are historical proposals, not active requirements.

# Experiment 001: Does symbolic fusion improve root-cause candidate recall?

**Branch**: `001-candidate-recall-experiment` | **Date**: 2026-09-17 | **Status**: Trace assumptions audited; experiment not executed
**Specification**: [spec.md](spec.md)
**Source hypothesis**: [HFCE proposal](../../docs/research/MantisGrid_HFCE_Multimodal_Symbolic_RCA.v1.md)

## Summary

The full project diagnoses dataset-designated fault events, represented by start
time, root-cause component, and fault reason, with supporting evidence. Experiment
001 tests only whether the correct component reaches the shortlist; it neither
decides whether a reliability requirement was violated nor completes the full
diagnosis contract. See [ADR 0001](../../docs/adr/0001-benchmark-failure-definition.md).

Test whether simple symbolic metric transitions plus trace-edge transitions place the true root component in the top three more often than the supplied metric heuristic. Use no LLM and no logs. Freeze a grouped holdout before tuning, retain a fair metric control, and report paired incident-level outcomes. The experiment is a decision about candidate selection, not a submission-quality RCA agent or proof of causality.

**Primary contrast**: symbolic metrics + traces versus harmonized metric heuristic, measured by macro incident-level component recall@3.
**Mechanism contrast**: symbolic metrics + traces versus symbolic metrics alone.
**Attribution control**: numerical metrics + traces using the same features and fusion, without symbolic quantization.

## Technical Context

- **Language/runtime**: Python 3.11 or newer; lock the actual version at implementation.
- **Dependencies**: Standard-library CSV/JSON/time tools plus the starter's NumPy/pandas stack; no new service or model dependency is needed.
- **Storage**: Organizer CSVs remain external; bounded reads and local aggregate caches; JSONL/CSV reports. Cache keys include data, clock policy, preprocessing, and configuration hashes.
- **Testing**: Small synthetic fixtures for clock conversion, grouping, labels, ranking, partial-order trace handling, and missing modalities; a development-only real-data smoke run.
- **Platform**: Local macOS development; portable unattended CLI suitable for later Linux/container use.
- **Performance budget**: Target under 4 GiB peak working memory and under 60 seconds warm processing per incident. Record cold ingestion separately. These are engineering targets, not measured performance; baseline reproduction may exceed them and must report it.
- **Scale**: Actual label-free inventory confirms 70 query rows across two telemetry days and 57 distinct query windows (44 appear once; 13 appear twice). Distinct windows are not yet verified independent incident groups; gold completeness remains unaudited.
- **Data readiness update**: Extracted data are now available at `data/track-1` (18 CSVs, 11,936,975,544 bytes). The March 20 trace file passed a full 9,132,857-record schema scan. The earlier incomplete-archive observation is historical, not a current blocker. Other files have not received full integrity scans. See the [trace audit](../../docs/research/track-1-trace-audit.md).

## Constitution Check

Pre-design and post-design review: evidence, bounded retrieval, reproducibility, and unattended artifact contracts are covered. The following scope exceptions apply to this representation-only experiment:

| Deferred requirement | Reason and impact | Follow-up / owner |
|---|---|---|
| Routed versus single-model evaluation | This experiment makes no model calls; routing cannot explain candidate selection gains | Maintainer: schedule experiment 002 only after the candidate gate |
| Full time/component/reason submission and Dockerfile | Candidate recall isolates one mechanism; optional baseline official scoring is a sanity check | Maintainer: add final-agent adapter, container and submission validation before any judged release |

These are documented experimental-scope exceptions, not changes to the constitution or claims that the final deliverable is complete. Continue through `speckit-tasks` before implementation. The goal clarification is synchronized with constitution version 1.0.1.

## 1. Hypotheses and boundaries

- **H1**: Symbolic fusion improves held-out recall@3 over the fair metric baseline.
- **H2**: Traces add recall beyond symbolic metrics, especially for network faults.
- **H3, exploratory**: Discrete behavior retains or improves recall relative to matched numerical fusion while producing smaller inspectable evidence.

Do not claim network benefit without reason labels, symbolic benefit from beating metrics alone, cost savings without a matched downstream experiment, or unseen-deployment transfer from a within-deployment split. Onset accuracy is secondary. Reason classification is outside experiment 001.

## 2. Data readiness and clock audit

1. Validate the extracted organizer manifest, expected files, and query CSV with a real CSV reader; archive validation is needed only if extracting again. Never fetch the original upstream dataset containing hidden evaluation answers.
2. Record bundle hashes, official repository revision, query count, distinct windows, fault counts, label fields, and modality coverage. Do not hard-code 70 into the evaluator.
3. The March 20 trace begins at epoch-millisecond `1647705600361`, which is local midnight +361 ms in UTC+8, matching the directory date. The first node metric timestamp is the corresponding epoch second `1647705600`. A query starting 09:00 UTC+8 maps to `1647738000` seconds; the starter's UTC interpretation moves it eight hours later. Apply this documented clock convention to B1/treatments and preserve B0 unchanged. Duration is a separate nonnegative integer field: microseconds are strongly supported by the selected trace's sequential timing, but producer metadata has not independently confirmed the unit. Record duration scale and its evidence; do not infer it from the timestamp unit.
4. Store normalized UTC epochs internally and preserve original values plus clock policy. Format answer times as UTC+8. Do not select timezone by whichever gives better held-out recall.
5. Preserve integer epoch milliseconds and raw duration integers; use integer microseconds for interval arithmetic when the microsecond duration interpretation is enabled. Allow for millisecond timestamp quantization and unknown clock synchronization when comparing endpoints. Never silently repair negative gaps or assign sub-millisecond causal order.
6. Verify exact aliases from telemetry. Container IDs such as `node-5.adservice-2` provide a pod and placement; preserve node identity separately. Trace `cmdb_id` identifies the recording component, not necessarily the service named by `operation_name`. Preserve names such as `adservice2-0` as distinct; do not strip arbitrary digits or collapse pods to services. Ambiguous service-to-pod mappings remain ambiguous, not copied onto every pod.

## 3. Evaluation units and frozen split

**Do not randomly split query rows.** Different task types can ask different fields about the same event.

- Parse every query's deployment, window, and stated failure count. Extract available gold fields with scorer-compatible parsing in a separate evaluator process.
- Collapse exact duplicate windows and consistent incident descriptions into one evaluation unit. Union partial labels only when window, count, and event correspondence are unambiguous; retain source rows and reject conflicts. Missing components cannot be inferred from reasons or telemetry.
- Group overlapping windows and shared labelled events into the same split block. Nonidentical windows can remain separate units within that block; average their recall inside the block so densely repeated incidents do not dominate the primary metric.
- Rank once per canonical window using only window and stated count. Task variants may reveal a known component in prose; never expose that prose or any gold fields to the candidate ranker.
- Use a deterministic, seeded group split (`seed=20260917`), targeting two-thirds development and one-third holdout. Balance network-present, non-network-only, and multi-fault groups where possible; assign ties by stable group ID. Publish the manifest before feature inspection or tuning.
- The preparation step may use labels to construct groups and balance the split. Development analysis may inspect only development gold and incident telemetry. Evaluation reads holdout gold only after ranking artifacts are frozen.
- If fewer than six independent holdout blocks fit, report the holdout as exploratory. Do not expand it after observing scores. With too few blocks, a later grouped cross-validation run is descriptive and cannot convert the original result into confirmation.
- No incident may move between splits after failure analysis. If a defect invalidates a run, retain it and version the correction. A holdout inspected for design changes becomes development data for the next experiment.

**Reference telemetry**: B1 and all treatments use same-day reference observations outside the union of all declared query windows, derived without gold labels. This prevents one evaluated incident from becoming another method's background reference. Compute and freeze those statistics once. A series needs at least 20 finite reference observations and positive MAD; otherwise it is unavailable for all matched methods. The data are an offline corpus; reference observations may occur after the incident, so this is not an online-detection claim. If insufficient reference coverage makes comparison impractical, amend this policy using development evidence before the holdout run and record the amendment.

## 4. Comparison arms

| ID | Method | Data / behavior | Purpose |
|---|---|---|---|
| B0 | Supplied heuristic, unchanged | Container + node metrics, native time parsing, rest-of-day median/MAD, maximum absolute robust z | Reproduce organizer floor; not the sole attribution comparator |
| B1 | Harmonized metric heuristic | Same two metric files; audited clock, common reference eligibility and candidate identities; maximum absolute robust z | Fair non-symbolic metric control |
| S1 | Symbolic metrics | Same series as B1; discrete states and persistent episodes | Metric representation contribution |
| S2 | Symbolic metrics + traces | S1 plus edge latency/error episodes and late fusion | Main treatment and trace increment |
| N2 | Numerical metrics + traces | Same aggregates, persistence windows, topology, normalization, and fusion as S2; continuous evidence strengths | Distinguish multimodal information from quantization |

All matched arms produce full rankings of distinct candidate IDs and report fixed top-1/top-3 prefixes. No oracle pruning by gold reason, component, or fault count. Trace-only candidates may enter S2/N2; explicitly report candidate-universe coverage so retrieval expansion is not confused with reordering. Report a common-universe sensitivity analysis restricted to B1-observable candidates. No extra metric files are added to S1/S2 in this experiment.

B0 candidate recall comes from `analyse(...).ranked`, before reason selection, not from the limited answers emitted by `solve()`. The organizer's reported 0.073 is an end-to-end score, not recall@3; measure recall from scratch.

## 5. Minimal representation and fusion

### Metrics

For eligible series, use `z(t) = (x(t) - median_reference) / (1.4826 * MAD_reference)`. B1 retains raw-sample peaks; the treatment aggregates signed z by median into 60-second bins. Record the native cadence, count, and gaps. Do not interpolate across empty bins.

Initial states: `NORMAL` for |z| < 3, `RISE` for 3 <= z < 5, `HIGH` for z >= 5, `DROP` for z <= -3, and `MISSING` for empty/unusable bins. Persistence requires two consecutive observed bins. An isolated |z| >= 5 bin is a `SPIKE`; returning to normal after an episode is `RECOVER`. Retain sign, peak numeric strength, duration, and the first abnormal-bin boundary. Report onset uncertainty from the last normal sample to first abnormal sample; already-abnormal window starts are left-censored.

Start with six states and run-length episodes; defer SAX/SFA, motif libraries, oscillation recognition, approximate string matching, and learned weights. This tests the smallest useful representation, not the full activity-recognition thesis.

For S1, each KPI scores 1 for a persistent HIGH/DROP episode, 0.5 for a persistent RISE or isolated SPIKE, otherwise 0. The component score is the maximum KPI score; this avoids rewarding components with more KPIs. Tie-break by earliest supported onset, then canonical component ID. For N2, use `min(1, |z|/5)` at each bin and the maximum of consecutive-bin minimum strengths or half-strength isolated-bin peaks, aggregated over KPIs by maximum.

### Traces

**Schema contract, grounded in the March 20 file**: Nine CSV columns. Parse `timestamp` and `duration` as integer values, and IDs/status/type/operation/component as strings with explicit empty-string handling. All observed span IDs are 16-character lowercase hex, trace IDs 32-character lowercase hex; preserve leading zeros and use `(trace_id, span_id)` identity. Observed `type` values are `rpc`, `telemetry`, `http`, `db`, and blank. Blank type means unspecified instrumentation type, not a missing row. Blank `parent_span` is the observed no-parent marker. Validate unknown values rather than silently applying this one-day vocabulary to every future deployment.

**Retrieval**: File order is not chronological and traces are not contiguous. Scan the whole relevant file while filtering, or use a validated index; never terminate a scan at the first out-of-window timestamp. A prefix sample cannot establish missing-parent rates or edge frequency. The selected 37-span trace occupies records 3 through 1,203,024. Start with the query window plus a two-minute retrieval buffer, then perform bounded ancestor closure by composite ID, including adjacent day partitions when needed. Do not call a buffered trace complete until all required references resolve; two minutes is an initial retrieval policy, not a demonstrated maximum trace duration. Scoring stays within the query window, and unresolved/ambiguous parents remain explicit.

**Span graph versus service graph**: Retain the original span parent graph. Classify each resolved relation as same-component or cross-component before projecting service dependencies. The inspected trace has 19 same-component and 17 cross-component relations. An apparent client span and its apparent server child can both say `rpc`; `type` is not a reliable client/server role field. Infer roles only from the observed parent relation, emitter identities and compatible operation names, with confidence/provenance. Preserve raw operation names; a separate normalization may remove observed leading `/` or `grpc.` for matching, but must not merge arbitrary case changes or service variants. Database operations such as `HGET` on `cartservice-1` do not supply an observed Redis component identity.

**Features**: Aggregate comparable cross-component interactions by directed emitter pair, normalized operation, raw instrumentation types, and inferred role class; keep same-component relationships for execution context rather than counting them again as network edges. Candidate features are matched-interaction count, receiver duration distribution, caller duration distribution where pairing is supported, and parent-to-child start gap distribution. Start gap includes scheduling, instrumentation and clock effects; it is not measured network transit time. A caller-minus-receiver duration residual is not automatically network delay either. Preserve structural partial order; the four apparent sibling overlaps in the example are only 106–453 microseconds and are below the 1 ms timestamp resolution, so they do not establish concurrency.

**Zero and status handling**: Zero duration is observed (four spans in the example, including HTTP and database operations); retain it with a quality flag and do not equate it with missing work, instantaneous execution, or a failed operation. Avoid interval-containment/exclusive-time claims for zero/coarsely quantized durations. Preserve status strings exactly: the day contains `0`, `1`, `4`, `13`, `14`, `200`, `OK`, and `Ok`, including `13` on `http` spans. Neither numeric conversion nor a global nonzero-error rule is valid. Error-fraction features stay disabled until an instrumentation-specific mapping is independently established. Raw status-category transitions may be inspected without calling them errors.

**Eligibility**: The proposed minimum of five matched interactions per one-minute bin and 20 reference bins is a development-stage starting policy, not a validated property of the data. Measure coverage only after reconstructing the time-filtered graph; the incomplete first-100,000-row sample cannot establish full-day support. Record insufficient support separately from observed normal behavior. Positive-MAD robust-z features may be scored where valid. For constant baselines, retain counts/zero-duration/status-transition evidence and record `constant_baseline`; do not add an arbitrary epsilon or silently claim there is no signal. Define and freeze any feature-specific alternative on development data before the main experiment, applying it identically in S2 and N2.

Apply the same state/persistence and numerical-strength transforms to supported trace features. Attach ambiguous abnormal interaction evidence to both observed endpoints, retaining direction and provenance; do not assert the callee caused it. Component trace score T is the maximum supported interaction-feature score. Path-onset explanations remain diagnostic only in v1. Relative duration changes can be explored in raw units per homogeneous instrumentation group; absolute-time features require an explicit duration-scale decision. This audit demonstrates parseability and recorded relationships, not a fault or a validated latency detector.

### Late fusion

Let M be the component's metric score and T its trace score in [0,1]. Use `F = 0.5*M + 0.5*T`; unavailable channels contribute zero, with a separate availability flag. If an entire case has no usable trace evidence, S2 equals S1 exactly. Unavailable metrics do not suppress a trace-only candidate. If all scores are zero, emit no supported candidates and score a miss; never fill a shortlist with arbitrary zero-evidence IDs. Tie-break by earliest supported onset, then canonical ID. N2 uses the same formula with its continuous strengths.

No weight search for this first run. Change thresholds or parsers only on development data, preserve configuration history, and freeze the final settings before evaluating holdout. S2's metric fallback and missing-evidence behavior must be tested explicitly.

## 6. Metrics, uncertainty, and decision rule

For eligible unit i, let G_i be its set of known distinct gold components and P_i(k) the first k distinct predictions:

`R_i@k = |G_i intersect P_i(k)| / |G_i|`.

Primary recall is the mean of unit recall inside each independent split block, then the mean across blocks. Also report pooled component recall and per-unit scores. Multiple faults on the same component count once for component retrieval; report fault-event counts separately. Cases without any component gold are excluded from component recall with an explicit denominator. Incomplete gold sets are reported separately and do not qualify for the primary decision.

Required report:

- Recall@1 and recall@3 for all arms; complete-gold all-root coverage@3, including the ceiling if a window has more than three distinct roots.
- S2−B1, S1−B1, S2−S1, and S2−N2 paired deltas; incident wins/ties/losses and IDs.
- Network recall using roots linked unambiguously to one of: container network latency, packet corruption, packet retransmission, or container packet loss. Report non-network roots separately; unknown reasons are not non-network.
- Candidate-universe gold coverage and common-universe sensitivity; node/pod and multi-fault breakdowns.
- Descriptive 95% paired bootstrap intervals by resampling whole split blocks (10,000 replicates, seed 20260917). Show raw counts prominently; small-sample intervals do not establish generalization.
- Optional exact paired sign test on non-tied block differences, explicitly exploratory; no significance fishing across arms/subsets.
- Conditional onset absolute error on correctly retrieved components with time labels, plus joint component+onset within 60 seconds recall over all eligible roots. Missing estimates count as joint misses. Match repeated events one-to-one and report left-censored estimates separately.
- Cold ingestion and warm runtime, peak RSS, bytes/rows scanned versus retained, evidence UTF-8 bytes, episode counts, and channel availability. Model calls/tokens/API spend are exactly zero; do not call this a measured LLM cost saving.

**Predeclared practical gate** (thresholds are proposed engineering decisions):

- **Continue fusion provisionally** if S2−B1 recall@3 >= 0.10, S2−S1 > 0, at least two more winning than losing independent holdout blocks versus B1, at least six eligible complete-gold holdout blocks, and no greater than 0.10 non-network recall@3 regression versus B1 where that subset has at least three blocks. An inadequately covered guard is inconclusive, not passed. A bootstrap interval spanning zero limits the claim to a promising pilot.
- **Support the network mechanism provisionally** only if S2 beats S1 on network recall@3, with at least three independent network-bearing holdout blocks and two network-block wins. Otherwise leave H2 unresolved or unsupported.
- **Support symbolic superiority only** if S2 also beats N2. If they tie, only claim evidence organization/representation feasibility, and quantify evidence size; compression effectiveness needs a matched downstream study.
- **Stop expanding this version** if the execution is valid and adequately covered but S2 fails to improve B1, or traces add no value over S1. Do not add an LLM to obscure a failed candidate gate.
- **Inconclusive** for insufficient labels/groups, invalid clocks, poor trace coverage, or gains below the practical threshold. Investigate the measured bottleneck on development data and preregister a revised experiment rather than retuning on holdout.

## 7. Execution sequence and timebox

The trace schema/semantics review is complete and documented separately; the following experiment implementation work has not run.

| Stage | Budget | Exit evidence |
|---|---:|---|
| 0. Validate bundle, labels, clocks, incident grouping; freeze split | 30 min after data readiness | Inventory, coverage, clock examples, split manifest |
| 1. Baseline adapter and evaluation harness | 45 min | B0/B1 development rankings; grouping and scorer fixtures pass |
| 2. Symbolic metric channel | 45 min | S1 development report and inspectable episodes |
| 3. Trace channel, fusion, numerical control | 75 min | S2/N2 development report; edge/missing-channel fixtures pass |
| 4. Freeze config, run holdout once, write result | 30 min | Paired table, evidence, costs, decision |

Total engineering estimate: 3 h 45 min after data is usable; adjust against the actual available hackathon time. Download/ingestion time is additional and measured. If time runs out before traces, publish the metric pilot as partial work; it does not answer H1/H2. Inspect all rescued and regressed holdout blocks only after the report is frozen.

## Project Structure

```text
specs/001-candidate-recall-experiment/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/experiment-cli.md
  checklists/requirements.md
# Proposed during implementation:
src/symbolic_rca/
  data.py          # bounded reads, clocks, IDs, caches
  episodes.py      # independent metric and trace symbolizers
  rank.py          # B1/S1/S2/N2 scoring; no gold input
  evaluate.py      # groups, gold, paired metrics, decision
  cli.py
configs/experiment-001.json
experiments/001/   # frozen manifests/configuration; no raw telemetry
out/experiment-001/  # ignored generated rankings/evidence/reports
```

**Structure decision**: One small offline package with retrieval, representation, ranking, and evaluation separated. No service, UI, model provider, database, or generalized motif framework. Stage-level work above is ready to become `tasks.md` via `speckit-tasks`.

## Complexity Tracking

Only the two bounded constitution exceptions above apply. The diagnostic audit scripts and their descriptive measurements support this plan. No experiment ranker, benchmark evaluation, or positive RCA claim is included.
