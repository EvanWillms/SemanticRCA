---
status: accepted
date: 2026-09-17
---

# Identify unusual behavior against qualified contextual references

A bounded incident prompt supplies investigation scope but leaves the relevant abnormal behavior to be discovered. Compare descriptive evidence against versioned, context-compatible references, recording differences and qualifications separately from observations and causal hypotheses. A typical reference does not establish health or success.

## Decision and trade-offs

- Define the comparison question and conditioning context before scoring. Build reference groups for candidate operations/entities without using gold component, onset, or reason. Freeze membership and policies for each investigation.
- Keep historical, peer, and independently verified-success references distinguishable. Declare selection, permitted lookback expansion, fallback, coverage, and unresolved context. Conflicting references remain visible; do not select the reference producing the largest desired departure.
- Distinguish eligible, qualified, and unavailable comparisons. Sample support is estimator-specific. Constant references, sparse observations, contamination, drift, and collection loss require explicit handling rather than forced scores.
- Compare structure, frequency, measured attributes, context, and expected activity as separate questions. Matching an observed call shape can support conditional latency comparison, but cannot filter changed or unmatched shapes out of structural investigation.
- Preserve absolute and relative differences, temporal persistence, scope, and quality. Standardized departures are not fault probabilities or universally comparable severity scores. Priority rules and review budgets are separate, versioned policies.
- Preserve observed behavior onset separately from inferred fault onset. Neither novelty nor a large departure proves the originating fault; both are potential diagnostic evidence.

A single global threshold ignores workload and instrumentation differences. Treating the preceding interval as healthy is unjustified in this benchmark. Unconstrained adaptation can absorb a disturbance into the reference. Qualified, frozen views cost more metadata and can produce abstentions, but keep the comparison reproducible and its assumptions inspectable.

## Resulting specification

The short-window frontend specialization is governed by [ADR 0013](0013-qualified-short-window-frontend-baselines.md) and [feature 009](../../specs/009-qualified-short-baselines/spec.md), with comparative descriptors in [ADR 0014](0014-reference-relative-comparative-descriptors.md) and [feature 010](../../specs/010-comparative-descriptors/spec.md). Its selected five-minute policy has no automatic fallback; this is a scoped choice, not a general prohibition on separately declared reference views. Support, center stability and field availability remain separate, and none establishes health or diagnostic accuracy.

See [feature 003](../../specs/003-contextual-telemetry-evidence/spec.md), the [baseline contract](../../specs/003-contextual-telemetry-evidence/contracts/baselining.md), and acceptance cases B1–B6. The [baselining research note](../research/contextual-baselining.md) explains the process; the [case-25 demonstration](../research/examples/track-1-case-25-anomaly-discovery.md) is development evidence, not detector validation. This decision extends ADR 0002's comparison boundary and leaves the first representation experiment unchanged.
