# Implementation Plan: Final demo and submission runner

## Active implementation scope — harness only

The user requested tasks for an empty-output harness. [tasks.md](tasks.md) implements H-001–H-004 in the specification, not the full pipeline below. Use Python 3.12 standard-library CSV/JSON/path/CLI facilities and unittest; no pandas, model SDK, telemetry reader, routing policy, or API credential validation is needed for this milestone. Preserve `solve(instruction, dataset_dir, ctx) -> Solution` as the replacement seam; keep `agents.heuristic` as the default compatibility shim to the stub in `agents.submission`.

Outputs are structurally present but contain no diagnosis: blank prediction values, explicitly unimplemented evidence, and genuinely zero calls/tokens. Empty query input produces headers/empty files. No fabricated incident object or benchmark success claim is allowed. Runtime process success means harness execution only. Tests cover this slice because the feature explicitly requires contract/integration validation.

Constitution review: this is an authorized intermediate scaffold, not a completed submission. Final best-guess predictions, supporting evidence, routed evaluation and release gates remain unsatisfied. No constitution amendment or final-release waiver is implied. The project maintainer owns the follow-up full-runner work described below; track the gap in REPORT.md and keep checklists/release.md unchecked. The no-key behavior applies only to the no-call stub.


**Branch**: `002-final-demo-runner` | **Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)

## Summary

Package a bounded headless RCA pipeline behind the official starter CLI. Use the same artifact for live demonstration and judging. Prioritize a complete contract-compliant vertical slice, then evidence quality and measured routing. Research scripts and experiment 001 are inputs to assess, not an existing production agent.

## Technical Context

**Language/Version**: Python 3.12, aligned with the official starter image.
**Primary Dependencies**: Starter pandas/OpenAI-compatible client; pin runtime dependencies during implementation. Avoid adding a service or database.
**Storage**: Read-only mounted CSV telemetry, bounded in-memory chunks; all caches, temporary files, bytecode if enabled, and outputs under --out.
**Testing**: Contract tests, deterministic mock endpoint, official validator and unchanged scorer, constrained Docker rehearsal.
**Target Platform**: Linux container, 2 CPUs, 8 GB, no GPU.
**Project Type**: CLI batch agent with evaluation scripts.
**Performance Goals**: Initial internal targets: 50 seconds and $1 per case; 1,100 seconds and $22 per run, with finalization reserves. These are design targets to validate, not measured performance.
**Constraints**: Hard external caps 600 seconds/$3 per case, 1,200 seconds/$25 per 20 cases; only the configured Featherless endpoint reachable at runtime.
**Scale/Scope**: 20 judged queries, multi-gigabyte telemetry, seven task types, exact incident projection output.

## Constitution Check

| Principle | Design evidence / release gate |
|---|---|
| Evidence first | Typed observation provenance, explicit uncertainty, deterministic evidence sections; audit claims against raw files. |
| Bounded telemetry | Chunked selected-day/column reads, explicit window/reference scope; retrieval isolated from diagnosis. |
| Cost-aware routing | GLM-only tier routing, call reservations, dollar accounting and measured fixed-model comparison. |
| Reproducible unseen evaluation | Freeze exposure-aware held-out cases, repeated configurations, unchanged scorer, offline metric recomputation. |
| Runtime/submission | Exact CLI, root Dockerfile, runtime credentials, predictions/evidence/usage, release checklist. |

Pre-research and post-design review: PASS for the design, with no constitutional exception. Execution gates remain pending; a plan is not evidence that the agent works. Existing development exposure metadata must be reconciled before any held-out claim.

## Project Structure

```text
specs/002-final-demo-runner/
  spec.md  plan.md  research.md  data-model.md  quickstart.md
  contracts/runner.md
  checklists/requirements.md  checklists/release.md
Dockerfile
.dockerignore
requirements.txt
run.py
agents/heuristic.py        # compatibility shim to submission agent
agents/submission.py
rca/                       # scope, retrieval, diagnosis, evidence, budget, model client
configs/                   # routing policy and official pricing snapshot
README.md
REPORT.md
eval/                      # split/config manifests, harness, sanitized results, summary
scripts/                   # validation, release audit, demo helpers
tests/contract/
tests/integration/
```

Only the feature documentation exists from this change. Source paths above are proposed. Keep the official entry point recognizable; retain its default agents.heuristic module as a compatibility shim to agents.submission, because the official validator also explicitly selects that module. Add minimal preflight/finalization protections where required. Preserve CLI and Solution/format_prediction compatibility. Do not depend on the neighboring official checkout or workstation data paths in the shipped image.

