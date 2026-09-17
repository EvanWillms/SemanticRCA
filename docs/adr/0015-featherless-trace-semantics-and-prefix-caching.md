---
status: accepted
date: 2026-09-17
---

# Separate trace facts from GLM annotations and reuse stable prompt prefixes

## Context

Trace executions can vary in scheduling, repetition, replica bindings and timing. Evidence may also be missing or contradictory. These differences must remain inspectable even when a structural comparison ignores incidental identifiers or input row order. Model response variability is a separate phenomenon.

[ADR 0010](0010-faceted-semantic-labeling.md) separates label meaning, production method and support. [ADR 0011](0011-scoped-error-interpretation.md) scopes status interpretation, and [ADR 0012](0012-incremental-semantic-validation.md) requires bounded validation. This decision specializes those boundaries for Featherless GLM requests and their accounting.

Featherless documents automatic cached-input pricing for recently served exact prompt prefixes of roughly 1,000+ tokens, without cache parameters. This reuses prefix computation, not a previously generated answer. The inspected documentation does not promise a cache TTL or a cached-token field in every response. Provider capabilities and rates remain versioned run inputs, not architectural constants. Sources were inspected on 2026-09-17: [pricing and caching](https://featherless.ai/docs/request-pricing-and-credits), [completion API](https://featherless.ai/docs/completions), and [GLM-5.3-Flash release](https://webflowcms.featherless.ai/blog/glm-5-3-flash-is-live-on-featherless).

## Decision

1. **Preserve facts deterministically.** Encoding retains contracted occurrences, counts, recorded relationships, entity bindings, raw statuses, timing qualifications, provenance and quality limits. Structural equivalence is a declared projection; it cannot erase timing or identity distinctions from the underlying packet. Do not infer a total execution order from file order or label ordinary variation anomalous without a qualified reference.
2. **Keep model annotations separate.** GLM may describe supplied facts and propose explicitly qualified interpretations. Every claim carries scope, definition/version, producer, support strength, evidence references, limitations and validation state. Unknown and conflicting remain explicit. A model cannot rewrite measurements or codebooks. Repetition alone is not retry; a child error does not establish request failure; descriptive classes do not become benchmark fault reasons.
3. **Use a stable prompt pack.** Place immutable instructions, output schema and versioned definitions first, followed by current evidence and volatile context. Freeze section/schema order and serialization. Keep run metadata outside prompts unless it is needed as evidence. No cache-control parameters or provider cache keys are sent; local hashes identify audit artifacts only. Do not pad small prompts to reach a cache threshold.
4. **Keep experiments independent.** Each S09 trial starts a fresh conversation containing the same applicable definitions and its own evidence. Previous answers and expected labels are excluded. Provider prefix reuse is allowed, but local answer memoization is disabled during repeated trials. Exact settings and requested/returned model identity are recorded; deterministic settings do not guarantee deterministic generations.
5. **Measure benefits separately.** Encoding size, classification fidelity, generation variation and cached-input savings are distinct claims. Include dictionary/schema overhead in actual input-token comparisons. Report provider cache counters when supplied; absent counters are unknown, not zero. Latency alone does not establish a cache hit. Distinguish estimated costs from observed charges and include all attempts and billable output, without double counting reasoning tokens.
6. **Budget without assumed cache hits.** Admit requests against conservative uncached costs, bounded input/output, time and concurrency, with completion reserves. Freeze effective model rates and capability evidence. Cache eviction must not affect correctness or budget compliance. Preserve malformed, truncated, failed and uncertain attempts; do not hide repair or fallback calls.
7. **Start with the bounded S09 study.** Use one frozen GLM candidate, three status-boundary cases, two equal-information formats and three repetitions: 18 attempts. No hidden warmups, automatic repairs or model substitutions. Independently adjudicate factual entailment and evidence references, then stop and choose the next smallest question. A deliberate cache probe or model-routing comparison requires a separate frozen study.
8. **Qualify integration.** Independently correct authored packets permit isolated S09 before all encoder slices pass, but do not establish connected-pipeline fidelity. Integrating real variable traces requires the applicable S02–S08 gates. Production diagnosis retains features 002/007's output, fallback, budget and evaluation obligations; S09 abstention/failure behavior does not replace the final runner's best-guess contract.

## Alternatives and consequences

LLM-only encoding conflates extraction errors and unsupported interpretation. A single normalized sequence loses concurrency and occurrence distinctions. Growing cross-case histories contaminate repeated trials with prior answers. Answer memoization hides model variation. Padding prompts or assuming cached discounts can make nominal efficiency misleading. Those approaches are rejected for this study.

A structured evidence packet plus annotation sidecar costs metadata and may not compress small fixtures. It makes errors inspectable and keeps a negative result useful. GLM-5.3-Flash is the provisional first candidate, subject to availability and challenge eligibility at run freeze; this ADR does not permanently pin a model or price. Embeddings, broad automatic behavior discovery and forced diagnostic classification remain outside scope.

## Acceptance and ownership

[Feature 008](../../specs/008-featherless-trace-semantics/spec.md) owns the requirements and [plan](../../specs/008-featherless-trace-semantics/plan.md). Its acceptance requires exact contracted-fact recovery, all 18 first-study outputs preserving the status/outcome boundaries for feasibility, complete attempt accounting, and no unsupported promotions. A token benefit requires equal fidelity and lower measured total input tokens; cache discounts cannot substitute. Missing cache evidence makes the caching claim inconclusive.

[Feature 001](../../specs/001-candidate-recall-experiment/spec.md) retains representation/equivalence authority. [Feature 002](../../specs/002-final-demo-runner/spec.md) owns final provider/runtime accounting and release; [feature 007](../../specs/007-evidence-backed-diagnosis/spec.md) owns diagnostic consumption and incident answers.

Constitution check: evidence and uncertainty preserved; packets bounded; GLM cost/routing measurable; frozen research controls separated from unseen evaluation; credentials and submission interfaces retained. Accepted status records the design decision, not implemented functionality, successful model experiments or validated cache savings.
