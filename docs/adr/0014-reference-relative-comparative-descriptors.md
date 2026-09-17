---
status: accepted
date: 2026-09-17
---

# Describe differences without promoting them into anomaly or cause

Represent each qualified comparison as a versioned comparative descriptor that links an observation to its baseline and states the measured difference, its support, and its limits. The primary duration descriptor reports the observed duration, reference median, and signed excess in the same units; a parallel structural descriptor retains changes hidden by conditional latency matching. This makes the short-window study's useful comparison product explicit without asserting detection or diagnosis.

## Decision and trade-offs

- Keep observations, baselines, comparative descriptors, priority views, and diagnostic hypotheses separate. A baseline change creates new descriptors without rewriting observations or earlier comparisons. The baseline producer owns membership and qualification; the descriptor producer cannot silently reselect references.
- Lead with `observed duration − reference median`. Preserve negative, zero, and positive results. “Absolute excess” in the research means a signed difference in duration units, not the absolute-value function. The primary product is median/excess; optional ratio and standardized-departure diagnostics retain explicit definitions and availability reasons.
- Undefined fields do not invalidate every field: zero MAD leaves median/excess usable but standardized departure unavailable; zero median also makes the ratio unavailable. No epsilon, infinity, zero-score substitution, or inferred confidence probability is permitted. Unknown unit compatibility prevents numerical comparison rather than silently converting values.
- A statement such as “above the reference median” denotes arithmetic ordering only. It must retain the actual values, baseline identity, measurement qualification, and support/stability state. It does not mean materially slow, statistically significant, healthy/unhealthy, an SLO breach, or a fault.
- Preserve C0 structural observations alongside C1 duration comparison: sets, multiplicities, reference frequencies and denominators, unmatched patterns, and unknown retrieval. Name differences against identified reference patterns; absence from a finite reference is not proof of a newly introduced system behavior. Unknown structure cannot become a known empty set or an asserted missing operation.
- Keep coverage and field availability first-class. Every selected request has a result or an explained unavailable outcome. A top-five positive-excess review is a view over that population, not a filter that deletes negative differences, unsupported cases, or structural observations. Relative scores alone cannot determine operational importance.
- Retain provenance to exact observations, reference membership, selection/comparison definitions, and uncertainty evidence. A compact symbol or prose rendering must resolve back to this record. No mandatory “anomaly” or benchmark fault-reason vocabulary is introduced.

## Evidence and alternatives

The [short-window report](../../data/experiments/short-window-baselining-v1/final-report.md) establishes broad availability of median/excess comparisons, but also shows sensitivity to pooling, reference contamination, and unstable centers. Conditioning on operation sets reduces mixture; exact counts can fragment support without adding a generally demonstrated benefit. Neither structural conditioning nor a high standardized departure establishes importance or cause.

A single anomaly score would hide units, magnitude, unavailable estimates, reference qualifications, and structural nonmatches. A binary healthy/abnormal descriptor would require evidence and calibration absent from this study. Richer descriptors cost metadata but preserve what a later investigator or detector is entitled to conclude.

## Resulting specifications

[Feature 010](../../specs/010-comparative-descriptors/spec.md) owns descriptor semantics and acceptance. [Feature 009](../../specs/009-qualified-short-baselines/spec.md) supplies the specialized frontend baseline. This refines [ADR 0002](0002-descriptive-semantic-compression.md), [ADR 0004](0004-qualified-contextual-baselines.md), and [ADR 0010](0010-faceted-semantic-labeling.md); it does not supersede their broader evidence boundaries. Production method does not change claim meaning. No service-operation comparison, causal label, cross-family severity score, p95/p99 claim, or calibrated alert is established here.