## Implementation Sequence

1. **Runnable vertical slice (FR-001–006,010)**: Import attributed starter interfaces and evaluator support into this repo. Make the default agents.heuristic delegate to agents.submission, pin dependencies, use a root Dockerfile with a narrow source COPY/build context. Adapt the baseline into a complete all-task diagnoser with exact projection/serialization and deterministic evidence. Add README with factual AI disclosure. Validate with fixtures before paid calls.
2. **Bounded evidence and diagnosis (FR-003–005,012)**: Parse scope deterministically and normalize times to UTC+8. Retrieve selected days/columns in chunks, retain source locators and sample limitations, discover component identities from the mounted deployment. Produce an observation packet and ranked hypotheses; preserve separate incidents even if components repeat. Use metrics first, targeted traces/logs for discrimination. Never translate descriptive symbols directly into cause labels without a supported hypothesis. Every path must yield a best guess when a valid scope exists.
3. **Model routing and budgets (FR-002,006–008)**: Route extraction/formatting to cheap GLM tiers and short diagnosis to stronger tiers. Retain deterministic serialization/evidence rendering. Check response error bodies before choices, use bounded retries and run-scoped model suppression. Reserve worst-case input/output-token costs before dispatch; include outstanding calls and treat unknown billing conservatively. Limit call timeouts and SDK-internal retries by remaining wall time; avoid multiplying SDK and application retries. A supervised case worker bounds CPU/retrieval/model work; parent retains a lightweight fallback and ledger so a worker timeout cannot lose usage or later cases. Recompute allowance from remaining run budget/cases, not just the ten-minute per-case cap.
4. **Fault-safe finalization (FR-004–008)**: Persist evidence and usage before atomic prediction checkpoint replacement. Restrict all mutable runtime state to --out, disable bytecode writes to source, sanitize exception messages, and redirect temporary/cache locations under --out. Preflight IDs/paths/credentials; do not echo credentials. Refuse stale nonempty outputs unless explicitly compatible resume is implemented. On recoverable exhaustion, render a marked low-confidence result without another model call. Preserve completed results if externally stopped; do not claim hard-kill recovery of in-flight work.
5. **Evaluation and presentation (FR-009,010,012)**: Freeze an exposure-aware split before tuning. Compare routed and fixed-model runs with identical retrieval, prompts, stopping policy, and dataset; make routing the explicit changed variable. Use at least two repeats per configuration (three preferred if budget permits), report variation and small-sample limitations. Fixed-model provider failure yields the deterministic fallback, never a second model; report outages. Keep the official evaluator unchanged, but aggregate over the full planned query set with missing cases scored zero: the official score wrapper filters to predicted rows. Use per-case usage deltas from the shared run ledger to avoid double counting. Produce REPORT.md, committed sanitized result records, offline summary command, and a four-minute demo script.
6. **Release rehearsal (FR-011)**: Scan secrets in source/history/build context/image and inspect disclosure. Run official-equivalent validation, a resource-capped 20-case rehearsal, and an endpoint-isolation test. Merge/push tested work to the actual remote default branch before the deadline; verify fresh public clone and form submission. Keep publication operations as explicit release work following implementation.

## Validation Strategy

Map each FR to the acceptance checks in quickstart.md and contracts/runner.md. Deterministic tests cover CSV quoting, seven projections, exact labels, UTC+8, row IDs, multi-incident associations, response failures, accounting, timeout finalization, and atomic checkpoints. Mock endpoint tests exercise routing and forbidden-network behavior without paid calls. A live 20-case constrained run is required to support resource/latency claims; mocks cannot establish these. Scoring reuses the official evaluator unchanged; evidence requires source review beyond shape validation. Release cannot pass on fabricated or placeholder evaluation results.

## Risks and Decisions

- The present repo has no complete diagnoser. Start with a working baseline contract; do not wait for semantic compression research.
- Starter behavior is a starting point: blank crash predictions, raw traceback evidence, default heuristic selection, and lack of hard internal budgets require attention.
- Sparse evidence can support only a weak guess; render uncertainty rather than manufacture measurements or ruled-out alternatives.
- Strict held-out evaluation may be small because earlier research exposed cases; disclose the split and exposure limits.
- No paid provider calls or runtime validation were performed while writing this plan.

Current phase: [tasks.md](tasks.md) defines the authorized empty-output harness milestone. Full-runner implementation tasks remain deferred.
