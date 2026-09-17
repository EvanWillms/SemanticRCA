# Frozen frontend baseline contract

**Version**: design v1, 2026-09-17. **Authority**: [ADR 0013](../../../docs/adr/0013-qualified-short-window-frontend-baselines.md), [feature 009](../spec.md). This is a semantic contract, not an implementation API.

## Policy profile

| Field | Required meaning for the initial profile |
| --- | --- |
| Observation | Scoped, resolved blank-parent frontend root; raw operation/type and source identity retained |
| Components | Explicit `frontend-0`, `frontend-1`, `frontend-2` allowlist, pooled within one deployment |
| C0 | Root raw operation name and raw type |
| C1 | C0 plus the set of raw direct-child operation/type pairs; counts and bindings retained separately |
| Anchor/reference | Epoch-millisecond T; UTC+8 presentation; root starts in `[T−300000,T)` |
| Completion | Root and all recovered span endpoints strictly less than T; unresolved completion excluded with reasons |
| Query horizon | Starts in six half-open five-minute slices `[T+300000j,T+300000(j+1))`, j=0…5 in milliseconds; endpoints may extend past the slice |
| Support | At least 20 usable references, 3 occupied one-minute bins, largest bin ≤50% of references |
| Alternatives | No automatic fallback or refresh; same-replica/other-lookback views have separate identifiers |
| Primary statistic | Empirical median; descriptive quartiles and raw MAD accompany it |
| Stability screen | One-minute blocks over the whole reference interval, including empty blocks; 200 resamples, seed 42; full p95−p05 width |

For resampling, draw the original number of interval blocks with replacement and keep all observations in each drawn block. Empty resamples fail explicitly. Use a declared, versioned quantile convention (the research uses linear interpolation between ordered values). Compare widths at unrounded working precision; display rounding cannot change a decision. Median/MAD and normalization inherit the versioned provisional duration-unit interpretation; incompatible or unknown conversions cannot silently mix units.

## Required baseline content

A baseline identifies the source snapshot/extraction, deployment, anchor/reference interval, context and replica policies, member observation identities and resolvable source locators, selection/support/estimator versions, and reusable membership identity. It retains descriptive statistics and diagnostics even where they are insufficient to authorize a comparison, marking such summaries audit-only.

Diagnostics include raw-record and resolved-request counts, usable/excluded membership with reasons, per-minute and per-replica contributions, first/last observation, largest inter-observation gap, median/quartiles/MAD, completion-excluded duration distribution, first/second-half centers, leave-one-minute-out changes, and bootstrap interval/replicate counts. Explicit alternative-policy evaluations retain common-support membership and pooling/lookback differences; they never replace the selected baseline automatically.

## State composition

| Dimension | States and consequences |
| --- | --- |
| Support | `supported` or `unavailable`, with all count/time/context/identity/unit failure reasons |
| Center stability | `passes_screen`, `fails_screen`, `inconclusive`, `not_applicable_zero_center`, or `not_assessed` with reason |
| Comparison eligibility | `qualified` if support and measurement compatibility suffice for the requested statistic; otherwise `unavailable` |
| Statistic availability | Separate for median, excess consumer eligibility, ratio, MAD-derived score, and relative-width screen |
| Qualifications | Health/workload/configuration/replica equivalence unverified; source-relative instrumentation completeness; provisional units; retrospective availability; contamination/drift/boundary-selection evidence where observed |

For supported positive centers and at least 190 usable resamples, width ≤0.40×median passes the exploratory screen; greater width fails. Under 190 usable replicates is inconclusive. A zero median has no positive-center relative-width result. Unsupported references do not gain comparison eligibility by having a narrow interval. Supported unstable references can supply explicitly unstable descriptive median comparisons, never an unqualified stable-center assertion.

No initial output is “verified healthy” or “unqualified normal.” A zero raw MAD only disables the MAD-derived score. A zero center only disables the ratio and relative-width screen; with valid support it still supports median and signed excess. No arbitrary epsilon is introduced.

## Coverage and reuse invariants

- Partition each resolved query population into supported and unavailable outcomes; separately retain unresolved raw identities, duplicates/conflicts and out-of-scope roots. Exclusion reasons may overlap, so provide a deduplicated total as well as reason counts.
- Request coverage is supported/resolved requests; class coverage is supported/observed cohort incidences. Keep fixed C0/C2 strata and unknown-structure counts alongside policy-dependent cohorts. An empty denominator has an unavailable ratio.
- Report each anchor/class/replica/slice before aggregate summaries. Shared window/request occurrences and shared reference traffic are not independent cases. Missing windows remain missing.
- Baseline identity covers sources, extraction, resolved membership, time/context/replica policy and estimator/support settings. Membership identity excludes presentation order; consistent identifier renaming is compared through the declared mapping, not by expecting an unchanged literal identifier hash.
- Changes in sources, policies, members or uncertainty definitions create a new baseline version. Consumers retain the old baseline and descriptors. Reuse outside the declared 30-minute horizon is unavailable under this profile.

Research reproduction artifacts may live under a local experiment directory; a future runtime must regenerate or validate its inputs under the existing runner contract and may not depend on an author's local cache.
