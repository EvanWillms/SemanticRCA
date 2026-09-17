# Contextual baselining for incident investigation

Status: proposed process, 2026-09-17. Generalizes the [case-25 discovery scan](examples/track-1-case-25-anomaly-discovery.md); it is not an implemented or validated detector. It elaborates the qualified-reference comparison in the [current specification](../../specs/001-candidate-recall-experiment/spec.md), without changing the scope of the first representation experiment.

## Definition and purpose

The architectural decision is recorded in [ADR 0004](../adr/0004-qualified-contextual-baselines.md); [feature 003](../../specs/003-contextual-telemetry-evidence/spec.md) and its contracts define the resulting requirements. This note provides rationale and examples rather than implementation validation.

A **baseline** is a versioned description of reference behavior for an explicitly defined context, together with the observations, variation, coverage, and comparison policy that support it. Depending on the question, it can contain a numerical distribution, an event-rate distribution, or a set of observed execution patterns.

Baselining answers: **Compared with which observations, under which conditions, is this behavior different, and by how much?** Typical behavior, independently verified successful behavior, and a contractual requirement are distinct references. A baseline need not establish health; a service requirement is not estimated by taking a percentile of whatever happened historically.

Descriptive evidence stays stable when the baseline changes. For example, a packet still says that a request lasted 428.249 ms. A comparison finding adds that this exceeds a particular cohort's median by 334.2965 ms. Fault attribution is a subsequent inference.

## 1. Specify the comparison question

Declare the observation unit, context, feature, direction of interest, and resolution before scoring. Different questions can use different references for the same observation.

| Question | Observation unit | Relevant context | Comparison |
|---|---|---|---|
| Is this request unusually slow? | Request or operation invocation | Logical operation, workload class, software/configuration, instrumentation | Duration distribution; absolute excess and relative departure |
| Did execution structure change? | Recorded request graph | Logical request type and input class where available | Operations, edges, multiplicity, ordering constraints, and missing/novel patterns |
| Did resource behavior change? | Entity/KPI interval | Entity role, capacity, workload, configuration, sampling | Level, direction, variability, duration of change, or headroom |
| Did an event become frequent? | Event class over an exposure interval | Component/operation, logging configuration, traffic or elapsed time | Counts and rates with denominators retained |
| Did outcomes change? | Requests with interpretable outcomes | Operation and instrumentation-specific outcome semantics | Outcome proportions and counts, including unresolved outcomes |
| Did expected activity disappear? | Expected observations over an interval | Offered demand, collection coverage, schedule, instrumentation | Missing observations versus evidence of missing collection |

Counter increments require a declared reset/rate policy. A raw categorical status must not be treated as a globally ordered numeric error score. A measured trend and an elevated level remain different descriptive attributes. Trace interval comparisons retain clock, unit, and instrumentation uncertainty.

## 2. Choose what must match, and what may differ

Select comparison context using information available independently of the answer: operation identity, known deployment/configuration, capacity, offered workload, or request input class. Record unavailable context rather than inventing it. Preserve original node, service, and replica bindings even when grouping by role.

Distinguish conditioning variables from the behavior under investigation. Matching on latency would hide a latency anomaly. Matching exactly on call count would hide extra or missing calls. Matching on observed throughput can hide a throughput collapse. Workload context should preferably describe offered demand rather than only completed work.

The case-25 operation-count signature supports a **conditional latency comparison among matching observed shapes**. It is a useful fallback when route/input metadata is absent, but it is not the universal cohort key. Run a separate structural comparison across the broader logical request cohort, and retain unmatched requests as potentially informative findings. No signature match does not mean normal or irrelevant.

## 3. Build qualified reference views

Use complementary references under a predeclared selection policy:

| Reference view | What it helps distinguish | Main qualification |
|---|---|---|
| Same entity/operation before the query window | Change from its own recent behavior | Earlier faults, drift, warm-up, and sparse observations may contaminate it |
| Comparable replicas during the query window | A localized departure from contemporaneous peers | Peers may share a fault, host, dependency, or workload imbalance |
| Comparable historical contexts | Recurrent workload or configuration effects | History must actually contain those contexts; do not assume seasonality from a short record |
| Independently verified successful executions | Difference from a specified successful outcome | Record the success criterion, scope, and verification source |
| Known engineering constraint | Difference from a configured limit or obligation | Keep this constraint separate from an empirical typical-behavior baseline |

For a bounded Track 1 investigation, start with reference observations before the supplied window and freeze them for that investigation. Evaluate contemporaneous peers separately where comparable. Neither view uses the labelled onset, root component, or reason to choose reference data. If a source is ineligible, use a declared fallback or return no supported comparison; never silently choose the reference that produces the largest anomaly score.

An in-window background can be used when external history is unavailable, but must be identified as potentially incident-contaminated. A later recovery interval can corroborate a retrospective diagnosis; it must not silently replace the original reference or be presented as information available at first detection.

## 4. Qualify the reference before using it

Evaluate context compatibility, retrieval completeness, observation coverage, time support, sampling, measurement resolution, and evidence of multiple regimes. Record sample count and time coverage separately: many requests in one burst do not provide many independent time periods.

Eligibility depends on the comparison. A count sufficient for a rough median need not support a tail percentile, an event-rate estimate, or a seasonal model. The 20-reference cutoff used in the exploratory scan is not a general minimum.

Use three explicit outcomes:

