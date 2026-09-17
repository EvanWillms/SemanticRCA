# Research and decisions

## Authority and current state

Read the local official repository at revision `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`: `track-1/docs/{submission,models,scoring,data}.md`, `track-1/starter/run.py`, `track-1/starter/Dockerfile`, and `track-1/starter/agents/routed.py`. The participant agreement governs conflicts; do not infer scoring weights beyond checked official documents. These supplied local materials are the source of the frozen challenge contract, not live provider guarantees.

The working SymbolicRCA repository contains research, a frontend experiment coordinator, and experiment 001 specifications, but no root submission entry point/Dockerfile/README/REPORT/eval harness. Existing modified and untracked work is preserved.

## Decisions

1. **Official CLI with root Dockerfile.** Track-specific submission rules require this despite the generic compose option. Preserve starter interfaces and retain agents.heuristic as a shim to the final agent: judging uses that default and the official validator explicitly selects it. Rejected: dashboard, notebook, custom launch flags, runtime dependence on neighboring checkout.
2. **Deterministic output projection.** `run.py:format_prediction` omits unrequested keys; scoring is regex-sensitive to key order. Keep datetime/component/reason relative order, exact failure count, exact strings, UTC+8; chronological incidents satisfy submission guidance even though scoring tries permutations. Rejected: model-authored final CSV or always emitting all three fields.
3. **Bounded GLM routing.** Cheap and strong tier preference lists are frozen configuration; provider availability remains a runtime concern. HTTP 200 can contain an error and no choices. Retry/fallback must fit both case and total budget. Rejected: treating HTTP status alone as success, unlimited retries, non-GLM fallback.
4. **Same pipeline for fixed-model comparison.** Pin all model calls to one model for the ablation, leaving retrieval/prompts unchanged. Record provider failures and deterministic fallback. Rejected: comparing different algorithms or quietly routing the nominal single-model condition.
5. **Telemetry-grounded degradation.** Return legal best guesses even on failure, with explicit missing evidence. Render prose from structured provenance. Rejected: blank abstention, invented measurements, stock ruled-out claims.
6. **Budget-aware sequential cases.** Respect query order; start with sequential cases and bounded workers, avoiding complex parallel request scheduling under two CPUs. Internal per-case budgets adapt to cases/time/cost remaining. Rejected: allowing every case its full ten minutes.
7. **Saved evaluation is replayable offline.** The official score.py filters its scoring input to IDs present in predictions, so aggregate over all planned query IDs and score missing outputs zero without modifying the evaluator. Version splits, configuration, pricing, outputs, and metrics; isolate labels to scorer. Rejected: presenting a cherry-picked demo as accuracy evidence or requiring paid calls to inspect results.
8. **Disclosure and release are acceptance gates.** List actual assistants/models/frameworks and generated contributions; scan publishable history as well as files; verify the remote default branch before the deadline. Planning does not itself authorize or claim public release.

## Resolved research questions

Runtime version follows the starter (Python 3.12). No web service is required. Dataset contract covers seven projections, multi-failure windows, seconds versus milliseconds, and UTC+8. Official cost caps use the supplied price table; save that table for reproducible accounting. Prices/availability in production may differ, so record the configuration used and do not describe the frozen table as a live quote.
