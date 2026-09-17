# S01: structural fidelity supported on three synthetic fixtures

**Decision: `supported_on_fixture`.** Run `20260917-s01-001` recovered all
required structural facts, preserved T0/T1 equivalence under the frozen policy,
and retained T2's one added catalog child. First differing fact: none.

| Fixture | Spans | Parent edges | Catalog occurrences | Same-entity pairs | Different-entity pairs |
|---|---:|---:|---:|---:|---:|
| T0 | 7 | 6 | 3 | 2 | 19 |
| T1: renamed IDs, shuffled rows | 7 | 6 | 3 | 2 | 19 |
| T2: added catalog#1 child | 8 | 7 | 4 | 4 | 24 |

The added node is `0ab7`, operation `catalog.get_product`, recording entity
`catalog#1`, with parent `8af0`. All existing T0 observations remain unchanged
in T2. Both occurrences on the original catalog#1 entity and the distinct
catalog#2 occurrence survive. Pair checks cover all unordered span pairs;
different-entity expectations are the complement of the authored same-entity
relations, not a separately annotated negative set. A constant output fails
the contrast gate.

The decoder recovered facts using packet contents alone. A separate provenance
audit resolved every synthetic source pointer and recovered all nine raw fields
across 22 records. Status interpretation, business outcome, interaction role,
backend target and instrumentation completeness remain explicitly unknown.

## What this means

A minimal normalized graph can preserve the declared facts on these fixtures
without treating renamed identifiers or storage order as structural differences.
It also preserves a small meaningful change. This is a usable control for the
next fidelity experiment, not evidence that an advanced symbolic representation,
behavior classifier, or LLM is needed.

| Fixture | Compact source fixture bytes | Cold packet bytes | Compact provenance bytes |
|---|---:|---:|---:|
| T0 | 1,548 | 3,455 | 1,181 |
| T1 | 1,548 | 3,455 | 1,181 |
| T2 | 1,741 | 3,645 | 1,336 |

Cold packets include dictionary, policy, context and reference metadata. They
are larger than these tiny source fixtures. The source fixture is not a matched
fidelity compression baseline, so this is descriptive size accounting, not a
compression conclusion. No token counts or model-cost savings are inferred.

The result remains provisional against authored synthetic expectations, checked
by a separate agent. It does not establish real-telemetry fidelity, handling of
missing/conflicting spans, general graph behavior, duration semantics, causal
interpretation, or LLM accuracy. There was no independent human annotation.

## Review and validation

Luna subagents were requested at extra-high reasoning for repository review,
fixture/method review, execution, and artifact audit. The retained
[pre-execution review](pre-execution-review.md) covers 77 existing authored code
files plus the new implementation. Existing runner and older experiment
limitations were documented; they are not dependencies of this run.

The first test preflight passed 9/10 cases. Its failing corruption test carried
an invalid index into a subsequent missing-digest case. Resetting the sidecar
between cases repaired that test; no expected structural fact or codec behavior
was relaxed. The failed [log](test-execution-attempt-001.txt) and exact code
snapshot are retained. The corrected [test run](test-execution-attempt-002.txt)
passed **10/10**, including entity/edge mutations with counts unchanged,
provenance corruption, and prevention of run-directory reuse.

One S01 experiment attempt completed. Experiment model calls: **0**. No real
telemetry was read, and no earlier experiment outputs or final-runner code were
modified. The [post-run audit](post-run-audit.md) records independent checks of
the saved evidence.

## Evidence and next action

- [Run result](../../../../data/experiments/semantic-encoding-v1/S01/20260917-s01-001/result.md)
- [Manifest and hashes](../../../../data/experiments/semantic-encoding-v1/S01/20260917-s01-001/manifest.json)
- [Exact fact differences](../../../../data/experiments/semantic-encoding-v1/S01/20260917-s01-001/fact-diff.json)
- [Implementation, graph diagrams, and reproduction command](../../../../experiments/semantic_encoding_v1/README.md)

The run directory also retains all three packets, decoded facts, provenance
sidecars, structural signatures, frozen inputs and a code snapshot. It is under
Git-ignored `data/experiments/`; retain that directory when sharing the evidence.

**Stop after S01**, as specified by the handoff and active A1 plan. The next
smallest separately scoped experiment is S02: freeze and independently review
the complete fact sheet for the single indexed real trace before testing its
round-trip. S02–S09 were not started.
