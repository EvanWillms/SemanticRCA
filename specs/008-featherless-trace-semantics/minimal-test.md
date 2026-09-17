# P01: minimal semantic tokenization prompt and cache test

Date: 2026-09-17. Design checkpoint: b83e97c. Subsequent execution: P01 completed 18/18 fidelity passes; see [results](../../docs/research/experiments/semantic-encoding-v1/P01-result.md). The protocol below preserves the pre-run design and stop rules.

## Decision and scope

Use the only validated encoding fixtures: S01's T0, identifier-renamed/reordered T1 and added-occurrence T2. Test one generic prompt on each, independently, in normalized and symbolic forms, three repetitions: **18 inference attempts**. Observe cache telemetry without adding calls. If that passes and the natural static prefix qualifies, a **separate six-attempt cache smoke** tests prefix reuse with changed case evidence. Maximum across the two studies: 24; the cache probe is conditional, not mandatory.

This explicitly changes feature 008's immediate priority from status-boundary S09 to structural P01 for the current user request. S09 remains a distinct, deferred 18-attempt study; its fixtures and acceptance rules are unchanged. P01 is not renamed S09 and does not validate producer mappings, real telemetry or general non-deterministic graphs. ADRs 0012 and 0015 record the priority amendment.

## What the prompt must do

Convert known recorded operations to the frozen C/D/P/R vocabulary, retain every occurrence and its original entity/parent/raw values/evidence, and preserve unknown interpretations. The output is a compact symbolic packet. This tests constrained semantic transcoding, not vector embedding or a promise that one code equals one model token.

[structural-v1.txt](prompts/structural-v1.txt) is the complete candidate system message. It is newly authored from S01's dictionary and ADR boundaries, not a modification of a supplied canonical prompt. Both input arms use the exact same message and output schema. The user message is compact JSON from one of the six [design fixtures](design-fixtures/p01/evaluation-manifest.json); that manifest itself is evaluator-only.

The symbolic arm is a regeneration control and has an easier copy path than normalized-to-symbolic conversion. Do not interpret an arm advantage as general semantic understanding. The deterministic serializer is the zero-inference baseline. GLM usefulness beyond that baseline is unproven even if all outputs pass.

## Inputs and leakage control

Neutral packet IDs q7/q2/q9 map to T0/T1/T2 only in the evaluation manifest. Build both arms from the original authored fixture records, not saved packets containing `policy.pass_rule`. Every source row's nine raw fields survive: trace ID is shared at packet level; span, parent, operation, entity, timestamp, duration, type and status are retained per occurrence or via explicit reversible dictionaries. Blank parent becomes null under the declared root-marker mapping. Preserve context and units in both arms.

Normalized records name operations and entities. Symbolic records use tuples and explicit entity aliases. A common static codebook defines both formats. No counts, expected differences, experiment narratives, answer labels, source filenames revealing variants or prior outputs enter requests. Opaque evidence IDs retain a reversible source-row map in the evaluator. Model-generated IDs or raw values are never accepted as replacement ground truth.

The six concrete JSON inputs and fixed 18-slot schedule are in [evaluation-manifest.json](design-fixtures/p01/evaluation-manifest.json), with source/input/prompt hashes. Expected structural facts originate in S01's pre-existing authored fact sheet; expected raw fields come from the original fixtures, separately from the prompt projection. Do not use the candidate model or projection output to generate its own expected result. Independence remains authored expectations with review, not independent human validation.

## Zero-call readiness gate

Before model execution:

1. Verify hashes and independently decode both representations to original records; require exact equality on all nine raw fields and context. Compare source IDs, evidence-row assignments, entity distinctions and all occurrences.
2. Check prompts and payloads for answer leakage. The builder may read only the prompt and selected input JSON, never evaluation metadata, expected facts, saved S01 policies or prior responses.
3. Exercise scorer negative controls offline: constant T0 response for all cases; missing added occurrence; changed entity with unchanged counts; wrong parent; invented evidence ID; unknown promoted to success; invalid JSON. Every corrupted result must fail. These are authored validator tests, not simulated model outcomes.
4. Resolve the selected-model tokenizer/chat-template accounting and record static prefix, each payload and total input tokens separately. No character-to-token estimate counts as measurement. If unavailable, mark token metrics unavailable and use a justified conservative admission bound; skip the cache probe. Account separately for any future provider tokenization/capability requests.

The design-fixture audit checks point 1 and leakage-related input structure; it is not a completed model runner/scorer test suite.

## P01 execution

Model candidate: `zai-org/GLM-5.3-Flash`, subject to frozen availability/eligibility and capability evidence. Temperature 0, reasoning effort low, non-streaming, one request at a time, no tools/history. Fix settings before observing responses. Unexpected model identity is a failed trial, not an automatic fallback.

Use the manifest's rotated case order and alternating format order. Each of six case-format cells receives three repetitions. Fresh conversations; no local answer cache; no warmups, repair calls or automatic retries. Every started attempt remains in the ledger. Leave skipped trials visible after admission/run failure. A model revision or prompt fix starts a new study identity, preserving old attempts.

P01 limits: 18 attempts, 8,192 input tokens, 4,096 total generated-token allowance per attempt, 60-second request timeout, 20-minute run deadline, 30-second persistence reserve, $1 conservative uncached estimate ceiling. The higher output allowance than the earlier S09 sketch accommodates occurrence-level output and reasoning; actual provider semantics must be checked at freeze. A truncated response fails; it is not silently repaired. No credential values are written to artifacts.

