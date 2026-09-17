# Implementation Plan: Featherless GLM trace semantics

**Branch**: `008-featherless-trace-semantics` | **Date**: 2026-09-17
**Spec**: [spec.md](spec.md) | **Status**: Planning complete; implementation and experiments pending.

**Decision**: [ADR 0015](../../docs/adr/0015-featherless-trace-semantics-and-prefix-caching.md)

## Summary

Build a deterministic evidence layer with a separate GLM annotation layer. Exploit common prompt prefixes opportunistically; measure encoding fidelity, classification quality, model variation and caching separately. Start with the existing S09 status-boundary study, using correct authored packets. Advance to variable-trace classification only after its smallest prerequisites pass.

```text
bounded trace records → deterministic facts → lossless evidence packet
                                                ↓
versioned definitions + output contract + per-case evidence → Featherless GLM
                                                ↓
                                     validated annotation sidecar
                                                ↓
                              independent adjudication + attempt ledger
```

## Technical Context

- **Language/platform**: Python 3.11-compatible standard library; local CLI and Linux, consistent with the existing experiment style.
- **Dependencies**: JSON/hashlib/unittest/urllib; Featherless chat completions. No embeddings, agent framework or new database.
- **Storage**: source-controlled fixtures/prompt definitions; immutable Git-ignored JSON/JSONL run artifacts under `data/experiments/semantic-encoding-v1/`; compact research summaries under `docs/research/experiments/semantic-encoding-v1/`.
- **Testing**: offline contracts and synthetic counterexamples; separately authorized real S09 calls and independent claim adjudication.
- **Scope**: one frozen GLM model, 3 cases × 2 representations × 3 repetitions. Later trace-variation and caching studies are separately registered.
- **Proposed S09 limits**: concurrency 1; 18 attempts total; no automatic retries/repair calls; 8,192 input tokens and 2,048 total generated-token allowance per attempt; 60-second timeout; 20-minute run deadline; $1 uncached estimated-spend ceiling. Reserve 30 seconds for artifact persistence. These are experiment defaults, not provider limits or measured performance.
- **Constraints**: `FEATHERLESS_API_KEY` only for credentials; honor `FEATHERLESS_BASE_URL`; GLM-only model selection. Check official challenge constraints before claiming submission eligibility. Runtime run freeze must lower limits if the applicable account or challenge imposes tighter bounds.

## Evidence and non-determinism

| Variation | Preserved facts | Comparison rule |
|---|---|---|
| ID renaming / input row order | Original IDs and provenance | Structural view may ignore opaque IDs and serialization order |
| Sibling scheduling | Starts, qualified intervals, observed relationships | No total order inferred from file order; supported overlap remains a distinct timing fact |
| Repetition / fan-out | Every occurrence, edge, binding and exact count | Grouping never deletes count/outliers; repeat is not retry |
| Replica substitution | Actual entity IDs and equality/distinctness | Role-pattern comparison is explicit and cannot replace exact-identity comparison |
| Clock / duration ambiguity | Raw strings, units, emitter qualification | Signed start offsets when supported; endpoints unavailable with unknown duration units |
| Missing/conflicting observations | Both records, unresolved references and coverage | No silent repair, winner selection, or absence claim from missing instrumentation |

Do not claim traces match in all respects when only their structural projections match. Freeze the equivalence policy with every comparison. An observed alternative path is descriptive; deciding it is allowed or anomalous requires the qualified cohort owned by feature 003. Mechanism interpretations require additional evidence and remain separate from fault diagnosis in feature 007.

## Classification contract

S09 returns raw status, mapping support, scoped span interpretation, independently supported enclosing outcome, evidence IDs and limitations. Values include unknown/conflicting, with no default healthy class. Follow ADR 0011's producer-specific applicability predicates.

The later vocabulary is faceted: temporal form, mechanism hypothesis, participant/relation, outcome, evidence strength. Each facet has a definition/version and can abstain independently. Code computes counts/timing; GLM may describe facts or propose interpretations. Unsupported mechanism proposals cannot become validated observations. Model confidence is not a calibrated probability. Organizer fault reasons do not enter the encoding prompt.

## Prefix construction

One stateless request per trial:

```text
SYSTEM: immutable task instructions, evidence boundaries, output schema,
        shared codebook/definitions and scoped mapping applicability rules
USER:   representation tag, current evidence packet and available context
```

Use a single frozen UTF-8 serialization: fixed section order, sorted object keys, stable whitespace/newlines, explicit array-order policy. Store exact strings and hashes. Include both representation definitions in the same pack so the arms have equal interpretive information. Include no expected labels, previous answers or case narrative. Telemetry text is quoted data, never instructions.

No tools are needed for S09. If a later consumer adds tools, freeze their schema and order and account for their overhead. Keep case IDs, timestamps, source pointers and volatile context in the suffix when needed; run/attempt metadata normally belongs only in the ledger. Local hashes are audit identities, not provider cache keys. Never send `cache_control` or invented cache parameters.

A prefix below roughly 1,000 tokens may not qualify: report that result and do not pad. Identical client bytes are a necessary reproducibility check, not proof of identical server tokenization or cache hits. Every call still generates a new answer; provider prefix reuse does not defeat isolated conversations.

## Model and runtime behavior

Provisional first candidate: `zai-org/GLM-5.3-Flash`, temperature 0, reasoning effort low, fixed output budget. Record requested and returned model IDs, any provider revision/fingerprint, settings and capability evidence. If revision is unavailable, record that reproducibility limit. Temperature 0 and seeds do not guarantee identical output.

