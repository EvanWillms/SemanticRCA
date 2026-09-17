# Implementation Plan: Always-running deterministic preparation executor

**Feature**: `004-prompt-anomaly-integration` | **Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)
**Authoring checkout**: `006-track1-trace-extraction`. Setup used explicit feature 004 selection; no branch switch or merge was performed.
**Status**: Initial design specified and aligned to the supplied official Track 1 docs; implementation, policy validation and acceptance pending.

## Summary

Build feature 004 as successive runnable vertical slices through the existing `run.py` → `solve()` → `OutputWriter` path. The first ten-minute implementation target is query interpretation with persisted scope and truthful stage status, not the entire multimodal pipeline. Then add bounded inventory, trace extraction, independent metric extraction, qualified comparisons, and targeted corroboration. Every increment preserves the official three-flag command and completed-case checkpoints. Feature 007 subsequently turns the evidence into incident answers; feature 002 owns final submission/release gates.

The user's ten-minute deadline is a development timebox, not a claim that full preparation or a valid judged diagnosis can be delivered within it. At the deadline, demonstrate the last passing slice and report remaining work. A blank-prediction discovery executor is runnable but not a submittable completed RCA solution.

## Technical Context

**Language/Version**: Python 3.12.
**Primary Dependencies**: Standard library (`csv`, `datetime`, `hashlib`, `sqlite3`, `statistics`, `unittest`); no new runtime package or provider for preparation.
**Storage**: Immutable mounted CSV input; SQLite prepared views and JSON/JSONL evidence beneath `--out` only.
**Testing**: Existing unittest contract/integration suite plus independently authored scope/telemetry fixtures and scan oracle; isolated Docker rehearsal.
**Target Platform**: Linux Docker, 2 CPUs, 8 GB RAM, no GPU.
**Project Type**: Unattended batch CLI with replaceable agent seam.
**Performance Goals**: Scope-only public-inventory target <5 seconds; full runtime <600 seconds/case and <1,200 seconds/20 cases, including cold preparation. These are targets, not measured full-pipeline results.
**Constraints**: No labels, network, model calls, developer indexes or fixed component lists in preparation; finalization reserves; finite responses; raw source provenance and unit qualifications.
**Scale/Scope**: Supplied Track 1 schemas, seven projections, variable deployment identities and dates. Seventy public prompts are a validation corpus, not a runtime limit.

## Official Track 1 authority

The supplied official `data.md`, `submission.md`, `scoring.md` and `models.md`
are pinned in [source-notes.md](source-notes.md). They govern the final entrypoint,
input/output boundary, unseen-deployment portability, answer format, GLM model
routing and external resource caps. Feature 004's no-call/blank-answer stages
are project development milestones, not an official submission exemption.

Final R7–R9 behavior must always produce a best guess for valid judged cases,
with exactly the requested incident count, requested fields in datetime/component/
reason order, UTC+8 datetime and exact allowed component/reason strings. Emit
incidents chronologically as submission.md requests, even though scoring.md says
the evaluator accepts permutations. Preserve row_id when judging a subset.
Unsupported scope remains an operational failure; uncertainty, no candidates or
provider failure alone must not become final-answer abstention.

R7–R9 must use only GLM-family models through FEATHERLESS_BASE_URL (the documented
Featherless default when unset), with FEATHERLESS_API_KEY, bounded capacity-error
retries and in-family fallback. Detect HTTP-200 error bodies before reading
choices. Final limits are $3/600 seconds per case and $25/1,200 seconds per
20-case run on 2 CPUs/8 GB/no GPU; all preparation and finalization count.
No-call discovery records zero model usage but does not fulfill routing or
routed-versus-single-model evaluation. Final evaluation records strict/partial
accuracy by task, dollars, seconds and repeat-run variation.

Only supplied dataset/query inputs are runtime case data; write under --out,
and use no network during preparation. Later runtime networking reaches only
the configured model endpoint. Never package developer data or download upstream
evaluation data. Official schema examples and development cardinalities are not
fixed component inventories. The official data guide defines timestamp units,
but does not establish duration units or make parent/child timing alone proof of
a network fault; preserve feature 003/005 qualifications.

## Constitution Check

| Gate | Pre-design | Post-design evidence/obligation |
|---|---|---|
| Evidence first | Pass | Facts, comparisons and hypotheses are separate; discovery predictions remain blank; provenance and missingness required. |
| Query-bounded access | Pass | Scope before telemetry, independent retrieval tools, bounded recovery and explicit coverage. |
| Cost-aware routing | Pass for this no-call feature | Zero model usage; future routing remains feature 007/002 work, not waived. |
| Reproducible unseen evaluation | Pass for design | Deterministic fixture/replay gates; development exposure recorded; held-out routed/single-model study remains release-blocking. |
| Runtime/submission interface | Pass for staged design | Three flags, Docker and checkpoint seams retained; discovery completion is never claimed as final submission readiness. |
| Spec Kit sequence | Pass | Existing feature spec → this plan → tasks generation → implementation → analyze/converge. No tasks.md or production changes generated by this command. |

