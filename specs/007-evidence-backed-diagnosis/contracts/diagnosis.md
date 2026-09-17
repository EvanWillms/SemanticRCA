# Diagnosis and scoring boundary contract

## Inputs and stages

The existing `solve(instruction, dataset_dir, ctx) -> Solution` seam remains the runner integration point. Preserve original row identity through the existing runner context. Reuse feature 004 interpretation and discovery; consume feature 003 evidence rather than recreating raw joins inside prompts.

Supported scope → qualified discovery → hypotheses → bounded distinguishing operations → final incident selection → projection → evidence/usage persistence. Unsupported scope cannot enter diagnostic telemetry access. Partial findings may support degraded diagnosis, but their coverage and upstream failure remain explicit.

Operation arguments are validated against the declared inventory, scope, policy and remaining budget. Results retain source locators and raw measurements; optional summaries do not replace source-backed results. Planning must define the operation schemas, result-size limits, retry rules and finalization reserve before implementation. No open-ended code-execution operation is included.

## Artifacts and states

The [feature 011 loop contract](../../011-completion-aware-investigation/contracts/investigation.md)
refines the investigation boundary: assess initial evidence, choose one useful
operation, reassess its result, and preserve the reason for termination. Its
ordered assessments, gate outcomes, evidence revisions, progress counters,
unassessed observations and `investigation_stop_reason` extend `diagnosis.json`.
Keep any `assembly_failure_reason` separate so finalization cannot overwrite an
earlier blocked or budget exit. These fields do not alter benchmark serialization.

Retain feature 002's `predictions.csv`, `evidence/<row_id>.md`, and `usage.jsonl`, plus feature 004's scope/findings artifacts. Proposed additional artifacts under the output root:

- `cases/<row_id>/operations.jsonl`: operation ID, parent question/hypothesis, type, validated scope/arguments, policy/source identities, result references, coverage, elapsed time, status and stop reason. Record failed attempts as well as successful ones; redact credentials.
- `cases/<row_id>/diagnosis.json`: case identity, hypotheses, selected tuples, observed/inferred times, support/contradiction references, selection rationale, unresolved alternatives, evidence adequacy and case status.
- `diagnosis-run.json`: input/configuration/source identities, shared preparation costs, per-case statuses, timing/cost/accounting qualifications and overall outcome.

Feature 004 retains `discovery-run.json` for upstream discovery accounting. The diagnosis manifest references shared work rather than double-counting it. Complete case artifacts are persisted before publishing that case's prediction checkpoint; no cross-file transaction or resume guarantee is added.

Case execution status is `completed`, `degraded` or `failed`. Evidence adequacy is separately `supported`, `qualified` or `insufficient` with reasons; these describe the declared evidentiary policy, not correctness or a calibrated probability. Legal best guesses may be completed or degraded but cannot be labeled supported solely because they satisfy format/count. Invalid scope or no legal assembly yields failed status and blank prediction as an operational failure artifact; this fails final diagnosis acceptance. Low confidence, an empty anomaly shortlist and model failure must instead produce a best guess for valid judged inputs using available legal choices. Any failed case, retained upstream partial/unavailable discovery, or unmet run cap makes overall exit nonzero. A bounded provider fallback producing a legal answer from otherwise completed discovery may finish with explicit degraded status and exit zero; output success is not a diagnostic-quality claim. Persistence failure remains fatal with earlier checkpoints preserved.

## Answer serialization

Emit a JSON object with keys `"1"`, `"2"`, ... for exactly the requested incidents where a legal answer is possible. Internally retain full tuple association and ordering metadata even for partial projections. Sort by estimated onset and use a frozen deterministic secondary rule for ties, documented in the result. Each incident emits only requested keys in this order:

1. `root cause occurrence datetime`: UTC+8, `%Y-%m-%d %H:%M:%S`.
2. `root cause component`: exact allowed identity supported by current-deployment mapping.
3. `root cause reason`: exact governing vocabulary string.

Answer values must contain no newlines. Uncertainty, source IDs and alternatives belong in diagnosis/evidence artifacts rather than additional answer fields. Unknown precision must remain visible there even when output requires a single estimated second. Do not copy a hypothesis into multiple slots merely to claim multiple established incidents; weak selections required by the best-guess contract must explicitly state their unsupported distinctness.

## Isolated scoring

The scorer is an evaluation tool, never part of `solve()` or an available investigation operation. Seal predictions with a content hash and case/input/configuration identities before evaluation loads labels. Mount/provide only allowed public case inputs to inference; runtime guards must reject labelled or archived-answer sources, including unexpectedly adjacent files. Checking only that prompts omit labels is insufficient.

Record the pinned reference revision and scorer content hash, governing Track 1 source identity, allowed vocabulary provenance and the documented differences between official and upstream wrappers. The authoritative official scorer and vocabulary sources, revisions and hashes are recorded in [adoption notes](../../../docs/openrca-adoption.md); do not require that neighboring checkout at runtime. If source code is later vendored, retain its applicable attribution/license material.

Align both query and prediction inventories by their original IDs before invoking the reference. Keep semantic validation, raw reference result/error and reporting outcome separate. The official scorer uses a fixed-order regex, exact component/reason equality, <=60-second absolute time tolerance, count equality and best permutation of whole incident tuples. It may parse text a strict JSON validator rejects; preserve that observation rather than redefining compatibility.

The official function stringifies predictions (blank inputs score zero for nonempty criteria) and returns zero for empty scoring criteria. Its wrapper uses an inner join and filters to submitted IDs; prevalidate duplicates and account for missing cases independently. For authored fixtures, store expected raw scores/errors independently. For benchmark summaries, failed/missing/unscorable expected cases contribute zero achieved credit and remain in the full expected-case denominator, with raw failure counts separately reported; identify this reporting policy explicitly rather than attributing it to the reference implementation. Duplicate or unalignable inventories invalidate the evaluation run; do not publish an apparently valid aggregate from a guessed join.

Strict accuracy counts fully correct cases; partial accuracy averages per-case achieved credit under the declared policy. Report per-task counts, failures and both metrics. A compatibility corpus is not a held-out accuracy corpus. Subsequent repeated/routed evaluation remains governed by feature 002, and never chooses a gold-best repeat as the single-run agent output.