- **Eligible:** supports the declared comparison within its stated scope.
- **Qualified:** supports a limited comparison with named unresolved assumptions, such as an unverified-health reference or unknown workload mix.
- **Unavailable:** insufficient or incompatible evidence; no supported comparison for this question.

Retain contamination indicators and conflicting references. Robust statistics can reduce the influence of some extreme observations; they cannot certify a healthy reference or rescue a cohort dominated by another regime. Do not remove observations just because they weaken the desired diagnosis or because a gold label identifies them as faults.

## 5. Measure the relevant differences

For numerical observations, retain at least the value, reference center and spread, absolute difference, and direction. Ratios are useful when the reference magnitude and units make them meaningful. Quantile ranks require adequate reference support.

One optional descriptive ranking measure is:

```text
departure = (observed − reference median) / (1.4826 × reference MAD)
```

This is not a probability or a universal alarm threshold. If MAD is zero, do not divide by zero, discard the observation, or invent an infinite-confidence alarm. Report a departure from a constant/quantized reference and use a declared measurement-resolution or engineering tolerance if one is available; otherwise leave standardized magnitude unresolved. Ratios likewise remain undefined when the reference is zero.

For counts and rates, retain exposure: events per request and events per unit time answer different questions. Keep total volume visible alongside normalization. For structure, retain which operations, edges, or counts differ, with coverage qualifications; do not force the finding into a latency score. For missingness, distinguish evidence that an expected event did not occur from lack of evidence because collection failed.

Every finding should preserve:

```text
observation + context + source evidence
reference identity/version + selection rule + coverage/qualifications
comparison rule/version + observed difference + unresolved assumptions
```

## 6. Turn differences into an investigation queue

Keep separate dimensions of a finding: degree of departure, absolute magnitude, persistence or recurrence, affected scope, evidence quality, and corroborating or conflicting signals. A 0.748 ms increase can be statistically conspicuous yet much smaller than a 334 ms increase. Both deserve accurate description; their investigation priority can differ.

Do not directly equate uncalibrated scores across KPIs, log classes, and trace features. Initially retain ranked candidates within each comparison family and use an explicit review budget across families. Any combined priority rule or alert threshold is a separate policy to validate. Shared spans or derived metrics must not be counted as independent corroboration merely because they appear in multiple packets.

Group related findings into candidate episodes by entity, time, and observed dependencies. Preserve isolated spikes as well as sustained shifts. Candidate grouping must allow multiple incidents and overlapping symptoms; the prompt's failure count does not force every anomalous observation into that many groups.

Estimate a behavior-onset interval from the first supported departure and the preceding reference-consistent evidence, including sample spacing and gaps. That interval is evidence for diagnosing fault onset, not automatically the root-cause time. A symptom-based entry point can lead backward to an earlier resource or execution change.

## 7. Freeze and version the baseline

Store reference membership or reproducible selection criteria, context bindings, time bounds, exclusions, sample support, estimator, uncertainty, and comparison-policy version. A finding must remain reproducible after new telemetry arrives.

For retrospective diagnosis, freeze references before scoring the candidate window. For an eventual online system, define adaptation as a separate policy: preserve a stable comparison view while evaluating a newer one, and expose disagreements. Automatically assimilating an ongoing disturbance can make the disturbance disappear from the baseline-relative findings. Software, instrumentation, or workload changes require explicit compatibility review and a new reference version where appropriate.

## Minimal proposed interface

```text
build_reference(observations, context, reference_policy)
  -> reference + eligibility + qualifications

compare(observation_or_episode, reference, comparison_policy)
  -> findings with provenance, differences, and uncertainty

prioritize(findings, investigation_policy)
  -> candidate investigations, retaining alternative signals
```

Compression supplies descriptions to this process. Comparison adds context-relative findings. Diagnosis links those findings to hypotheses about when, where, and why. These stages must remain inspectable separately.

## Separate validation of baselining

The [short-window like-for-like experiment space](experiments/short-window-baselining.md) scopes a concrete E1–E3 exploration for `data/track-1`: frontend duration comparisons using 5–60 minute references, progressively stricter context matching, and explicit coverage, stability, and change-preservation checks. It defines how to choose a bounded useful scope; its candidate settings are not validated defaults.

The [phase-isolated experimentation protocol](phase-isolated-experimentation.md) separates reference selection, qualification, difference description, episode assembly, and downstream diagnosis into independently testable studies. It also defines connected checks for errors passed between phases. It is a proposed protocol, not validation evidence.

Use independently authored observations and references before relying on encoder output or benchmark accuracy. Check at least:

- Identical behavior in compatible contexts produces no invented departure; a planted change remains visible.
- Expected workload differences change the appropriate comparison without rewriting the observation.
- Extra/missing calls remain visible instead of being filtered out by exact-shape matching.
- Sparse, constant, contaminated, shifted, and incompatible references yield the declared qualification or refusal.
- Collection loss and absence of expected activity produce different findings.
- A peer-wide disturbance is not dismissed solely because all peers agree.
- An isolated spike and a sustained shift retain their different temporal descriptions.
- Changing the reference version changes only reference-relative findings and preserves earlier results for audit.

Then freeze comparison and prioritization policies and evaluate candidate retrieval across grouped, held-out incident windows under a fixed review budget. Report missed incidents, candidate burden, abstentions, and sensitivity to reference choice. Negative controls need independent justification; absence from a benchmark fault label does not alone prove health. Root-cause accuracy is a later measurement and cannot replace these checks.
