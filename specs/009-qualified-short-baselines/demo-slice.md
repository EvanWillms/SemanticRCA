# First demo cut line: Baselines → comparative descriptors

User priority, 2026-09-17: make the smallest honest happy path runnable as soon as possible, using only core TDD coverage. This note orders delivery; it does not mark the full feature 009/010 acceptance matrices complete or change their policy semantics.

Implementation owner: [Implement baseline descriptor plans](codex://threads/01a0b13b-d809-7c80-a199-c868d40b8781). Current executable handoff and passing command belong in [coordination status](../../coordination/baseline-comparison/status.md).

## Demo gate

One public Python call sequence or CLI invocation reads the small authored CSV fixture, produces a frozen five-minute contextual baseline, describes query requests, and exposes an inspectable result. A runnable library entrypoint plus one passing source-to-descriptor check is enough for the first handoff; a polished CLI or complete artifact system must not delay it.

Show the known fixture facts directly:

- Twenty matching references across three occupied minutes, with counts 8/6/6 and median 10 ms; a 12 ms query has signed excess +2 ms.
- A below-median or equal query remains in complete results with −2 ms or zero excess, rather than disappearing from the population.
- A zero reference remains usable for signed excess; an unsupported or missing context produces an explicit unavailable outcome rather than zero or a guessed fallback.
- The observation, reference identity/count, qualification and actual source locator remain inspectable. A positive difference is not presented as a diagnosis or verified anomaly.

Keep existing structural and six-slice behavior if already in the vertical path, but do not add a new demonstration matrix before the first passing handoff. Report missing behavior explicitly. A late missing context must not mutate the frozen catalog.

## Core TDD only

Use the already agreed public producer and consumer interfaces. Run one failing behavior check, implement the minimum to pass it, then move to the next slice. Do not build an exhaustive suite first, mock internal helpers, or generate expected values with the implementation under test.

1. **Supported reference to signed descriptor**: the authored CSV path yields the independently known 10 ms reference and +2 ms descriptor, preserving a nonpositive outcome and source links.
2. **Support abstention**: insufficient/unmatched reference produces unavailable comparison and stays visible. Existing count/time policy remains intact.
3. **Zero handling**: zero reference still yields finite signed excess; any implemented optional ratio/MAD fields retain explicit undefined states.

These are the first evidence targets, not an instruction to rewrite equivalent core tests already passing. Retain red/green evidence when tests are newly written; do not retrospectively claim TDD for existing code. Small extra tests are justified only by an actual blocker found in this path.

## Defer beyond the first handoff

- Full B01–B12 / D01–D12 coverage and all 57 development windows.
- SQLite optimization, scale benchmarks, cache performance and storage tuning.
- Exhaustive malformed-source, corruption, pointer-adversary, interruption and relocation cases.
- Optional ratio/MAD diagnostics, generalized policy configuration and expanded measurement families.
- Container rehearsal, complete JSON bundle publication and a polished CLI if a working library/test entrypoint is available first.
- Default discovery integration, model calls, diagnosis and alert calibration.

Do not drop essential source/context checks, finite arithmetic, unavailable outcomes or reference qualifications to obtain a pass. Unimplemented evidence validation must be labeled as such; it cannot produce a trusted/fully validated claim. Deferred work remains in the original plans.

## Checkpoint and handoff

Immediately after the first passing end-to-end check, commit only owner changes and publish: exact command, short expected/actual output, available public signatures, checkpoint hash and remaining gaps. Set coordination state to ready only with that executable evidence. Broader hardening follows the demo handoff rather than blocking it.
