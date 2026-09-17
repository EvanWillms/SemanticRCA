# Research and design decisions

Date: 2026-09-17. Documentation research only; no inference requests executed.

## Provider facts and operational unknowns

Featherless documents automatic cached pricing for recently served exact prompt prefixes of roughly 1,000+ tokens, without cache parameters. It gives no residency guarantee here. Its current pricing guide lists GLM-4.7 Flash at $0.0653/$0.0131/$0.40 and the GLM5 Next class at $0.15/$0.03/$0.50 per million fresh/cached/output tokens. The guide's GLM-5.3 example is $1.40/$0.26/$4.40. These are planning references, not a frozen effective model quote. [Developer pricing](https://featherless.ai/docs/request-pricing-and-credits).

The GLM-5.3-Flash release documents the exact ID `zai-org/GLM-5.3-Flash`, 256K served context and `reasoning_effort` values low/high/max, default max. Choose low provisionally for bounded annotation. Recheck the exact model page, account context limit, effective rates and challenge eligibility before freezing a run. [Release](https://webflowcms.featherless.ai/blog/glm-5-3-flash-is-live-on-featherless), [model page](https://featherless.ai/models/zai-org/GLM-5.3-Flash).

The completion API documents messages, output caps, temperature and total prompt/completion usage. It explicitly warns seeds are unreliable across servers. The inspected response schema does not guarantee cached-token details or constrained JSON output. Preserve raw usage extensions when present, validate output locally, and treat missing cache telemetry as unknown. [Completion API](https://featherless.ai/docs/completions).

## Decisions

| Decision | Rationale | Alternative considered |
|---|---|---|
| Code preserves facts; GLM emits sidecar annotations | ADRs 0010–0011 prevent inference from overwriting evidence | LLM-only extraction obscures loss and unsupported inference |
| Explicit equivalence projections | Scheduling order, timestamps and replicas have different relevance | Sorting everything or dropping volatile values would erase meaningful differences |
| Isolated S09 first | It tests one boundary with 18 calls even before integrated fidelity is established | Full 126-call taxonomy matrix is deferred by ADR 0012 |
| Stable prompt pack, volatile case last | Improves potential prefix reuse while keeping trials independent | Growing cross-case history leaks previous model answers |
| No padding for caching | Tiny study should measure its natural workload | Artificially adding tokens can increase total cost |
| No local answer reuse during trials | Repeat variation remains observable | Response memoization would make agreement meaningless |
| One model per frozen study | Avoids confounding representation and model changes | Routing belongs in a later matched comparison |
| Narrow standard-library HTTP transport | No existing inference adapter exists in inspected code | Importing an agent framework expands the experiment boundary |
| Cache savings secondary to uncached budgets | Residency/telemetry unknowns cannot block safe completion | Assuming 80% cache hits understates worst-case spend |

## Repository grounding

`experiments/semantic_encoding_v1/codec.py` offers `compact()` and `digest()` patterns, not a general encoder. It requires dictionary-known operations, unique IDs, resolved parents and one rooted tree. Keep S01 fixtures/contracts stable. Later adapters must explicitly support unknown operations, unresolved graphs and conflicts before integrated use.

`run_s01.py` provides immutable run IDs, hashes, frozen inputs, provenance auditing and first-difference reports. Reuse these conventions in sibling S09 modules. The final `agents/submission.py` is still a stub; `rca/outputs.py` owns submission usage/output shape. This feature does not modify either.

Research review independently checked reuse seams and ADR constraints. Source expectations and model-output adjudication still require their own independence records at execution time.

## Resolved planning uncertainties

The plan treats non-determinism as both execution variation (retained facts) and separately model variation (repeated trials). It selects structured encoding, descriptive facets, no embedding service, and no forced fault taxonomy. Provider TTL, effective account price, supported JSON mode and cache counters remain runtime capabilities to record or conservatively bypass, not unresolved design choices. Model availability is a run prerequisite; an unavailable candidate yields not run, never an unregistered model substitution.
