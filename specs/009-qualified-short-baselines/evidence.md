# Evidence translated into baselining and descriptor requirements

Source: [short-window final report](../../data/experiments/short-window-baselining-v1/final-report.md), [frozen selection](../../data/experiments/short-window-baselining-v1/selection.json), [predeclared protocol](../../docs/research/experiments/short-window-baselining.md). Local generated artifacts are linked for reproducibility; this summary preserves the decision-relevant facts in source documentation. They are research results on exposed telemetry, not feature acceptance results.

| Report finding | Architectural/specification consequence |
| --- | --- |
| C1 pooled five-minute supports 9,763/9,802 core requests; confirmation 50,366/50,933 primary requests | Adopt a scoped five-minute policy, not universal coverage promises; feature 009 FR-004/009 |
| C0 pooled centers 55.577–58.363 ms versus C1 cohort centers 0.168–91.609 ms | Condition on recorded operation presence, with qualified observed-shape semantics; 009 FR-002 |
| C2 pooled five-minute loses 32 more requests; common-population median excess change zero per anchor and top-five overlap 80–100% | No general need for exact count conditioning established; retain counts in a separate structural descriptor; 010 FR-007 |
| Five-minute same-replica C1 support 88.54%; ten-minute support 97.31% | Pooled five-minute is selected; same-replica ten-minute is a separate alternative, not an activated fallback; 009 FR-004 |
| On 8,679 commonly supported requests, pooled-minus-same centers range −2.308 to +7.316 ms; 96 differ by more than 5 ms | Preserve replica contributions and pooling qualification; 009 FR-007/008; 010 FR-004 |
| Row 62 primary 343/633 supported; completion exclusions 29/739; supported median near 60,000 ms | Low coverage and boundary-selection bias remain visible; support does not establish health; 009 FR-003/009 |
| Row 45 has 449 primary comparisons failing the width screen despite count/time support | Separate support from center stability, retaining qualified descriptive outcomes; 009 FR-006; 010 FR-002 |
| Doubling durations in 60% of copied references moves median 56.892 to 109.487 ms and weakens all 280 standardized departures | Median robustness is limited; retain contamination/sensitivity qualifiers; no healthy-baseline claim; 009 FR-007/008 |
| Both full trace files validated: 18,160,322 records; 200 sampled source pointers reconcile; 34 package tests and 216 synthetic + 216 natural control cells pass | Prior extraction/contract evidence informs future acceptance, but does not certify the feature; 009 acceptance B01–B12 and 010 acceptance D01–D12 |
| C1 matching may hide operation-set changes; C2 may hide multiplicity changes; unknown structure is distinct from empty | Parallel C0 structural descriptors and zero silent losses; 010 FR-006/007 |
| 57 windows/70 rows and five connected overlap groups; no labels used | Preserve shared-support and exposure accounting; no held-out or incident-sensitivity claim; 009 FR-011 |

## Normative choices versus observations

The selected five-minute C1 pooled policy, no fallback, count/time thresholds, and exploratory uncertainty screen become versioned requirements for this limited scope. The reported coverage percentages do not become service-level guarantees. The original aggregate 90% / 80%-anchor/interval-width policy-selection gates are historical selection criteria, not permission to label each cohort stable or to discard replay failures.

The main comparison product is median and signed excess. Ratios and MAD-derived measures remain optional diagnostics with field-specific availability; they are not a newly selected detector or a calibration result. The contracts split baseline production from descriptor production and make state composition explicit. These are design decisions grounded in the report, not claims that the research prototype already implements every new requirement.