At planning rates F=$0.15/M and R=$0.50/M, this token ceiling estimates $0.0032768 per attempt, $0.0589824 for 18 or $0.0786432 for 24 including the probe, before account-specific differences. These are hypothetical uncached estimates, not quotes or charges; freeze effective rates before execution. Cost output includes billable reasoning without double counting.

## Scoring and falsifiers

Score all 18 outputs against the same contract:

- Exact syntax/schema, IDs, raw strings, trace context, every occurrence and evidence assignment.
- Codebook decoding reproduces all original operation/entity identities and recorded parent edges.
- Offline graph comparison of q7/q2 is equivalent under S01's declared structural projection. q9 differs by the one independently specified catalog occurrence and edge; all prior facts survive. Do not tell the model either relationship.
- Raw statuses and the five unknown interpretation fields remain unchanged. Reject unsupported extra labels/claims even if the JSON or pointers otherwise look valid.

Expected diagnostic counts, kept out of prompts: spans 7/7/8; edges 6/6/7; catalog occurrences 3/3/4. Exact per-node comparisons catch identity/parent errors that counts cannot.

Feasibility passes only when every required fact in every trial passes; report each arm and all failures. A wrong mapping or unsupported promotion falsifies fidelity on that fixture. Missing access/transport prevents a complete feasibility claim. Compare semantic content across repetitions, not output order/whitespace. Three repeats are a smoke test, not a deployment reliability estimate.

Report actual total input tokens for N versus S at equal fidelity, including the common prompt/codebook. Separately report output tokens, end-to-end latency and total estimated/observed cost. Input-token reduction is supported only when the symbolic requests are smaller on matched cases without fidelity loss; caching discounts do not count as compression. Neither a byte win nor a smaller generated response proves improved input tokenization.

## Conditional cache smoke: six calls

Proceed as a separately frozen study only after P01 fidelity passes, the unchanged natural static prefix is roughly 1,000+ actual tokens, and cache counters or attributable billing can support the question. If the prompt is too short, the minimal result is **not eligible for this cache test**; do not pad it. If telemetry is absent, record caching inconclusive and avoid spending extra calls just to infer hits from timing. Observational P01 usage may show full-request reuse, which must be labeled separately.

Use one representation throughout (symbolic if it passes), the same system pack/model/settings and two cases A=q7 and B=q9. Prefix each system message with an explicitly inert probe tag. Match tag token lengths using the verified tokenizer; all tags unique except the within-block shared pair. Keep the tag short; it separates controls, not pads the pack. Serialize the user message beginning with packet_id, so A/B suffixes diverge immediately; ordinary sorted JSON could otherwise share a long context/entity preamble. Freeze this probe-specific serialization and include its size overhead.

| Block | Call 1 | Call 2 | Call 3 | Paired target comparison |
|---|---|---|---|---|
| 1 | shared-tag-1 + pack + A | shared-tag-1 + pack + B | unique-control-1 + pack + B | call 2 vs call 3 |
| 2 | unique-control-2 + pack + B | shared-tag-2 + pack + A | shared-tag-2 + pack + B | call 3 vs call 1 |

The seed directly precedes the shared target. All six calls count, including seeds. Record actual delays; do not assume residency. Seed and target differ in evidence, preventing exact full-request replay. Shared/control targets within each pair contain identical B evidence. Unique early tags create nominally fresh prefixes, not a guaranteed cold server. Fixed template tokens may still match; measure what was cached.

Require P01 scoring on all six outputs as well. If either target pair differs in factual validity, report the quality difference and do not claim an equal-quality saving. Report the two paired measurements individually; no significance test, stable hit-rate claim, TTL estimate or general latency speedup from two blocks.

For input P, reported cached input H, output O and frozen per-million rates F/C/R:

`estimate = ((P-H)*F + H*C + O*R)/1e6`

Report H/P and cache-only modeled input savings `H*(F-C)/1e6` per call, using actual P differences. Pairwise cache-only differences isolate the accounting contribution of reuse; full cost differences also include output length. Observed provider charges are separate. Validate H within [0,P]; absent H is null and prevents a cache-only claim unless attributable billing independently supports it. Latency includes queueing/prefill/generation and is not TTFT. Count seeds in the total study cost; do not hide the cost of populating a prefix.

## Outputs and next action

Preserve exact requests, raw responses, usage extensions, model identities/settings, all timestamps/statuses, source/prompt/input hashes, schedule, offline scoring and claim adjudication. Emit separate verdicts for prompt fidelity, representation tokens and prefix reuse. Results stay under new immutable P01 or cache-smoke run IDs; no S01 artifact is overwritten.

Stop after P01 adjudication; the separately scoped cache smoke is the one conditional follow-up designed here. S09 status semantics, real-trace fidelity and general behavioral labels remain subsequent studies. This request designs the tests and artifacts; it does not dispatch inference.

Constitution 1.0.3 check: deterministic preparation retained; model transformation is an isolated experiment; no authoritative fact replacement; bounded inputs/budgets; credentials and submission interfaces unchanged; failures and exposure explicit. Experimental feasibility cannot substitute for unseen diagnostic evaluation.
