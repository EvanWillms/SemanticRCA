# Acceptance matrix: prompt-to-anomaly integration

These checks are requirements for subsequent implementation. Initial selection/comparison rules are defined in [discovery-policy.md](contracts/discovery-policy.md); they are project defaults, not official detector requirements. No detector, parser or runtime acceptance test was executed for this documentation task.

| Case | Independent fixture or action | Required result | Requirements |
|---|---|---|---|
| P1 | Review all 70 public instructions without labels; manually author scope expectations independently of implementation | Exact deployment/window/count/projection for every row and all seven types | FR-001–003 |
| P2 | Equivalent whitespace, wording already present in public prompts, another date/deployment and valid midnight transition | Same semantic scope with original extraction provenance; no fixed-row/date assumptions | FR-001–003 |
| P3 | Missing count, malformed date, impossible window, metadata/projection conflict, unsupported instruction | Explicit scope failure before any telemetry access; valid following case proceeds | FR-002/003/012 |
| D1 | Authored matched traces with known duration changes, added/removed children and multiplicity-only change under track1-discovery-v1 rules | Correct empirical differences; structural changes/unmatched requests retained; no causal label | FR-004/006/008/009 |
| D2 | Sparse/constant/zero/incompatible/contaminated references and provisionally known units | Qualified or unavailable results per declared policy; no fabricated numeric score or healthy reference claim | FR-006/008/009 |
| D3 | Pod/node/service metric change with normal or missing frontend traces; isolated spike omitted by the 120-value display sample | Source-grounded per-sample candidate independent of frontend trace shortlist and retained despite display reduction | FR-007/009 |
| D4 | Targeted log follow-up and ambiguous service/replica/host relationship | Link/question/source retained; no unsupported exact request join; uninspected families listed | FR-004/007/009 |
| D5 | Two independent changes sharing a component, one repeated correlated observation, and a one-failure prompt | No forced failure-count partition, no silent candidate loss or false independence | FR-009/010 |
| I1 | Official three-flag invocation on small Track 1-shaped corpus with IDs 9/42 | Joined scope/findings/evidence, blank prediction rows, zero usage and truthful discovery status | FR-010/011 |
| I2 | Duplicate windows with different projections; same timestamps in another deployment | Safe shared retrieval, separate per-row scope/results and correct invalidation | FR-001/005/010/014 |
| I3 | Empty query inventory, invalid scope, unavailable sources and no findings | Distinct valid-empty, unsupported, unavailable and completed-no-candidates states; explicit exit semantics | FR-003/010–012 |
| I4 | Existing empty-output stub invocation and new discovery validator | Both mode contracts tested independently; neither claims official answer validity | FR-011 |
| R1 | Cold source preparation and repeated lookup; change source/policy, interrupt preparation | Correct compatible reuse or rebuild; no false completeness or source escape | FR-004/005/014 |
| R2 | Forced stage deadline/volume exhaustion followed by another valid case | Partial status, retained coverage/stop reason, previous checkpoint preserved and final nonzero exit | FR-010/012/013 |
| R3 | Fresh isolated Docker build/run, 20 declared development cases, 2 CPUs/8 GB, network disabled | No local-index prerequisite; runtime caps honored including preparation; measured completion/memory/time | FR-005/011/013 |
| R4 | Replay completed runs with identical inputs/policy/work limits; replay forced deadline runs at recorded batch boundaries; audit every source pointer | Equal completed findings and equal partial findings at identical replay boundaries; live deadline variation retains explicit coverage; no labels or exposed cases misrepresented as held-out | FR-009/014 |

## Constitution review

### OpenRCA adoption amendment

| Case | Independent fixture or action | Required result | Requirements |
|---|---|---|---|
| O1 | Renamed deployment, changed replica count, missing required field, unavailable KPI and mixed seconds/milliseconds | Discover exact current identities; explicit schema/field errors; normalized timestamps retain raw values; no guessed duration unit | FR-015 |
| O2 | Successful, valid-empty, invalid-argument, unavailable, failed and truncated discovery operations | Question/scope/policy/source/timing/status recorded for every attempt; distinct outcomes and source-linked observations | FR-016 |

These checks add schema and audit acceptance only; final predictions remain blank for discovery mode. See [ADR 0006](../../docs/adr/0006-bounded-investigation-operations.md) and [feature 007](../007-evidence-backed-diagnosis/spec.md).

Evidence-first behavior is enforced by D1–D5/R4; bounded retrieval and resource linkage by D4/R1–R3. Model routing and routed-versus-single-model evaluation remain final-deliverable requirements and are not claimed by a no-call discovery stage. Interpretation correctness, empirical differences and RCA accuracy are separate claims. Runtime integration retains feature 002's intermediate blank-prediction exception; this is not permission to submit blank answers as a completed Track 1 agent.

No new governance exception is created beyond the previously authorized intermediate harness milestone. The implementation plan must carry the deferred final-diagnosis/model/evaluation gates and their owner (project maintainer). User preference for Luna xhigh TDD implementation with all code reviewed in the originating task remains applicable when implementation is requested; this document makes no code changes.
