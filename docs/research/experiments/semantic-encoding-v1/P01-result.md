# P01: semantic prompt fidelity passed; small token saving and full-request cache reuse observed

Run `20260917-p01-002`, 2026-09-17. Design checkpoint: `b83e97c` (`docs(semantics): freeze minimal prompt fidelity and cache test design`). Model: `zai-org/GLM-5.3-Flash`; temperature 0, reasoning effort low, 4,096 generated-token cap, concurrency 1. No retries, repairs, model fallback or hidden warmups.

**Decision: supported_on_fixture. All 18/18 responses passed**, nine per representation. The prompt converted normalized evidence into the frozen operation symbols and regenerated already-symbolic evidence while retaining every occurrence, identity, parent relationship, raw value, evidence assignment and explicit unknown. The independent raw-record audit recovered **1,188 raw-field values** across the responses. This remains one tiny authored structural family, not general trace understanding or proof that a model is needed for deterministic mapping.

## Measured results

| Measurement | Normalized inputs, 9 calls | Symbolic inputs, 9 calls | Total |
|---|---:|---:|---:|
| Fidelity passes | 9/9 | 9/9 | 18/18 |
| Actual input tokens, including prompt/template | 11,022 | 9,021 | 20,043 |
| Actual output tokens | 3,716 | 3,630 | 7,346 |
| Provider-reported cached input tokens | 2,401 | 2,060 | 4,461 |
| Estimated inference token cost | $0.00322318 | $0.00292095 | **$0.00614413** |
| All-fresh counterfactual token cost | $0.00351130 | $0.00316815 | $0.00667945 |

Symbolic inputs used **18.15% fewer total input tokens** than normalized inputs on the matched cases, with no contracted-fact regression. The common codebook/output schema is included in every request. This result concerns the new matched prompt projections, not the earlier cold S01 packet/source byte comparison. The symbolic arm has an easier copy path; no extra reasoning benefit follows.

Total request wall time was **88.70 seconds**; median **4.24 seconds**, range **3.16–8.78 seconds**. Non-streaming elapsed times include queueing and generation. No causal latency improvement is claimed.

Rates frozen for estimates: $0.15/M fresh input, $0.03/M cached input, $0.50/M output. The model catalogue confirmed fresh/output rates and current-plan availability; the effective model page supplied the cached rate. Source: [Featherless model page](https://featherless.ai/models/zai-org/GLM-5.3-Flash). This is an inference token-cost estimate from returned usage, **not an observed invoice/account debit**. Metadata/tokenization request charges were not reported and are not silently represented as measured zero.

## Caching finding and stop decision

The natural static prompt measures **626 tokens** using Featherless's tokenizer. Every completed chat reports 13 more input tokens than the separately tokenized system/user contents combined. Complete request inputs range from 984 to 1,273 tokens.

Featherless reported cached input in four calls:

| Trial | Cached / input tokens | Identical earlier request trials |
|---|---:|---|
| 10 | 1,030 / 1,030 | 6 |
| 12 | 1,205 / 1,205 | 1 |
| 14 | 1,030 / 1,030 | 6, 10 |
| 17 | 1,196 / 1,196 | 4, 8 |

These are **whole-request repeats**, including trace evidence. They demonstrate provider-reported input reuse on these calls; they do not establish static-pack reuse across different traces. Repeated requests did not always hit, consistent with opportunistic caching. The modeled input saving attributable to returned cache usage is **$0.00053532** over the 18 calls. Four hits in this tiny scheduled run are not a general hit-rate estimate.

**The separate six-call cache smoke was not executed.** Its natural-prefix gate fails: 626 tokens is below the roughly 1,000-token threshold documented by [Featherless](https://featherless.ai/docs/request-pricing-and-credits). No padding was added. Cross-trace prefix benefit, TTL and general latency impact remain untested.

## Execution and audit qualifications

- Frozen design inputs omit the S01 hypothesis/pass rule and use opaque case IDs. All model inputs are synthetic; no original telemetry or development answers were sent.
- Before inference, 11 offline contracts passed. A subsequent usage-adapter test brings the current suite to 12 passing tests.
- First preflight `20260917-p01-001` made no inference calls. It preserved a valid tokenizer response containing `{count, model}` instead of the older documented token-array shape. The corrected adapter and run 002 were frozen before all inference.
- The live adapter initially recognized only nested cached-token counters. Featherless returned top-level `usage.cached_tokens`. Raw responses and the original ledger/report are retained unchanged. The corrected, tested adapter produced a separate `result-audited.json`, with its code hash and post-run source snapshot. This changed usage interpretation only: no prompt, generated response, fidelity criterion or inference attempt changed.
- An independent script compared decoded raw values and evidence assignments to original source rows without using the runner scorer, and recomputed the cost arithmetic from raw usage. Source/input/request/response artifacts have SHA-256 inventory. Credential-value scans found no matches in run artifacts.
- The zero-inference deterministic route already preserves these facts. P01 validates a constrained prompt interface; it does not show that GLM improves on that route. Human annotation independence, real-trace model fidelity, status mappings, anomaly/causal labels and unseen diagnostic accuracy remain unestablished.

## Reproduction and retained evidence

From the repository root, offline only:

```sh
python3 -m unittest experiments.semantic_encoding_v1.test_p01 -v
python3 -m experiments.semantic_encoding_v1.run_p01 score --run-id 20260917-p01-002
```

- [Audited result](../../../../data/experiments/semantic-encoding-v1/P01/20260917-p01-002/result-audited.json)
- [Independent raw-field and usage audit](../../../../data/experiments/semantic-encoding-v1/P01/20260917-p01-002/independent-audit.json)
- [Frozen execution configuration](../../../../data/experiments/semantic-encoding-v1/P01/20260917-p01-002/freeze.json)
- [Preflight tokenizer measurements](../../../../data/experiments/semantic-encoding-v1/P01/20260917-p01-002/preflight.json)
- [Artifact hash inventory](../../../../data/experiments/semantic-encoding-v1/P01/20260917-p01-002/artifact-sha256.json)
- [Design and stop rules](../../../../specs/008-featherless-trace-semantics/minimal-test.md)

Generated run evidence is Git-ignored and must accompany this report for independent reproduction. Request/response bodies, initial and corrected code snapshots, all 18 attempts and metadata calls remain available locally. The pre-run design checkpoint is committed. The user subsequently requested a semantic checkpoint of the P01 execution code and result documentation; generated run artifacts remain Git-ignored.

Next smallest scientific question: S09's scoped status interpretation on its separately frozen cases, or one real-trace structural prompt transfer after reviewing the newer S02 evidence. Do not enlarge the prompt solely to chase caching. This run stops here.
