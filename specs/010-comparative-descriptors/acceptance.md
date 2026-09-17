# Comparative descriptor acceptance matrix

These are planned acceptance cases, not executed feature results. Independently authored expectations are required; reproducing an implementation's own output is insufficient.

| Case | Required verification | Requirements |
| --- | --- | --- |
| D01 | Fixed context/reference with independently calculated 25%, 50% and 100% duration interventions, unchanged controls, negative differences and values near display rounding boundaries; preserve exact signed arithmetic and units | FR-001, FR-002, FR-011 |
| D02 | Supported constant and zero references; median/excess remain usable while ratio and MAD-derived fields have the prescribed independent availability; not-requested differs from undefined | FR-002, FR-003 |
| D03 | Sparse/unmatched references, invalid observations, unknown or incompatible units; preserve raw evidence and explained unavailable outcomes without numeric substitution | FR-003, FR-004, FR-006 |
| D04 | Supported wide/inconclusive intervals, provisional units and unverified health/pooling; qualifications survive full and compact renderings without significance or anomaly claims | FR-004, FR-005 |
| D05 | Added/removed operations and unmatched C1 shapes; preserve comparisons against identified C0 patterns with correct frequency denominators | FR-006, FR-007 |
| D06 | Multiplicity changes that leave C1 presence unchanged; preserve separate count deltas and unchanged cohort identity | FR-001, FR-007 |
| D07 | Unknown versus recovered empty structure, multiple reference patterns and zero known denominator; no inferred absence, expected route or frequency division by zero | FR-007, FR-010 |
| D08 | Tiny-center large ratios versus larger duration excesses, negative/zero outcomes and tied positives; top-five ordering uses positive signed excess and scoped identity, retains qualifications and loses no full-population records | FR-005, FR-006, FR-008 |
| D09 | Shared requests across windows and six frozen-baseline slices; reconcile observation/occurrence/field/cohort counts and expose unavailable comparisons without interpreting counts as faults | FR-006, FR-010 |
| D10 | New baseline or calculation version; preserve old observations/descriptors, create a distinct comparison and reject silent reference reselection | FR-001, FR-009 |
| D11 | Valid, malformed, stale, wrong-entity and wrong-statistic references; validate both resolution and claimed value, including array-member source representations | FR-009 |
| D12 | Independently authored natural controls and planted arithmetic/structure changes; preserve expected outcomes without fault labels, an encoder, model or diagnoser | FR-011 |

## Constitution review

The feature preserves observations, comparisons and diagnosis as distinct products; requires exact evidence and explicit uncertainty; and makes no causal or evaluator-accuracy claim. Frontend-only scope does not remove the architecture's independent metric discovery path. Existing research results motivate the contract but do not certify a production implementation. Planning, tasks, implementation and integration remain subsequent stages.
