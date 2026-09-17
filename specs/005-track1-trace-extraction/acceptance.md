# Acceptance matrix: Track-1 trace extraction

Status: planned verification, 2026-09-17. Authority: [specification](spec.md), [ADR 0009](../../docs/adr/0009-track1-trace-extraction.md).

Expected records, relations, values, and coverage outcomes must be authored independently before execution. A second call to the implementation under test is not an oracle. Fixtures use synthetic identities and public schema, not benchmark answers.

| Case | Independent scenario and expected result | Requirements | Outcomes |
|---|---|---|---|
| T01 | Unsorted CSV with quoted delimiters/newlines, late physical root, blank type, unfamiliar statuses, and invalid timestamp: exact raw records/logical locators, explicit unplaceable-time record, no prefix cutoff or success filtering. | FR-001–004, FR-011 | SC-001–003 |
| T02 | Exact interval bounds, changed host timezone, millisecond starts and separately declared duration scale: correct half-open membership, no 1000× or eight-hour error. | FR-003–004 | SC-002 |
| T03 | Trace interleaved across dates with out-of-window descendants: recover all enumerated spans; remove a partition and require explicit limited coverage. | FR-001, FR-005 | SC-001–002 |
| T04 | Repeated span IDs across traces/deployments, identical/conflicting duplicates: no cross-scope joins/overwrites; reconcile raw/logical counts and ambiguity. | FR-006, FR-011 | SC-001–003 |
| T05 | Missing parent, cycle, disconnected fragment, absent/multiple roots, known empty children: preserve records and distinct quality states. | FR-005–009 | SC-002–003 |
| T06 | Valid graph with zero, negative, nonnumeric, and large durations: graph facts survive; zero stays zero, invalid timing unavailable, valid endpoints preserve declared precision. | FR-002–003, FR-007, FR-009 | SC-002 |
| T07 | New frontend replicas and non-frontend traces, ambiguous entry binding: use observed justified identities, retain other traces, invent no entry/target binding. | FR-004, FR-008–009 | SC-001, SC-004 |
| T08 | Same-emitter ancestry, caller-side RPC, zero-duration parent preceding child: preserve recording identity without invented remote target, retry, transit time, success, or cause. | FR-007, FR-009 | SC-002–003 |
| T09 | Reference descendant ending at/after cutoff, unavailable endpoint, partial recovery, query ending after slice: correct exclusions, retained completion, reconciled denominators. | FR-003, FR-005, FR-010 | SC-001–003 |
| T10 | Add/remove child type, change multiplicity, mark recovery incomplete: correct set/multiset facts and visible unmatched/unknown observations, no extraction score. | FR-007, FR-009–010 | SC-002–003 |
| T11 | Changed content under same path, changed conversion/version/deployment, killed preparation: no stale/partial current view; preserve completed identified results. | FR-001, FR-012 | SC-005 |
| T12 | Oversized trace/response and exhausted budgets: exact partial coverage, safe completion state and continuation where possible, no falsely complete shape/reference. | FR-005, FR-007, FR-013 | SC-001–003, SC-006 |
| T13 | Consistent record/ID renaming, ordering, date shifts, repartitioning: inverse-mapped semantic equivalence with accurate transformed provenance. | FR-001, FR-006, FR-011–012, FR-015 | SC-004–005 |
| T14 | Seven task projections, reordered/non-contiguous IDs, duplicate windows, multiple failures, empty observed interval, outside-coverage interval: preserved cases, honest shared costs, no incident-count candidate cap. | FR-004, FR-013–014 | SC-003, SC-007 |
| T15 | Trap answer paths, scoring fields, cached predictions, network, and models during cold/warm operation: zero reads/calls; evidence or explicit unavailability still returned. | FR-013–015 | SC-007 |
| T16 | Identified two-day development snapshot and independent scan: hashes/counts and selected/recovered records agree exactly; measured cold/warm costs fit predeclared runner allocation or fail explicitly. | FR-001, FR-005, FR-011–013, FR-015 | SC-001, SC-003, SC-005–006 |

## Evidence to retain

- Source identities and independently frozen expectations; extracted artifacts, counts, quality states, and oracle differences for every T01–T16 case, including failures.
- Exhaustive finite-fixture provenance/reconciliation plus source-linked real-data samples; raw and logical counts, coverage, membership identities, and rule versions.
- Cold preparation, fingerprint validation, warm selection, recovery, derivation and serialization time; peak memory, source-read work, artifact bytes, and interruption behavior. Shared work is not multiplied across cases.
- The plan's extraction budget within the runner envelope and clean-machine rehearsal, including any budget failure. Prior research timings cannot substitute for these checks.
- Extraction correctness is separate from diagnosis accuracy. Any later scoring/routing evaluation must freeze evidence and outputs before label access and retain exposure accounting.
