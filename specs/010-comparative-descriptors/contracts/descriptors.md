# Comparative descriptor contract

**Version**: design v1, 2026-09-17. **Authority**: [ADR 0014](../../../docs/adr/0014-reference-relative-comparative-descriptors.md), [feature 010](../spec.md). This is a semantic contract, not an implementation API.

## Required contents

A descriptor contains its identity/version, scoped observation identity, declared context and measurement, baseline identity/version, comparison definition, result fields with availability reasons, support/stability and other qualifications, structural comparison where available, and resolvable evidence references. A compact label is a rendering of this record, not a replacement for it.

Availability distinguishes `available`, `not_requested`, `undefined`, and `unavailable`, with reasons. Undefined arithmetic (such as division by zero) differs from an unavailable eligible reference. Audit-only summaries from unsupported references are not eligible comparison statistics.

## Duration semantics

For valid nonnegative finite durations in compatible units, let x be the observation, m the reference median and a the raw reference MAD:

| Field | Meaning and eligibility |
| --- | --- |
| Observed duration | x, with original measurement and normalization provenance |
| Reference median | m from the identified supported baseline |
| Signed excess | x − m; positive, negative and zero values retained |
| Optional ratio | x / m, only when m > 0 |
| Optional standardized departure | (x − m) / (1.4826 × a), only when a > 0; identify this research definition and version explicitly |

The research phrase “absolute excess” refers to duration units, not `abs(x − m)`. Compare unrounded values; above/below/equal labels follow their sign. A tolerance, materiality threshold or alternative normalization requires its own declared policy rather than a silent change to these labels. Standardized departure is not a probability or calibrated alert.

Supported unstable baselines retain numerical comparisons with instability attached. Unsupported baselines retain raw observations and audit evidence but no eligible duration comparison. Unknown unit compatibility prevents numerical comparison; the source's declared provisional normalization can be used only with its qualification preserved. Negative/nonfinite observations are invalid measurements, not unusually fast/slow requests.

| Observation / reference | Expected result |
| --- | --- |
| 120 ms / supported median 100 ms | +20 ms |
| 80 ms / supported median 100 ms | −20 ms, retained outside positive-excess views |
| 12 ms / supported constant 10 ms | +2 ms; ratio 1.2 if requested; standardized departure undefined |
| 12 ms / supported constant 0 ms | +12 ms; ratio and standardized departure undefined |
| 120 ms / unsupported median summary 100 ms | Numerical comparison unavailable; raw duration and audit summary retained separately |
| 120 ms / supported unstable median 100 ms | +20 ms with failed stability screen; no stable-center claim |
| 0.921 ms / supported median 0.172 ms | +0.749 ms; a large ratio does not establish operational importance |

## Structural semantics

Use the eligible C0 reference population under the same declared time/completion policy, before restricting to the query's C1 shape. Retain identified reference patterns, operation/type sets, multiplicities and their frequencies. Frequency denominators count references whose recorded structure is known; unknown structure has a separate count. A zero known denominator makes frequencies unavailable.

Describe additions/removals or count deltas against an explicitly identified reference pattern. If several patterns occur, preserve those alternatives and frequencies. No modal pattern becomes an expected business route by default. “Not observed in this reference population” does not mean never previously observed or newly introduced into the system.

For a named reference containing A once and B once, A once/B twice has unchanged C1 presence and a B count delta of +1. A once/C once differs by B −1 and C +1 against that reference. Unknown query structure supports neither claim. A recovered empty child set means no direct children were recorded in the declared recovered data; it does not certify that the execution made no calls.

Structural comparison remains available when supported C1 duration comparison is absent, provided the structural evidence and its own denominator are available. It never borrows duration support to conceal missing structural evidence.

## Review and aggregation

The initial review view takes at most five available positive signed excesses, descending, with ties ordered lexicographically by deployment, trace identity and span identity. It retains the qualification of each result, including supported instability. The complete population remains accessible, including zero/negative differences, unavailable comparisons and structural observations.

Report resolved observations and window occurrences separately. Identify repeated observations and reference membership across windows; fields, descriptors and overlapping windows are not independent incidents. The view has no cross-family severity meaning and does not remove failures from coverage denominators.

## Evidence and revisions

Evidence references resolve to the actual source representation: exact records or array members and the correct measurement, plus baseline membership/statistics and rule versions. A trace identifier or KPI name alone is insufficient when it cannot locate the claimed record and value. Validate source snapshot, entity, measurement and version compatibility, not merely pointer syntax.

A changed observation source, baseline or comparison definition produces a distinct descriptor version. Earlier observations, baselines and descriptors remain reproducible. Renderings retain access to all qualifications and availability reasons rather than turning a missing value into zero or stripping a warning from a ranked result.
