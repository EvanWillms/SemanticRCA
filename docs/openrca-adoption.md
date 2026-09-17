# OpenRCA adoption decisions and delivery sequence

Created 2026-09-17 from the local checkout at `/Users/nonadmin/Development/mantisgrid-hackathon/OpenRCA`, revision `c1bd4af7f635171a1c31cdd567c07d698dff6abc`. This path is a review source, never a runtime dependency. This work inspected source and documentation, not archived predictions or fault records. No benchmark or runtime acceptance was executed. The official data guide contains a worked labelled example; that example is development-exposed and must not be described as held out.

## Source-to-decision map

| Inspected source relative to OpenRCA | Useful scaffold | SymbolicRCA decision |
|---|---|---|
| `main/task_specification.json` | Seven when/where/why projections | Feature 004 interpretation fixtures; actual instruction remains scope authority |
| `rca/baseline/rca_agent/prompt/basic_prompt_Market.py` | File schemas, identity formats, timestamp conventions | Validated adapters and discovered identities; no copied component inventory or assumed replica count |
| `rca/baseline/rca_agent/controller.py` | Atomic investigation step followed by observation | [ADR 0006](adr/0006-bounded-investigation-operations.md); bounded operations with explicit results |
| `rca/baseline/rca_agent/executor.py` | Separate execution and result collection | Structured evidence operations; no unrestricted generated-code kernel |
| `rca/baseline/rca_agent/prompt/agent_prompt.py` | Distinction between discovery and localization | [ADR 0007](adr/0007-evidence-backed-incident-diagnosis.md); heuristic assumptions require validation |
| `rca/run_agent_standard.py` | Per-case trajectories and execution bounds | Retain existing runner/checkpoints; add operation audit trail; keep labels out of inference |
| `main/evaluate.py` | Executable parsing and scoring reference | [ADR 0008](adr/0008-isolated-evaluator-compatibility.md); pinned parity tests and explicit row association |

The inspected scorer extracts fields in time/component/reason order, requires equal predicted/gold incident counts before awarding points, compares component/reason exactly, allows absolute time error <=60 seconds, and searches permutations of incident tuples. Its file wrapper sorts prediction row IDs but does not independently join both inputs by identity. These are upstream source observations, not newly executed test results. The official reference below supersedes this upstream wrapper for compatibility.

## Ordered delivery gates

1. **Scope and schema:** [feature 004](../specs/004-prompt-anomaly-integration/spec.md) interprets all seven query types and discovers the mounted source inventory; feature 003 supplies fidelity and linkage contracts.
2. **One complete discovery path:** query → scope → bounded telemetry operations → qualified metric/trace candidates → auditable evidence. Keep predictions blank and model usage zero. Complete feature 004's cold-run and failure checks.
3. **Diagnosis:** [feature 007](../specs/007-evidence-backed-diagnosis/spec.md) compares hypotheses, performs bounded follow-up, and assembles associated incident tuples with explicit uncertainty. Use controlled operations/model responses for acceptance before paid evaluation.
4. **Compatibility:** seal outputs, validate all projections and row associations, and compare with the pinned scoring reference in isolation. Small serialization fixtures can be developed before the diagnoser; a live scorer pass depends on diagnosis outputs.
5. **Measured final deliverable:** feature 002's repeated held-out routed/single-model comparison, evidence audit, resource/cost rehearsal, documentation and release checks remain required. Neither these ADRs nor passing a compatibility fixture establishes diagnostic accuracy.

## Ownership and deferred choices

Feature 003 owns retrieval, reference qualification and evidence-backed relationships. Feature 004 owns interpretation and deterministic discovery. Feature 007 owns hypothesis investigation, diagnosis projection and evaluator compatibility. Feature 002 owns the external runner, provider restrictions, routing comparison and final release. The project maintainer owns remaining delivery gates.

Concrete operation signatures, model/prompt/routing configuration, hypothesis ranking, tie handling, reason-vocabulary provenance and budget allocation must be frozen in implementation planning. These are planning decisions within the requirements, not missing user approvals. No runtime changes, paid runs, commits or publication are part of this documentation task.

## Governing Track 1 sources checked

The user supplied `hackathon-2026-official/track-1/docs/scoring.md` and `docs/submission.md`. Both were read, along with `docs/data.md` and `starter/score.py`, at official repository revision `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`. These documents govern the adaptation; the participant agreement remains the authority for rubric weights. No weights are inferred from OpenRCA.

- Official scorer: `track-1/starter/score.py`, SHA-256 `b62dbe060b200a155d66c5beca7da7a981b006f03bb594e3b1e2bde71ca91c0a`. Use this as the compatibility target.
- Upstream comparison: `main/evaluate.py`, SHA-256 `9a1c235139266c32b0e95c7e9938591b8fe014aad4cde95580f73f13a54d53f1`. It is not byte-identical to the official scorer.
- Shared scoring semantics: exact count, exact component/reason, ordered datetime/component/reason extraction, <=60-second tolerance and permutation matching of whole incident tuples. No newlines in answer values.
- Official differences observed in source: predictions are converted to strings before regex matching, zero scoring criteria return 0.0, and the file wrapper merges by `row_id`. The wrapper filters queries to submitted IDs and uses an inner join, so it does not by itself establish full expected-case coverage or reject duplicate IDs. Add coverage/uniqueness checks outside it without changing the scoring function.
- Always provide a best guess for a valid judged case; low confidence, missing candidates or provider exhaustion are not abstention policies. A blank artifact is permitted only as explicit operational-failure reporting, scores zero and fails diagnosis acceptance. The retained stub/discovery milestones are not submission-ready agents.
- Submission requires chronological numbered objects and original `row_id` association, although scoring permits arbitrary incident order. Retain chronological output. Evidence has four required sections and is checked against raw files. Judges meter dollars/time themselves; `usage.jsonl` supports our own evaluation.
- Endpoint isolation, GLM-family fallback (including HTTP 200 error bodies), 2 CPUs/8 GB, 600 seconds/$3 per case and 1,200 seconds/$25 per run remain mandatory. Build dependencies into the image; no runtime installs/downloads.
- Report at least two configurations with accuracy, seconds, dollars and repeat variation; the constitution specifies routed versus the same agent on one model. Public deployment results are development estimates, not results on the unseen judging deployment.
- The official submission document allows bug/deployment repairs after the September 17, 2026, 3 p.m. PDT deadline, but no new features. These specs authorize neither late feature publication nor submission; feature 002's release gate must respect that restriction.

The 15 exact reason strings in official `docs/data.md` are the allowed vocabulary source, not OpenRCA's static component list. Plans must preserve these source identities and recheck only if the governing inputs change.
