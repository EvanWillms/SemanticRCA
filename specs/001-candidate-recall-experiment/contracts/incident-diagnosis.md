# Bounded-window incident diagnosis contract

**Status**: Required downstream interface; not part of the first compression experiment.
**Updated**: 2026-09-17
**Definition**: [ADR 0001](../../../docs/adr/0001-benchmark-failure-definition.md).

The diagnostic problem is to identify **when, where, and why** within a bounded incident window. An incident is represented by `(occurrence_time, component, reason)`. Each request asks for a projection of that tuple for each designated failure.

## Investigation inputs and task projections

Allowed scope inputs are request ID, task type, deployment, bounded time interval with timezone, supplied failure count, and requested fields. They constrain the search and response; they are not symptoms or telemetry evidence. `scoring_points` and answer-derived fields belong only to evaluation and must be stripped before passing requests to an encoder, reference selector, or diagnostic agent.

The supplied development query file contains these request counts, verified from `task_index` without using answer contents:

| Task | Requested fields | Requests |
| --- | --- | ---: |
| task_1 | When: occurrence time | 12 |
| task_2 | Why: reason | 10 |
| task_3 | Where: component | 8 |
| task_4 | When + why | 7 |
| task_5 | When + where | 10 |
| task_6 | Where + why | 12 |
| task_7 | When + where + why | 11 |
| Total | | 70 |

There are 44 single-failure and 26 two-failure requests. These are request counts, not independent incident counts. The [label-free audit](../../../docs/research/track-1-trace-audit.md) found 57 distinct windows. The same or overlapping windows may expose the same incidents under different projections; related windows/incident groups must not cross later tuning/evaluation splits. Grouping must not fabricate missing tuple fields or pair partial answers ambiguously.

## Evidence and hypotheses

1. Scope retrieval to the investigation, with explicit context buffers and ancestry retrieval as needed. Record any incompleteness.
2. Use telemetry to infer onset, originating component, and fault reason; iterate among them as evidence requires. No fixed causal-search order is imposed.
3. Maintain incident hypotheses with separate IDs and field associations. Preserve competing hypotheses, shared evidence, and uncertainty. Do not force each observation into one incident because the query supplies a count.
4. Return only requested fields, using the organizer's exact naming and formatting contract. An unrequested field may remain unknown internally.

The first observed slow span is not necessarily the fault onset; the recording or affected component is not necessarily the originating component; an observed repeat pattern is not the fault reason. Each such step is an inference requiring evidence. Success verification for a comparison cohort is a separate concept from benchmark failure designation.

## Output invariants

- Emit exactly the supplied number of incident objects. Wrong count invalidates the case under the official contract.
- Preserve each incident's time/component/reason association through projection and reordering. Failures need not be listed chronologically; the evaluator considers ordering permutations. Never independently sort times, components, and reasons.
- Use exact component identifiers, including meaningful replica suffixes; service-role aliases must resolve back to original identities.
- Use the exact organizer fault-reason vocabulary. It distinguishes container from node faults and includes CPU/memory pressure, I/O load or consumption, disk-space consumption, network disruption, and process termination. Descriptive behavior labels such as oscillation or retry amplification do not replace those reasons.
- Render requested times in UTC+8 with the official 60-second tolerance. Preserve internal timezone, precision, and uncertainty; the tolerance is a scoring rule, not permission to erase observation timing.
- Serialize requested keys in relative order `datetime`, `component`, `reason`; omit unrequested keys and avoid newlines in values. Use the official formatter/validator when implemented because scoring uses regex extraction.
- Emit a best guess as required by the benchmark, while stating uncertainty, alternatives, and evidence limitations in `evidence/<row_id>.md`. Internal unknown observations must not be turned into false certainty to satisfy answer shape.

## Isolated downstream acceptance checks

These checks use synthetic supplied hypotheses; they do not establish diagnosis accuracy:

- All seven projections return exactly their requested fields.
- One- and two-incident cases preserve tuple associations, even if the second incident starts earlier.
- Aliases resolve to exact component IDs without merging replica/node distinctions.
- UTC conversion, 60-second boundary behavior, reason spelling, count, and key ordering agree with the pinned official formatter/scorer.
- Agent input contains no scoring points or answer-derived features; evaluator access is separate.
- Duplicate/overlapping views stay in one evaluation group, and unresolved partial-label associations remain unresolved.

## Sources

- [Official Track 1 README](../../../../hackathon-2026-official/track-1/README.md): telemetry-based diagnosis and submission artifacts.
- [Official data guide](../../../../hackathon-2026-official/track-1/docs/data.md): task projections and exact reason vocabulary.
- [Official scoring guide](../../../../hackathon-2026-official/track-1/docs/scoring.md): field precision, object count, ordering, key order, best guesses, and uncertainty.
- Local `data/track-1/dev/query_dev.csv`: 70-request task/count inventory. Its scoring points are evaluator-only; this document does not reproduce incident answers.