No constitutional exception is requested. Ratification-date placeholder in the existing constitution is not changed here.

## Always-running main policy

“Main” means the integration baseline, not permission to switch the shared dirty checkout. Work in small independently reviewable changes; promote each only after its CLI smoke and affected contract checks pass. No wholesale runner rewrite, dormant TODO path selected by default, or bulk import of experimental code.

Keep `agents.submission` as the explicit stub regression path. Add `agents.discovery` behind the existing `--agent` seam while incomplete. The official three-flag default stays on the last accepted behavior until full feature 004 acceptance; then promote discovery. Scope-only and other intermediate demos use the optional agent override, clearly report incomplete discovery, and cannot masquerade as feature acceptance. Diagnosis becomes default only after feature 007 contract gates. Each promotion includes a clean-checkout/image check; untracked local files are not a deployable baseline.

Every slice must provide: real behavior through the CLI, explicit capability/status in artifacts, a small independent acceptance fixture, prior-mode regression coverage, and a reversible default-selection change if promoted. No schema-breaking change without updating producers, writer and validator together.

## Delivery sequence

Effort boxes are planning targets, not elapsed-time promises. R0/R1 are the immediate ten-minute implementation attempt; later slices are ordered by dependency and acceptance rather than invented completion times.

| Slice | Concrete end-to-end behavior | Change seam | Promotion/exit evidence |
|---|---|---|---|
| R0: baseline (minute 0–1) | Existing CLI emits durable stub artifacts | No refactor | Existing 26 tests green; explicit stub smoke; identify only slice-owned files |
| R1: scope (minute 1–10) | Public instruction → typed scope → scope.json, findings not_run, honest evidence and zero usage | Optional task_index in QueryRow; pure parser; optional structured result in Solution; writer persists sidecars; discovery agent | All seven independently authored projections; renamed deployment/date; midnight; conflict rejected without telemetry; later valid row persists. Public 70-query agreement is required before claiming parser completion |
| R2: inventory | Supported scope → allowed telemetry inventory and source snapshot receipt | Track 1 adapter, source/policy manifest, bounded operation envelope | Missing/schema-invalid sources distinguished; answer-file access trap; raw units and discovered identities; cold work charged |
| R3: recorded traces | Select by deployment/time; recover all available records for selected trace IDs; extract facts | Streaming oracle first, adapted SQLite builder/access layer; extraction from feature 005 | Unsorted/cross-partition/boundary fixtures; no identity collision or silent duplicate overwrite; source locators resolve; partial recovery explicit |
| R4: resource series | Independently retrieve scoped container/node/service/mesh/runtime measurements | Metric adapter and series operation using same receipt/budget contract | Planted resource change remains visible with normal/missing frontend trace; invalid KPI differs from valid empty series |
| R5: comparison and packet | Historical references + trace duration/structure + per-resource metric differences → auditable candidates | Versioned policy, comparisons, evidence packet, discovery validator | Sparse/zero/constant/missing references qualified; unmatched structure retained; candidate count independent of incident count; completed/controlled partial replay; no NaN/Infinity |
| R6: corroboration and acceptance | Supported relationship expansion and question-directed log inspection; cold 20-case run | Relationship/log operations and integrated discovery agent | Ambiguous targets remain unknown; complete operation journal; budget/cache invalidation tests; full 004 acceptance matrix. Promote discovery default only here |
| R7: first diagnostic executor (feature 007) | Evidence packet → associated hypotheses → legal requested projection, with explicit best guesses | Diagnosis agent, typed answer assembler, pinned vocabulary; bounded GLM provider path | Seven projections, repeated-component incidents, exact strings/count/order, no fabricated evidence; controlled provider responses first |
| R8: investigatory loop (feature 007) | Choose distinguishing question → declared tool → update hypotheses → bounded finalize | Controller over same operation registry; no arbitrary Python | Invalid calls, provider failure, budget exhaustion and replay tested; all attempts/unknown usage recorded; legal best guess when possible |
| R9: submission gate (feature 002/007) | Clean image runs official command from cold input, writes scored-compatible answers and evidence | Build/packaging, isolated pinned scorer, runtime ledger and release report | Controlled scorer parity, label isolation, 20-case CPU/memory/time/cost rehearsal, required held-out routed versus single-model comparison, evidence review |

If R1 cannot clear its exit checks in ten minutes, keep the passing baseline and report scope work as incomplete. Do not delete tests, hardcode public answers, skip invalid-scope handling, or claim inventory-only work is full data preparation to meet the clock. Subsequent task generation must split each row into small runnable changes, rather than separate all-model/all-storage/all-UI batches.

## Architecture and operation flow

