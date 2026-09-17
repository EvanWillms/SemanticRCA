# Completion assessment and termination contract

Status: proposed implementation contract under [ADR 0016](../../../docs/adr/0016-completion-aware-investigation.md).
No runtime capability is asserted.

## Boundary and records

Retain `solve(instruction, dataset_dir, ctx) -> Solution` as the repository runner's
integration seam, outside the standalone domain package. The domain package
exports the evidence and investigation APIs in [domain-api.md](domain-api.md);
it imports neither `Solution` nor runner persistence code. A future runner adapter
maps its scope and returned domain result into feature 007 artifacts.
Consume supported scope and initial evidence from features 003–004; do not infer
that those suppliers exist merely because their contracts do. Authored fixtures
permit independent development. Unsupported scope exits before telemetry access.

One state owns the case identity, scope, source/policy identities, evidence ledger,
coverage, hypotheses, current draft, material gaps, operations and remaining limits.
Preserve observations separately from summaries and inferences. A draft may be
incomplete; finalization applies feature 007's legal best-guess policy.

Each assessment records:

- Assessment ID, assessed evidence revision, current incident draft and evidence adequacy.
- Supporting and contradicting observation IDs, alternative explanations and material gaps.
- Proposed `complete`, `continue` or `blocked` decision with rationale.
- For `continue`: exactly one operation request, its target gap and how possible results could change the answer or adequacy.
- For `blocked`: a specific reason and evidence that remaining available operations cannot resolve the gap.
- Controller acceptance/rejection, failed checks, elapsed time, usage and remaining limits.

Source IDs must resolve to observations in the correct case/entity/time scope.
Existence is necessary but does not prove a claim follows from an observation.
The assessment explains evidential support; controlled expectations independently
check that judgment. Uncalibrated confidence is never a completion predicate.

## Transition rules

1. Validate scope; prepare or load evidence under the shared budget.
2. If assessment capacity is unavailable, record a hard stop. Otherwise assess
   the initial state before any follow-up, or the new state after each attempt.
3. Validate the assessment schema and reference/answer integrity. Invalid
   assessments preserve valid state and receive bounded correction feedback;
   they cannot silently become completion or absence of useful actions.
4. Accept `complete` only when all FR-003 conditions pass for the assessed
   evidence revision. Record `evidence_sufficient` and retain qualifications.
5. Accept `blocked` only with the corresponding inability explanation. A known
   alternative operation that could resolve the gap invalidates the blocker.
6. For continued investigation, enforce the non-progress rule and available
   operation/assessment/time/cost budget. Dispatch one validated useful operation,
   record its result even if empty/failed/rejected, and return to assessment.
7. Finalize from retained state. No additional live model call is required.
   Output validation failure is an assembly failure, not permission to invent
   evidence or retrospectively alter the investigation's reason.

A hard deadline or provider failure can interrupt the normal assess-after-result
path. Mark newly arrived observations unassessed, retain them in evidence, and
do not carry forward an old sufficiency claim over contradictory or unreviewed
evidence. Late responses after a terminal decision do not reopen the case; audit
and account for them if received. Resource cancellation/timeout enforcement must
be defined in planning, rather than relying on a cooperative model stop.

## Terminal reasons and output semantics

| Reason | Required explanation |
|---|---|
| `evidence_sufficient` | Accepted assessment and completion checks for the current evidence revision |
| `missing_source` | Required unavailable evidence and why available alternatives cannot resolve the gap |
| `missing_capability` | Needed unavailable operation and why available operations cannot resolve the gap |
| `no_useful_action` | Available operations exhausted or unable to distinguish the remaining alternatives |
| `stalled` | Two consecutive operation attempts with no qualifying progress |
| `provider_failure` | Failed provider attempt(s), recovery outcome and retained state |
| `invalid_assessment` | Schema or semantic validation failures after the allowed repair attempt |
| `budget_exhausted` | Exhausted counter/deadline/cost limit or insufficient reserve for the next step |
| `unsupported_scope` | Input validation failure before diagnostic telemetry access |
| `no_legal_answer` | Final assembly failure when supported scope has no legal answer choices |

Record the first terminal decision with ordered events and all concurrent limiting
conditions. A resource boundary preventing another call yields `budget_exhausted`;
an unrecoverable provider/assessment failure while capacity remains yields its
specific reason. An accepted sufficiency assessment remains sufficient if the
follow-up counter has just reached its cap; it needs no additional operation.

Keep `investigation_stop_reason` separate from `assembly_failure_reason`, execution
status (`completed/degraded/failed`) and evidence adequacy
(`supported/qualified/insufficient`). If an earlier investigation reason exists,
retain it when final assembly fails; put `no_legal_answer` in assembly failure.
Use `no_legal_answer` as the investigation reason only when no earlier reason
exists. Feature 007 remains authoritative for case/run exits and answer projection.

No missing-source, stalled or forced-limit exit automatically upgrades or erases
evidence adequacy. Missing requested support stays insufficient or qualified as
appropriate. Valid judged cases still receive legal best guesses; failed scope
or impossible legal assembly yields blank failed output under feature 007.

## Initial toy profile

- At most three follow-up attempts, including rejected requests and operation retries.
- At most four assessment-provider attempts, including provider retries and malformed/invalid decision repairs. Permit at most one repair/retry per failed assessment or operation, within the global caps; permanent failures are not retried unchanged.
- Before a follow-up, reserve capacity for at least one reassessment and finalization. Repair can reduce the number of available follow-ups. There is no hidden fifth assessment.
- Two consecutive non-progress operation attempts stop continued investigation. New source-backed evidence, new coverage knowledge or resolution of a named gap resets this counter. An empty result can add coverage; repeating the same empty result does not.
- Reject an identical operation against the same source/scope/policy unless retrying a recorded transient failure. Each rejection counts as an operation attempt and as non-progress.
- Time/cost limits include preparation, assessments, repairs, operations and persistence. Feature 002 caps dominate these toy counts. Concrete timeout/reserve amounts must be fixed before implementation.

Persist the frozen profile and decision-policy identity for replay. Fixed
operation/assessment observations and clock/limit decisions reproduce the same
terminal path. Live deadlines and provider variability may change coverage.

## Artifact integration

Extend feature 007's `cases/<row_id>/diagnosis.json` with ordered assessments,
gate outcomes, evidence revisions, progress counters, terminal reason, unassessed
observations, remaining gaps and assembly failure when applicable. Reference
`operations.jsonl` rather than duplicating raw results. Retain every provider
attempt in usage accounting; unavailable usage is explicitly unknown.

The existing four evidence sections explain the selected answer, adequacy,
sources, unresolved alternatives and why investigation stopped. Do not add
internal status fields to the benchmark prediction. No resume guarantee or
default-agent change is added. Persistence failures remain governed by feature
007, with earlier checkpoints preserved.
