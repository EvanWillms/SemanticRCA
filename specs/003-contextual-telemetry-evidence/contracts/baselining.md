# Qualified contextual baseline contract

**Version**: design v1, 2026-09-17. **Authority**: [ADR 0004](../../../docs/adr/0004-qualified-contextual-baselines.md), [spec](../spec.md).

## Reference policy

The initial short-window frontend profile is specialized by the [feature 009 baseline contract](../../009-qualified-short-baselines/contracts/baseline.md) and [feature 010 descriptor contract](../../010-comparative-descriptors/contracts/descriptors.md). Their explicit no-fallback policy does not remove the broader reference alternatives below.

Declare the observation unit, comparison question, context keys and unknowns, reference source views, estimator, support criteria, time/availability mode, bounded lookback expansion, fallback order, and contamination/variation policy before evaluating the candidate window. Freeze membership for the investigation. Do not use gold onset, component, or reason to select references or remove inconvenient observations.

Historical self-reference, contemporaneous peers, historical context matches, independently verified-success observations, and engineering constraints are distinguishable views. Known requirements are not inferred from historical percentiles. A reference window is not called healthy merely because it precedes the prompt. Peer agreement does not exclude a shared fault.

Context matching must not remove the target difference. In particular, exact operation-count matching is permitted for conditional latency comparison but must preserve unmatched/changed structures for a separate structural comparison. Exposure normalization retains raw volume, and completed throughput must not silently stand in for offered demand.

## Eligibility and differences

Each requested comparison returns one of:

- `eligible`: evidence supports the declared question within its scope;
- `qualified`: a usable limited comparison with named unresolved assumptions;
- `unavailable`: no supported result for this question, with a reason.

Support thresholds depend on the estimator and sampling structure. Preserve observation count, time coverage, exposure, and missingness separately. No universal minimum sample count, lookback, tail percentile, or alarm threshold is established by this contract.

Keep support, center stability and individual field availability separate. In the short-window profile all supported comparisons retain qualifications. A supported unstable center can supply an explicitly unstable median comparison; zero MAD does not invalidate median or signed excess, although it makes a MAD-derived score undefined.

Numerical findings retain raw value/unit, reference center/spread where supported, absolute difference, direction, and applicable ratios/standardized departures. Ratios with zero denominators and standardized scores with zero scale remain undefined. A declared measurement-resolution/engineering tolerance can support a constant-reference comparison; no arbitrary epsilon or infinite-confidence alarm is implied.

Frequency findings retain denominators. Structural findings name changed observations/relationships. Missing-event findings require a stated expectation and sufficient completed observation coverage; otherwise the finding is unobserved/unknown. Keep contextual mismatch and parsing uncertainty distinguishable from system novelty.

Every finding links observations, cohort/version, selection/comparison versions, source evidence, qualifications, and conflicting views. A baseline change creates new findings without rewriting descriptive facts or earlier results.

## Prioritization and diagnosis boundary

A priority policy specifies comparison families, candidate allocation, and treatment of absolute magnitude, relative departure, persistence, scope, and quality. It must retain meaningful alternatives and unavailable comparisons in the audit trail. Scores across families must not be presented as commensurate or probabilistic without calibration. Reused observations must not be counted as independent evidence.

Assemble candidate episodes without forcing all findings into the prompt's failure count. Preserve a supported behavior-onset interval and its sampling limits separately from inferred fault time. The output is a set of findings and candidate investigations; the existing incident contract governs final when/where/why projections.
