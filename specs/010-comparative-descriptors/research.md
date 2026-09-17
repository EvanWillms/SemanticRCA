# Phase 0 research: Comparative descriptors

Research completed 2026-09-17 through local source review and two bounded planning investigators. The [feature 009 research](../009-qualified-short-baselines/research.md) resolves the shared Python, arithmetic, preparation and source-identity choices. No experiment execution or diagnosis evaluation was performed.

## 1. A pure consumer with an explicit dependency

**Decision**: Implement `rca.comparisons` as a Python 3.12 standard-library consumer of feature 009 observations, assignments, C1 baselines and C0 structural populations. Membership is read-only. Keep descriptor construction, evidence validation, review views and artifact serialization as separate concerns.

**Rationale**: [compare_traces](../../rca/telemetry/traces.py) currently combines collection-derived context, selection, count-only support, arithmetic, structural comparisons and candidate ranking. It lacks the new support/stability states. [research compare_duration](../../experiments/short_window_baselining_v1/contracts.py) provides arithmetic examples but is neither support-aware nor a complete descriptor API.

**Alternatives considered**: Reusing the existing combined function would let a descriptor consumer select its own baseline. An LLM/codebook-dependent descriptor would make deterministic acceptance depend on unrelated semantic labeling.

## 2. Field availability and lossless outcomes

**Decision**: Use typed per-field availability, explicit numerical definition IDs and mandatory qualifications. Every resolved query occurrence yields one descriptor envelope containing duration and structural subresults. Nonpositive and unavailable outcomes remain in the complete artifact. Optional ratio/MAD diagnostics are off by default.

**Rationale**: The [research runner](../../experiments/short_window_baselining_v1/runner.py) returns no duration comparison rows for unsupported cohorts. Its null/undefined diagnostics also do not distinguish all feature 010 availability states. The new [semantic contract](contracts/descriptors.md) requires these distinctions.

**Alternatives considered**: A nullable score alone hides whether a field is undefined, unsupported or not requested. One record per numeric field makes request coverage harder to reconcile. A top-five-only artifact loses the denominator.

## 3. C0 structure without inventing expectations

**Decision**: Consume per-C0 structural populations with member identities, known-structure denominator, unknown count and exact multiset frequencies. Emit deltas against each identified reference pattern, retaining a match count and finite-reference-absence statement. Use evidence references or explicit pages when a pattern list is large; never silently truncate it.

**Rationale**: Current code contains useful `Counter` differences, but the research structural output lacks the required per-C0 known denominator and per-pattern member evidence, and can mix unknown signatures with known patterns. C1 conditions away operation-set changes; a separate population is necessary.

**Alternatives considered**: Selecting only the modal pattern would imply an expected route. Matching on C2 would hide the count changes this feature must expose. Using C1 support for structural eligibility would wrongly suppress unmatched queries.

## 4. Evidence verification and stable revisions

**Decision**: Verify artifact integrity, scoped entity, source snapshot, record locator, measurement selector, normalization and statistic definition. Resolve CSV locators to logical records; support a tagged JSON-array-member locator where the declared source representation uses arrays. The initial frontend adapter uses CSV. Recompute baseline statistics once per distinct validated baseline; cache that validation within the snapshot handle.

**Rationale**: The [research reconciliation](../../experiments/short_window_baselining_v1/replay_reconciliation.py) samples identity/file/record against an index. It does not establish the complete duration, digest, statistic and normalization validation required by D11. The [general comparison contract](../003-contextual-telemetry-evidence/contracts/baselining.md) already requires exact evidence and versions.

**Alternatives considered**: Pointer syntax checks accept wrong-but-resolvable measurements. Hash-only validation can preserve internally consistent but semantically wrong artifacts. Rescanning all source records per descriptor wastes shared work.

## 5. Views, aggregation and integration

**Decision**: Keep complete descriptors separate from a top-five positive-excess view. Use the exact scoped-identity tie-break from the semantic contract; top-five lists are scoped to one baseline-set snapshot and query slice. Do not combine different units or snapshots in one rank. Count unique observations, occurrences, fields and reference cohorts separately.

Provide a versioned findings adapter for a future explicit discovery profile, with references to full descriptors. Keep original diagnostic predictions and incident count outside the descriptor API. Metric discovery remains independent.

**Rationale**: Current [discovery pipeline](../../rca/discovery/pipeline.py) merges trace/metric findings and has its own ranking policy. An adapter must expose the new policy rather than silently treating it as `track1-discovery-v1`.

**Alternatives considered**: Fusing scores across families would imply comparability absent from the study. Forcing the number of descriptors to match requested failures would discard observations before diagnosis.

## 6. Independent validation and deployment

**Decision**: Use authored D01–D12 fixtures with independently calculated expected values; add a joint feature 009→010 fixture and corruption/round-trip checks. Run locally and in the existing Python 3.12 container without network/model credentials. Provide an offline CLI consuming the baseline bundle and caller-supplied dataset root, with a separate validator.

**Rationale**: The existing standard-library runtime is sufficient. Tests must establish arithmetic, availability and evidence fidelity before optional source-snapshot regression. The CLI is a developer validation interface; it adds no required flags or preparation step to the official runner.

**Alternatives considered**: The earlier investigation's diagnostic correctness is not an acceptance target for this feature. Copying the producer's output as the expected fixture would only prove self-consistency.

All planning unknowns are resolved. Feature 009's output contract is the integration dependency; mocks can exercise pure comparisons, but cannot substitute for the required joint acceptance run.