1. Preflight the whole query CSV/path contract without telemetry; preserve row identity and optional metadata.
2. Interpret each instruction before any case telemetry read. Freeze scope and policy IDs.
3. Create a run context once: monotonic deadline, fair remaining-case allocation, source manifest, prepared-view handles and shared-work ledger. The runner passes it through ctx; individual agents do not own output paths arbitrarily.
4. Execute deterministic operation requests: inventory → trace and metric paths → references/comparison → optional justified relationship/log follow-up.
5. Assemble immutable observation/reference/finding/candidate records. Write case sidecars, evidence and usage before publishing its prediction row.
6. Continue after recoverable analysis failures and return nonzero mixed status. Persistence/global preflight failures remain fatal. A valid empty finding list differs from work not executed.

Use source content digests and extraction/schema version for prepared-view identity. Comparison-policy identities belong to derived caches. Reuse only completed compatible views; build to temporary names and publish completion after reconciliation. No cross-process resume is added. Repeated same-window queries may share evidence but retain their own count/projection/instruction and case artifacts.

## Initial project policy and budgets

The executable design rules are in [discovery-policy.md](contracts/discovery-policy.md). These are project choices, not official Track 1 detector requirements or validated effectiveness claims.

Start with a declared five-minute pre-window reference, with no automatic lookback expansion or peer fallback. This is a limited descriptive comparison, never certified healthy. Trace conditional duration uses operation/type/direct-child signature context and discovered compatible frontend identities; preserve pooled-replica qualification and a separate unmatched-structure channel. Require at least 20 eligible reference occurrences for the initial median policy; this conservative engineering default is not a significance or health claim. Ineligible channels return unavailable, not a guessed score. Reference completion obeys feature 005 cutoff rules and provisional duration-unit qualifications.

Metric comparisons use exact resource/KPI/unit context with at least 20 valid reference samples; report sample coverage and median/signed absolute differences. No cross-unit score fusion, interpolated missing data, percentile claim or division by zero. Rank positive duration excess within compatible contexts and absolute metric differences within one KPI/unit channel; retain both directions for metrics, deterministic ties and truncation. Retain constant-reference absolute differences as qualified descriptive findings; no standardized anomaly confidence. These policy choices must be encoded as versioned configuration and validated on authored fixtures before promotion; they make no incident-sensitivity claim.

Proposed initial limits: 1,180-second run stop, 580-second case stop; reserve 20 seconds of run capacity and 5 seconds per case for finalization, never spend reserves on analysis. Shared cold preparation cap 180 seconds; on cap report partial/unavailable and preserve case allocation. Allocate each remaining case the lesser of 575 seconds and its fair share of remaining nonreserved run time. R7+ must revise allocations to reserve model/diagnosis capacity before use, within unchanged external caps.

Bound initial evidence packets to 30 recovered traces, 50 metric series per operation with 120 deterministically selected display values each (selection and full-series comparison rules are in the policy contract), and 200 records per targeted log operation. Deterministic selection, withheld counts and continuation/stop reasons are mandatory. Raw indexed records remain addressable; packet limits do not establish complete coverage. Check deadlines between bounded parse batches and query operations; enforce SQLite query interruption, cap scans/response bytes, and measure peak memory during rehearsal. Shared preparation is charged once in the run ledger and referenced by cases.

## Project Structure

```text
specs/004-prompt-anomaly-integration/
  plan.md                 # sequence and gates
  research.md             # decisions and reuse findings
  data-model.md           # structured handoff and states
  quickstart.md           # present and future validation commands
  contracts/integration.md
  contracts/executor.md   # operation and persistence seam
  contracts/discovery-policy.md # explicit project comparison/selection defaults
  tasks.md                # subsequent speckit-tasks output, not created here
run.py
agents/submission.py      # retained stub
agents/discovery.py       # planned deterministic orchestration
rca/contracts.py
rca/inputs.py
rca/outputs.py
rca/scope.py              # planned pure interpretation
rca/telemetry/            # planned inventory, index, trace, metrics, logs
rca/discovery/            # planned policies, comparison, operations, budgets
scripts/validate_discovery.py  # planned, distinct from stub validator
 tests/contract/          # existing and extended
 tests/integration/       # existing and extended
 tests/unit/              # planned pure parser/extraction checks
```

Adapt reusable functions from experiments into runtime modules only after fidelity tests; Docker currently copies runtime packages only. Do not make runtime import research coordinators or evaluators. SQLite is a rebuildable access layer, not a diagnosis engine.

## Verification and acceptance impact

Map R1 to FR-001–003, R2/R3 to FR-004/005/015, R4/R5 to FR-006–010, and all slices/R6 to FR-011–016. Existing [acceptance.md](acceptance.md) remains authoritative; the slice schedule does not remove any scenario. Run changed-seam tests plus stub regression on each increment. At R6, run the entire discovery acceptance corpus and the cold 20-case rehearsal. Never infer full readiness from a small fixture or this plan.

Planning-time baseline: 26 existing unittest tests passed on 2026-09-17. No new discovery implementation, telemetry benchmark, Docker run, paid call, diagnosis or accuracy result is claimed.

## Complexity Tracking

No gate violations. Additional state is limited to a run context, typed records, bounded operations and a writer-owned artifact handoff. General agent platforms, vector stores, arbitrary-code tools and a new web service are unnecessary.
