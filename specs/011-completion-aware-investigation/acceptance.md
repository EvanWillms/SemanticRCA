# Acceptance matrix: completion-aware investigation

Planned checks only; none are executed by this documentation change. Use
independently authored evidence and expected trajectories, controlled assessments,
fake operation outcomes and a controllable clock. Do not derive expected
sufficiency from the model response under test.

| Case | Fixture/action | Required outcome | Requirements | Outcomes |
|---|---|---|---|---|
| L01 | Initially sufficient packet | Initial assessment; zero follow-ups; accepted sufficiency for current evidence | FR-001/002/003 | SC-001/002 |
| L02 | Replica-pressure versus shared-dependency explanations | Named gap; one comparison; result appended and assessed before completion or next action | FR-001/002/004 | SC-001/002 |
| L03 | Invented reference, wrong entity/time, legal-looking answer with contradiction, missing incident support | Reject each false completion; preserve failed checks and valid evidence | FR-003/008/011 | SC-001/004 |
| L04 | Partial projection with non-material uncertainty | Complete supported requested fields without forcing unnecessary work; retain qualification | FR-003/009 | SC-001/004 |
| L05 | Missing source with an alternative available operation | Reject unsupported blocker and retain useful path | FR-004/005/008 | SC-002/003 |
| L06 | Required missing source or capability, then exhausted useful actions | Distinct reason and unresolved gap for each fixture; no global impossibility claim | FR-005/009/010 | SC-003/004 |
| L07 | Same unchanged request twice; reworded hypothesis; increased confidence | Repeats rejected/audited; no fake progress; two consecutive non-progress attempts stop | FR-006/007/011 | SC-003 |
| L08 | Valid empty selection adds coverage; later duplicate view | First outcome can reset progress; duplicate adds no independent evidence or progress | FR-001/006 | SC-002/003 |
| L09 | Invalid scope/resource/operation and transient retry | Reject before execution; charge attempts; only eligible bounded transient retry allowed | FR-004/006/007/008 | SC-002/003 |
| L10 | Malformed assessment, missing action, unsupported blocker after repair | Bounded recorded repair within four calls; `invalid_assessment` if unrecoverable with capacity remaining | FR-007/008/011 | SC-003/004 |
| L11 | Timeout, permanent provider failure, unknown usage | Bounded recovery; provider reason or recorded earlier limit; no additional live call required to finalize | FR-007/008/010/011 | SC-003/004 |
| L12 | Initial, mid-loop and final-step assessment/operation/time/cost limits; repairs consume capacity | No work without reserves; at most three operations/four assessment attempts; limit named; final result assessed if reserved capacity survives | FR-002/007/009/010 | SC-002/003/004 |
| L13 | Final observation arrives at hard deadline or contradicts earlier draft | Retain as unassessed; hard-stop reason; no stale sufficiency or silent reuse of contradicted support | FR-002/009/010 | SC-004 |
| L14 | Weak support with legal choices; more requested incidents than supported explanations | Legal best guess, unsupported selections explicit, no fabricated independent incidents or adequacy upgrade | FR-003/009/010 | SC-004 |
| L15 | Unsupported scope or impossible legal assembly after earlier blocked exit | No access for unsupported scope; failed blank output; retain earlier stop reason plus assembly failure | FR-009/010/012 | SC-004/005 |
| L16 | Replay fixed evidence, assessments, policies and clock decisions | Same decision history, progress and terminal reasons; separate stop/status/adequacy fields | FR-001/009/011 | SC-005 |
| L17 | Stub/discovery regressions, label-access probe, case persistence failure | Existing mode behavior and isolation preserved; earlier checkpoints survive; no default diagnosis switch | FR-010/012 | SC-005 |
| L18 | Completion after third follow-up; rejected completion at cap; assessment/operation returns no calls | Valid final sufficiency accepted without more tools; unsupported completion or silence never treated as success; bounded explicit exit | FR-002/003/007/008 | SC-001/003/004 |

## Constitution review

Evidence-first reasoning: L01–L06/L13–L15. Bounded query access and unchanged
comparison policies: L02/L09. Cost and unattended runtime: L07–L12/L18.
Reproducibility and inference isolation: L16–L17. Submission compatibility and
truthful artifacts: L14–L17. The routed-versus-single-model held-out study and
final release remain feature 002 obligations; scripted loop correctness proves
neither causal accuracy nor sufficient production budgets.
