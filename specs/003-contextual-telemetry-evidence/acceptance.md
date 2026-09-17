# Acceptance matrix

**Status**: planned checks; none executed as part of recording these documents. Authored inventories and expected findings must be fixed independently of the implementation being tested. See [spec](spec.md).

| Case | Independent setup | Required result | Requirements |
|---|---|---|---|
| R1 | Interleaved spans across two date partitions; child outside selection window | All available records of selected traces recovered; unrelated traces excluded | FR-001–003 |
| R2 | Same span/trace strings in distinct namespaces; conflict and orphan planted | No cross-namespace join; conflicts and missing ancestry surfaced | FR-003, FR-009 |
| R3 | Absent partition, bounded result, interrupted build, then changed source snapshot | Coverage/truncation explicit; incomplete or stale view not presented as compatible complete data | FR-004, FR-012 |
| R4 | Repeat window/trace/component queries against prepared data and scan inventory | Identical record sets and provenance; no repeated full-source parse; preparation/reuse/storage/memory measured separately | FR-004, FR-013 |
| R5 | Trace starts before cutoff and ends after; second trace has uncertain duration units | Strict pre-cutoff and start-selected policies produce declared eligibility; no unsupported online-availability claim | FR-002, FR-005–006 |
| B1 | Compatible references and independently planted level, trend, frequency, and attribute differences | Correct difference descriptions with units, exposure, reference versions, and source evidence | FR-005–007, FR-012 |
| B2 | Zero median/MAD, sparse tail, unknown unit, and incompatible context | Declared qualification/refusal; no arbitrary denominator, probability, or health assertion | FR-006–007 |
| B3 | Matching requests plus extra/missing call and unknown request type | Conditional latency matching preserves changed/unmatched cases for appropriate comparison | FR-007–008 |
| B4 | Contaminated history, peer-wide disturbance, and conflicting eligible views | Contamination/disagreement retained; no reference selected for the desired largest score | FR-005–006, FR-008 |
| B5 | Tiny relative outlier, large absolute spike, sustained shift, and overlapping episodes | Priority follows declared policy; magnitudes and temporal distinctions survive; shared evidence not multiplied | FR-007–008, FR-012 |
| B6 | Collection loss, observed absence with complete coverage, and revised baseline | Missingness cases distinguished; baseline revision preserves original observations and earlier findings | FR-007, FR-012 |
| L1 | Client DB span with no target plus service-level Redis traffic evidence | Resource expansion supported; individual operation target remains unresolved | FR-009–010 |
| L2 | Explicit span ancestry, placement, service dependency, and temporal coincidence | Each relationship kind/scope preserved; no contextual edge becomes exact request linkage | FR-009–010 |
| L3 | Endpoint reused over time; two possible replicas; similar-looking service names | Time support, alternatives, and distinct identities preserved | FR-003, FR-009–010 |
| L4 | Persistent connection and request-like log ID without a validated mapping | No invented per-operation join or trace-ID equivalence | FR-009–010 |
| L5 | Shared source evidence, cyclic relationships, and exhausted expansion budget | Evidence deduplicated; traversal bounded; unvisited frontier and stop reasons reported | FR-011–012 |
| G1 | Replay unchanged sources/policies, then change each version independently | Same content on replay; changed identities/qualifications on update; every product resolves to provenance | FR-001, FR-012 |
| G2 | Inspect integration under the runner's data and budget constraints | No developer-local artifact dependency; output restrictions and preparation costs honored | FR-013 |

## Success-criterion coverage

SC-001: R1–R5. SC-002: B1–B6. SC-003: L1–L5. SC-004: G1 plus provenance assertions in every case. SC-005: R4. SC-006: independent case setup plus G2 and review of the existing incident contract.

## Constitution review

Evidence-first diagnosis is supported through provenance and explicit uncertainty; query-bounded access through selection, prepared retrieval, and budgets; reproducibility through snapshots and frozen policies. This feature makes no model-routing change and inherits the runner's execution/submission constraints. Implementation planning and tasks follow specification; documentation completeness does not establish implementation or empirical performance.