Use JSON text plus strict local validation as the baseline. Do not require undocumented constrained-output support. A truncated, malformed, empty or semantically invalid response is retained as a failed trial. No automatic repair or stronger-model fallback inside S09. Reject non-GLM models and unexpected returned identities; retain their responses for audit without grading as the frozen model.

HTTP/timeouts/capacity failures, auth errors and missing usage get typed states. Persist an attempt-start record before sending. On ambiguous timeout, conservatively reserve the entire attempt's input/output allowance; never quietly replay it. Resuming preserves completed attempts and marks interrupted calls uncertain. Missing credentials do not produce synthetic model results.

## Cost and cache accounting

Let P be total input, H provider-reported cached input, O billed output; rates F/C/R are fresh/cached/output per million:

`estimated_cost = ((P - H) * F + H * C + O * R) / 1_000_000`

Validate `0 <= H <= P`. Missing H is null: report the all-fresh upper estimate and, if useful, a clearly hypothetical cached lower estimate. Never label the upper estimate an observed charge. Missing P/O prevents exact accounting; retain a conservative budget reservation. Retain raw usage and reasoning-token fields without double counting reasoning already included in completion usage. Record the account's effective rate source/date separately from challenge-scoring rates.

Illustration at $0.15 fresh/$0.03 cached: 52K fresh input costs $0.0078; 50K cached plus 2K fresh costs $0.0018, a 76.9% input-cost reduction. Output is additional, and 50K cache reuse is an assumption. At planning output rate $0.50/M, an 8,192-input/2,048-output attempt has a $0.0022528 uncached token-cost ceiling; 18 total $0.0405504 before any account-specific differences. Verify rates before execution rather than spending against this illustration.

Use conservative tokenizer bounds for admission until exact provider/template token counts are available. For tiny authored fixtures, an input UTF-8 byte count plus explicit template reserve may be used only as a documented upper-bound admission heuristic, never reported as actual tokens; if the bound cannot be justified for the selected tokenizer, block live admission until tokenization is available. Extra tokenize/capability traffic must be recorded separately and never hidden in the 18 inference calls.

Within S09, record caching observationally only. No warmup, cache-busting, extra trials or batching. Cache-hit rate requires provider token/billing evidence. Non-streaming wall time is end-to-end latency, not time-to-first-token.

After S09, a separately frozen optional 12-call cache probe may compare three blocks of four calls: shared-prefix first/repeat and matched-length unique-prefix controls, with block order counterbalanced. Use an inert fixed-length block tag near the beginning solely for this probe, semantically identical instructions and equivalent suffix sizes. First-use is only nominally cold; token-prefix overlap and server residency are not controllable. Keep classification scores and request size matched, count every call, use the same budget guards, and report observed warm/control results rather than causal infrastructure claims. If cache counters/billing evidence are absent, report latency distributions with cache effectiveness inconclusive. This probe is a later study, not added to the initial 18 calls.

## Implementation sequence and acceptance

1. **Freeze inputs and boundaries.** Author three S06 cases: unmapped `14`; mapped child `14`; same mapping plus independent enclosing success. Make normalized and symbolic forms equal-information. Freeze expected facts separately from prompts and record annotator independence/exposure. Do not include S06's fourth non-error control as an extra S09 case.
2. **Build offline infrastructure.** Add prompt builder, narrow transport boundary, output validator and immutable attempt ledger. Test no credential logging, model mismatch, unknown usage, invalid JSON, timeouts, budget refusal, and restart behavior. Replay scoring without network.
3. **Run isolated S09 when executing this plan.** Exactly 18 frozen attempts with fresh conversation contexts. Alternate normalized/symbolic order by case and repetition, yielding nine trials per arm. No answer cache, cherry-picking, repair calls or model substitution. If preflight fails, record not run. Failures remain visible and can make the study incomplete/inconclusive.
4. **Adjudicate and stop.** Score schema validity, reference resolution and factual entailment separately. All required distinctions must pass in all trials for feasibility. Compare semantic labels/evidence sets across repetitions, not prose identity. Report denominators, each arm, actual token totals and cost uncertainty. Do not infer deployment accuracy or calibrated reliability from 18 calls.
5. **Choose one next study based on results.** If the error boundary passes, freeze one operation-description or edge-timing question from the ADR handoff; alternatively choose the separate cache probe. Do not launch all studies automatically.
6. **Later integration.** Complete relevant S02–S08 fidelity gates before consuming real encoder output. Add one-change variability fixtures and held-out families/deployments, with splits grouped by trace/window/template to prevent leakage. Compare code-only, single-model and explicit cheap/strong routing at matched information. Route on validator failure or supported ambiguity, not confidence alone; each fallback costs a separate recorded call. Only independently qualified improvements may enter feature 002/007.

## Constitution Check

Pre-design and post-design: PASS for this bounded research plan. Evidence/provenance and unknowns preserved (I); bounded packets and separate retrieval (II); GLM-only measured costs, conservative limits (III); frozen matched comparisons, failures retained and later unseen evaluation distinguished (IV); environment credentials, portable artifacts and final submission boundaries retained (V). No claimed improvement or production readiness. No exception required.

## Project Structure

Documentation in this feature: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/annotation-study.md`, `quickstart.md`, `checklists/requirements.md`. Dependency-ordered `tasks.md` belongs to the next Spec Kit command.

Proposed new modules under `experiments/semantic_encoding_v1/`: `prompt_pack.py`, `featherless.py`, `annotations.py`, `run_s09.py`, `score_s09.py`, `test_s09.py`, `fixtures/s09/`. Reuse canonical JSON/hash and run-artifact conventions where contracts fit. Keep the S01 codec restricted; do not broaden its contract incidentally. No changes to `agents/submission.py`, `rca/outputs.py` or previous run artifacts in this phase.
