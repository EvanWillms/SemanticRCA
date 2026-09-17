---
status: accepted
date: 2026-09-17
---

# Freeze a qualified five-minute frontend reference without automatic fallback

Use a five-minute historical reference, pooled across an explicit frontend allowlist and conditioned on recorded direct-child operation presence, for the first frontend-duration baselining feature. Reference selection and qualification produce a versioned baseline; comparison produces a separate descriptor under [ADR 0014](0014-reference-relative-comparative-descriptors.md). This specializes [ADR 0004](0004-qualified-contextual-baselines.md), without claiming that recent or well-supported traffic is healthy.

## Evidence and alternatives

The [short-window report](../../data/experiments/short-window-baselining-v1/final-report.md) and its [frozen selection](../../data/experiments/short-window-baselining-v1/selection.json) support C1 pooled at five minutes: 9,763/9,802 core requests had supported comparisons; confirmation supported 50,366/50,933 primary requests. These are availability measurements on exposed telemetry, not prospective guarantees. The [source-controlled evidence summary](../../specs/009-qualified-short-baselines/evidence.md) records the qualifications and failure cases.

C0 alone mixes contexts whose cohort medians span about 0.17–92 ms. C2's exact multiplicity conditioning loses additional support without a demonstrated general improvement over C1; counts therefore remain in the structural channel. Five-minute same-replica C1 fails the aggregate coverage screen; ten-minute same-replica is a separate supported alternative, not a fallback. Pooling improves support but does not establish replica equivalence: some pooled centers differ from same-replica centers by more than 5 ms. The class-specific decision table remains evidence, not an automatic policy router.

## Decision

- Observe blank-parent frontend roots with scoped execution identities. Freeze the explicit `frontend-0`, `frontend-1`, `frontend-2` allowlist for this dataset; preserve replica identities and unknown deployment/workload/capacity equivalence. Other deployments require a new declared inventory and policy version.
- Define C0 as raw root operation/type and C1 as C0 plus the set of recorded direct-child operation/type pairs. Preserve multiplicity and component bindings outside the C1 key. Recovered empty structure and unknown structure are different states.
- At anchor T, select references starting in `[T−5 minutes, T)` whose recovered execution endpoints are all strictly before T. Recover recorded traces across the source inventory; a fixed time buffer does not prove closure. Report completion exclusions and their duration distribution. This is retrospective event-time qualification, not a claim that records had arrived online by T.
- Freeze reference membership for six five-minute query-start slices through T+30 minutes. Do not refresh within that horizon, trim slow references, expand history, change context, or switch replica policy to obtain a preferred result. A new anchor or explicit alternative creates a separate version and comparison context.
- Require at least 20 resolved, usable references across at least three occupied one-minute bins, with no minute contributing more than half. These are versioned scope settings, not universal sufficiency guarantees. Unmatched, ambiguous, and unsupported requests abstain from supported duration comparison while remaining in coverage and structural reporting.
- Assess center stability separately from sample support: the study's one-minute block resampling, 200 replicates, seed 42, and 5th–95th percentile interval remain an exploratory screen. Fewer than 190 usable replicates is inconclusive; full width above 40% of a positive median fails the stable-center screen. A supported but unstable center remains explicitly qualified descriptive evidence. A zero median makes that relative-width screen inapplicable, not the median meaningless.
- Retain count/time support, exclusions, distributions, pooling contributions, temporal sensitivity, uncertainty, source membership, and policy versions. Zero MAD does not invalidate a supported median. Qualifications never disappear because aggregate coverage is high or a screen passes.

## Consequences and scope

No automatic fallback is selected. This preserves comparison meaning at the cost of explicit gaps, such as the confirmation window with 54.19% primary support. A supported reference near 60 seconds remains a possible degraded reference. Broad stability or coverage claims cannot conceal individual cohort failures.

This decision defines baselining only. It does not authorize service-span/metric/log baselines, tail reliability, adaptive online refresh, healthy/abnormal classification, alert thresholds, anomaly-library selection, or diagnostic accuracy claims. [Feature 009](../../specs/009-qualified-short-baselines/spec.md) specifies acceptance independently of those later layers. Accepted status records the architectural choice; the research prototype is not a certified production implementation.
