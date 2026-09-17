# Feature Specification: Featherless GLM trace classification and semantic encoding

**Branch**: `008-featherless-trace-semantics` | **Created**: 2026-09-17
**Status**: Specified and planned; implementation and model experiments pending.
**Input**: Plan Featherless GLM classification and semantic encoding of non-deterministic traces, using automatic prompt-prefix caching where available.

**Decision**: [ADR 0015 — trace semantics and prefix caching](../../docs/adr/0015-featherless-trace-semantics-and-prefix-caching.md)

## Scope and interpretation

Non-deterministic traces means observed execution varies in sibling scheduling, repetition, replica bindings, timings, and incomplete evidence. It does not mean all such differences are irrelevant or anomalous. Model response variation is a separate measurement. Semantic encoding means inspectable structured evidence, not vector embeddings. Classification means scoped descriptive facets and explicitly qualified interpretations, not forced benchmark fault labels.

Extend feature 001's later A5 research and ADRs 0010–0012. Keep deterministic facts authoritative and LLM annotations separate. Preserve the incremental S01–S09 fidelity gates. The first model study remains S09's 18 calls on independently correct authored inputs; a broader variable-trace study follows only as a separately frozen slice. This request authors the plan, not an experiment run.

## User Scenarios & Testing

### User Story 1 — Preserve execution variation (P1)

As a researcher, I need equivalent structural evidence to compare consistently while meaningful changes remain inspectable.

**Why priority**: Classification is untrustworthy if the representation deletes distinctions.
**Independent test**: Independently authored equivalents and one-change contrasts.

1. Given renamed IDs and shuffled input rows, structural comparison returns equivalence while original evidence pointers remain resolvable.
2. Given changed multiplicity, replica binding, parent, or timing, the relevant fact changes; no normalization erases it.
3. Given missing parents, conflicting rows, or unknown units, the packet retains those limitations instead of repairing them.

### User Story 2 — Obtain supported classifications (P1)

As an investigator, I need every model annotation to state its scope, evidence and uncertainty.

**Why priority**: A plausible description must not become an unsupported measurement or diagnosis.
**Independent test**: Three S06 status-boundary cases in normalized and symbolic representations, repeated three times.

1. Unmapped status stays unknown; documented mapped status has the supported span interpretation.
2. A child error and independently verified enclosing success coexist without contradiction.
3. Unknown operations remain distinct, repetition does not imply retry, and model output cannot rewrite the codebook or packet.

### User Story 3 — Measure reuse and cost honestly (P2)

As an experiment owner, I need repeatable requests, bounded spending, and separate measurements for token reduction and provider prefix reuse.

**Why priority**: Cached prefill can reduce cost without making encoding smaller or classification better.
**Independent test**: Offline serialization/accounting fixtures, then a separately registered paired cache probe.

1. Changing only the case payload leaves the stable instructions, definitions and schema identical.
2. Missing provider cache usage is reported as unknown; a fast response alone never proves a cache hit.
3. Exhausted budgets, malformed output, or unavailable models preserve failed attempts and return explicit unavailability.

### Edge Cases

Concurrent/interleaved repeats; equal operation counts with different entities; ambiguous identity correspondence; clock skew; absent producer semantics; root-only traces; truncation; tool-like instructions in telemetry; conflicting mappings; model substitution; capacity errors with no choices; missing usage; cache eviction; reused run IDs; provider model aliases changing behind a stable name.

## Requirements

- **FR-001**: Preserve all contracted raw values, occurrences, edges, bindings, timing qualifications and provenance under a versioned fidelity policy; model output cannot mutate them.
- **FR-002**: Separate structural equivalence from timing/identity-sensitive comparison. Compare partial-order observations without inventing a total execution sequence or causal edge.
- **FR-003**: Every annotation must carry definition/version, semantic layer, producer, support strength, evidence scope, limitations and validation state. Unknown and conflicting are explicit outcomes.
- **FR-004**: Status mapping must be producer-scoped; span errors, request outcomes, business success and benchmark incidents stay separate. Abstention on unsupported facets is valid.
- **FR-005**: Build stable versioned prompt prefixes with volatile evidence last, deterministic serialization, and no provider cache keys or cache-control parameters. Local hashes identify audit artifacts only. Do not pad prompts to qualify for caching. Cache residency is never a correctness or budget dependency.
- **FR-006**: Each planned model call records exact input identity, model/settings, raw result or failure, usage availability, timing, validation and attempt identity. No answer memoization during repeated trials.
- **FR-007**: Use Featherless GLM models and runtime environment credentials under feature 002's endpoint contract. Bound input, output, time, concurrency and spend; never silently substitute models within a frozen experiment.
- **FR-008**: Score 18 first-study outputs individually against independently frozen expectations. Preserve errors and disagreement; fail unsupported promotions even when evidence IDs are valid.
- **FR-009**: Report bytes, actual input/output tokens, cache-token evidence, cost estimates and observed charges distinctly, including stable dictionary/schema overhead. Count failed/invalid attempts in experiment accounting. Missing cache usage remains unknown; latency alone cannot prove reuse. Admit calls against conservative uncached cost, including output and completion reserves.
- **FR-010**: Isolate development controls from later held-out deployment evaluation; keep benchmark answer files and case-specific prior diagnoses out of model input. No production diagnosis improvement claim follows from this study.

### Key Entities

EvidencePacket; EquivalencePolicy; PromptPack; ScopedMapping; Annotation; ModelAttempt; StudyManifest; ClaimAdjudication. See [data-model.md](data-model.md).

## Success Criteria

- **SC-001**: All frozen equivalence/contrast fixtures recover 100% of contracted facts and resolve every evidence pointer; zero silently discarded differences.
- **SC-002**: S09 feasibility requires all 18 outputs to preserve all required status/outcome distinctions with zero unsupported promotions. Report each format separately; failed or unavailable calls cannot count as passes.
- **SC-003**: Every attempt and expected trial is accounted for, including incomplete studies; replaying saved scoring requires no paid calls.
- **SC-004**: Offline boundary fixtures demonstrate stable prefix bytes, explicit cache-usage unknowns, and budget stops under cold/evicted-cache conditions without relying on discounts. Prefix checks must show no expected labels or previous answers in requests and no padding to reach a cache threshold. A live caching benefit is reported only with supporting provider usage or billing evidence; absent evidence is inconclusive.
- **SC-005**: Representation benefit requires equal factual fidelity and fewer measured total input tokens on matched inputs including overhead. Cache discounts alone do not satisfy it.

## Assumptions

The first model candidate is GLM-5.3-Flash, subject to availability and challenge eligibility checks at run freeze. Exact request settings and safety budgets are specified in the plan. Unsupported capability or absent model access yields not run/inconclusive. Existing S01 code is a reuse candidate; later fidelity slices are not assumed complete. All paid studies and production integration remain future execution work.

## Constitution check

Pass for design: evidence retained; query-bounded packets; GLM routing measurable; frozen controls and later unseen evaluation distinguished; unattended credentials/output compatibility preserved. Full routed-versus-single-model diagnosis evaluation remains feature 002/007's release obligation, not claimed by this research slice.
