# Tasks

- [x] Inspect existing encoding, source format, domain vocabulary and ADRs.
- [x] Record isolated specification and implementation plan.
- [x] Use the public partition/early-return/description boundary specified in
  the user's request; user also explicitly requested practical parallel agents.
- [x] Implement partitioning and deferrals through Luna extra-high TDD slices.
- [x] Implement deterministic description construction through TDD slices.
- [x] Document the public contract and provide standalone packaging.
- [x] Review all new code; repair demo blockers and record broader findings.
- [x] Verify standalone installation, the nonempty demo and core regressions.
- [x] Reconcile specification, plan and tasks with the user's demo-first scope.

## Resumed follow-up: final three-step scope

The user explicitly resumed remaining work, then requested wrapping up with
only these three material steps on the isolated follow-up branch:

- [x] Fix partition identity, evidence recovery and conflicting parent links.
- [x] Finish description structural validation and scoped context qualifications.
- [x] Run core checks, independently install, review and commit for handoff.

Delivered behavior includes typed scalar identity keys, exact root markers,
unique per-call evidence addressing, valid rows retained after malformed duplicate
envelopes, equivalent unit handling, per-record operation deferrals, all observed
parent candidates and linear conflict-reference storage. Broader additional
hardening and new capabilities are deferred per the final user instruction.
