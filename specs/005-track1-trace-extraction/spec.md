# Feature Specification: Track-1 trace extraction pipeline

**Feature Branch**: `006-track1-trace-extraction`

**Feature Directory**: `specs/005-track1-trace-extraction` (directory numbering is independent of branch numbering)

**Created**: 2026-09-17

**Status**: Specified; ready for planning, implementation and acceptance pending

**Input**: User request: “ADR and feature-spec the related trace extraction pipeline tightly tied to the track-1 dataset”, grounded in the supplied `track-1/docs/data.md` and `track-1/docs/scoring.md` and the completed short-window baselining study.

## User Scenarios & Testing

### User Story 1 — Obtain trustworthy traces from a supplied Track-1 bundle (Priority: P1)

An unattended investigator supplies a dataset and public case scope, then receives selected recorded executions with original identifiers, source references, and coverage. The process works on another deployment without editing known component names or dates.

**Why this priority**: Missing or misbound records undermine every later comparison and diagnosis.

**Independent Test**: Use a Track-1-shaped fixture with independently enumerated records, then repeat with consistently renamed components and shifted dates. Compare evidence and provenance with the expected inventory; no diagnoser, model, or labels are required.

**Acceptance Scenarios**:

1. **Given** unsorted, interleaved records, **when** spans are selected in a half-open window, **then** every eligible record is considered, including records physically after out-of-window rows, and the selection rule is recorded.
2. **Given** selected trace IDs with records outside the window or in another available partition, **when** recovery completes, **then** all available matching records are returned or accessible through declared continuation, with source coverage distinct from graph quality.
3. **Given** unfamiliar deployment components and dates, **when** the same selection intent is applied, **then** identities come from that bundle; no development component, date, or expected answer is substituted.
4. **Given** an ambiguous entry rule, missing partition, or unsupported schema, **when** extraction is requested, **then** the limitation is explicit and cannot produce an apparently complete empty evidence set.

### User Story 2 — Inspect execution structure and timing with their limitations (Priority: P1)

An evidence consumer examines parent relationships, recording components, duration, and direct-child structure while seeing what could not be established. It can distinguish a recorded change from a retrieval or timing limitation.

**Why this priority**: Timing gaps, caller-side recording, and missing spans can otherwise become invented network or causal explanations.

**Independent Test**: Inject duplicate/conflicting identities, missing parents, cycles, multiple roots, empty children, invalid durations, and cross-deployment ID collisions. Compare each quality dimension and derivable fact with independently authored expectations.

**Acceptance Scenarios**:

1. **Given** a span ID repeated in another trace or deployment, **when** parent links are resolved, **then** no cross-trace or cross-deployment join is introduced.
2. **Given** identical duplicate rows or conflicting rows for one span identity, **when** evidence is produced, **then** all source records remain accounted for, duplicate/conflict status is visible, and no arbitrary winner creates an unqualified execution.
3. **Given** fully recovered records with missing ancestry or multiple roots, **when** structure is described, **then** records remain available and unresolved graph facts are explicit. A resolved root with no recorded children is distinguished from unknown structure.
4. **Given** valid parent links but an invalid duration, **when** evidence is derived, **then** structural facts remain inspectable while duration/endpoints are unavailable. Zero duration and blank type remain recorded values, not automatic failures.
5. **Given** a caller-recorded operation naming another service, **when** a target identity is requested, **then** the recording component and unresolved target are retained unless independent linkage supports more. Parent/child timing alone is not labelled network delay or fault cause.

### User Story 3 — Supply reproducible inputs to contextual comparison (Priority: P1)

A comparison consumer obtains frontend-root observations for separately declared historical and query intervals. It reproduces membership, inspects structural changes independently of matching, and explains exclusions without changing raw extraction.

**Why this priority**: The experiment demonstrated useful short references but also low coverage, wide uncertainty, and reference contamination. These belong in comparison qualifications, not hidden extraction filters.

**Independent Test**: Use roots around a cutoff, cross-partition descendants, unknown endpoints, and changed direct-child sets/counts. Verify facts and membership without an anomaly threshold or incident answer.

**Acceptance Scenarios**:

1. **Given** explicit frontend entry criteria and an observed component allowlist, **when** roots are selected, **then** membership is identified by deployment, trace, and root span; operations, types, recording components, and statuses remain raw and traceable.
2. **Given** completed-before-cutoff reference eligibility, **when** any recovered endpoint equals or exceeds the cutoff, **then** the observation is excluded with its reason and duration retained. Unresolved required endpoints or recovery cannot be treated as completed.
3. **Given** a query root starting inside a slice but ending outside it, **when** its trace is recovered, **then** completion is retained rather than truncated at the slice end.
4. **Given** a new child operation, changed multiplicity, or unknown structure, **when** an observation cannot match a shape-conditioned reference, **then** it remains visible to structural analysis; extraction invents neither a match nor a zero-departure score.
5. **Given** a changed reference policy with unchanged sources, **when** selection is repeated, **then** membership may change but raw observations, source identities, and recorded relationships do not.

### User Story 4 — Reuse preparation within the unattended run (Priority: P2)

An operator prepares trace access once and reuses it across cases. A reviewer can attribute preparation cost, detect stale inputs, and reproduce results. Interruptions and budget limits leave explicit partial status and preserve completed work.

**Why this priority**: Millions of records per day make repeated preparation costly for downstream diagnosis.

**Independent Test**: Compare cold preparation and warm retrieval with a scan oracle; change a source under the same name, interrupt preparation, and exhaust a declared budget. Measure elapsed time, memory, bytes, and source-read work separately.

**Acceptance Scenarios**:

1. **Given** unchanged sources/rules, **when** prepared evidence is reused, **then** records and semantic memberships match the independent scan without reparsing every source for each query. Fingerprint validation cost remains separately visible.
2. **Given** a changed source, deployment, conversion policy, or extraction version, **when** reuse is attempted, **then** stale results cannot serve as the new snapshot. A completed old view may remain identified as old while replacement proceeds.
3. **Given** interrupted preparation or an exhausted budget, **when** the run continues, **then** incomplete recovery, continuation, and unavailable derivations are explicit; completed outputs are preserved.
4. **Given** reordered query rows, repeated windows, or multiple requested failures, **when** evidence is reused, **then** original case IDs and scope remain attached. Shared work is accounted for once and incident count does not cap trace candidates.

### Edge Cases

- CSV records contain quoted commas/newlines or empty fields; physical line numbers are not logical record positions. Malformed CSV preventing reliable record boundaries cannot yield a complete inventory.
- Guide cardinalities differ from inspected data; unfamiliar operations/types/statuses remain raw. Blank `parent_span` is the initial root convention; unfamiliar sentinels are not guessed to mean root.
- A trace has no qualifying frontend root, multiple roots, duplicate root rows, a cycle, or disconnected records. It remains inspectable without being forced into one frontend request.
- Root and child cross midnight; an adjacent partition may be present, absent, or outside the snapshot. A child can appear earlier than its parent because precision and clock alignment are limited.
- Negative, nonnumeric, zero, and very large durations require distinct handling. Identity, structure, timing validity, and reference eligibility can disagree without deleting records.
- New replica counts, dates, repeated IDs across deployments, and identical source basenames must not collide with a development cache.
- Empty observed intervals and intervals outside source coverage are different outcomes. Oversized traces/responses require continuation or explicit truncation, not complete-trace claims.
- Seven task types request different fields; supplied failure count establishes neither which traces matter nor how many traces exist.

## Requirements

### Functional Requirements

- **FR-001 — Track-1 source boundary**: Accept a caller-supplied dataset location and identified deployment; inventory available trace partitions with content identity, relative path, logical record counts, schema/extraction version, and completion status. Runtime MUST NOT require a developer path, fixed dates, case count, or shipped development index.
- **FR-002 — Loss-accounted parsing**: Parse the documented trace fields and public query records with format-aware readers. Preserve raw values and unknown nonstructural values. Invalid typed fields MUST retain source-linked rejection/quality records where boundaries remain recoverable; records with unusable timestamps remain unplaceable in time rather than being assigned to a guessed interval. Unrecoverable syntax/schema errors MUST prevent a complete-build claim.
- **FR-003 — Dataset timing**: Interpret trace starts as epoch milliseconds and calendar scope as UTC+8 regardless of host timezone. Keep raw duration, interpreted units, conversion version, and confidence separate. Mark the initial microsecond duration interpretation provisional; invalid/unresolved conversions MUST NOT fabricate endpoints. Derived precision MUST NOT exceed supported source precision.
- **FR-004 — Explicit selection**: Record deployment, time bounds, selection basis, component/entry criteria, and policy version. Enforce half-open start intervals and consider all matching records regardless of physical order. Gold answers, expected fault components, latency, or interpreted success MUST NOT become hidden selection filters.
- **FR-005 — Recorded-trace recovery**: Search the declared available inventory for each selected execution independently of candidate time range. Preserve out-of-window/cross-partition records, searched/missing sources, and partial/truncated status. Complete recorded recovery MUST NOT be presented as complete instrumentation.
- **FR-006 — Identity and duplicates**: Scope traces to source snapshot/deployment and spans to their traces. Resolve parents only within that scope. Keep duplicate/conflicting raw records addressable and logical observations separately counted. Ambiguity MUST block unqualified derivations that require a unique record.
- **FR-007 — Independent quality**: Report source coverage, identity resolution, graph quality, and timing validity independently, including missing parents, multiple roots, cycles, disconnected spans, and incomplete recovery. Distinguish empty recorded children from unknown structure. One quality limitation MUST NOT silently discard evidence available in another dimension.
- **FR-008 — Extraction views**: Support selection of available component/time spans, recovery of explicit trace identities, and a separately declared frontend-root view. Freeze the frontend view's observed deployment-specific allowlist and entry criteria. Retain non-frontend and unresolved-root executions without forcing them into that view.
- **FR-009 — Execution facts**: Where resolvable, retain raw root operation/type, recording component, parent links, span counts, valid root duration, maximum known recovered endpoint, and direct-child operation/type pairs with counts. Derivations MUST carry rules and quality; operation names/timing MUST NOT invent target replicas, errors, retries, network transit time, or causes.
- **FR-010 — Comparison handoff**: Preserve separately reproducible historical/query memberships. Completed-before-cutoff eligibility MUST reject endpoint equality/overlap and unresolved required timing/recovery, retain exclusion counts/durations, and not truncate query completion. Unmatched/unknown structures MUST remain visible. Extraction defines no default baseline window, health rule, anomaly score, or automatic fallback.
- **FR-011 — Auditable evidence**: Every returned fact, derived observation, exclusion, and coverage limitation MUST resolve to identified source records and extraction/selection rules, or state that a source was unavailable. Use logical CSV record numbering with header record 1 and first data record 2; physical line positions, if retained, are separate. Unchanged identified inputs/rules MUST reproduce semantic membership and measurements.
- **FR-012 — Safe reuse**: Reuse MUST validate source content and extraction compatibility and require completed preparation. Changed sources/interrupted writes MUST NOT be accepted as current complete views. Preserve immutable telemetry and previously completed, correctly identified results during replacement/recovery.
- **FR-013 — Bounded costs**: Require declared resource/response budgets, preserve truncation/continuation, and charge validation, cold preparation, recovery, derivation, and serialization to the run. Report elapsed time, records scanned/retrieved, memory, and artifact bytes without multiplying shared work across cases. Extraction MUST require no models, answer access, downloads, or interactive input.
- **FR-014 — Case/scoring separation**: Preserve original query identity, instruction, UTC+8 bounds, incident count, and requested fields as scope metadata. Share evidence for repeated windows without losing case associations. Extraction MUST NOT read `dev/query_dev.csv`, `scoring_points`, hidden upstream data, or cached answers. Unavailable evidence MUST NOT become a final-answer abstention rule; best guesses and prediction formatting remain downstream responsibilities.
- **FR-015 — Verifiable adoption**: Retain an independently authored fixture inventory and scan oracle covering the acceptance matrix, a source-linked two-day development comparison, and renamed-component/date-shifted fixtures. Report retrieval/derivation correctness and preparation/reuse costs separately from baseline validity, incident sensitivity, accuracy scores, or routing claims.

### Key Entities

- **Track-1 source snapshot**: Deployment-scoped partitions, source identities, schema/conversion versions, counts, and completeness.
- **Investigation scope**: Original case identity, public instruction, deployment, UTC+8 interval, failure count, and requested fields.
- **Trace selection**: Observable criteria and selected span/execution memberships, independent of later recovery.
- **Recorded span**: Raw Track-1 fields and recoverable physical source-record identities; its logical identity can be conflicted.
- **Recovered execution**: Available records for one trace identity, searched-source coverage, graph/timing quality, and continuation when incomplete.
- **Frontend root observation**: An entry satisfying the declared rule, with duration, direct-child structure, and independent quality dimensions.
- **Comparison handoff**: Historical/query memberships, execution facts, and explicit eligibility/exclusion reasons for a separate comparison policy.
- **Extraction receipt**: Source/rule identities, coverage/reconciliation results, case associations, preparation/reuse status, and measured work.

## Success Criteria

### Measurable Outcomes

- **SC-001 — Available-record fidelity**: Finite fixtures return exactly independently enumerated eligible records with **zero omitted available records, invented joins, or silent overwrites**. Bounded cases instead report their exact partial state and withheld scope.
- **SC-002 — Quality/timing fidelity**: Every planted identity, graph, timing, schema, or coverage limitation appears in its relevant dimension. Cutoff/timezone fixtures produce exact expected memberships; **zero** invalid endpoints or unknown structures are reported as valid facts.
- **SC-003 — Accountability**: **100%** of fixture facts, exclusions, and logical observations resolve to sources/rules. Raw, distinct, included, excluded, unresolved, and truncated counts reconcile under their declared categories; unsupported derivations remain explicit.
- **SC-004 — Deployment portability**: Consistent identifier renaming, record reordering, source repartitioning, and calendar shifts preserve expected semantic results after inverse mapping. No output contains an unobserved development identity; physical provenance reflects transformed files rather than falsely remaining identical.
- **SC-005 — Reproducible reuse**: Cold, warm, and independent scan paths agree on the acceptance corpus. Warm queries perform **no full-source record parse per query**; validation work is measured separately. Changed/interrupted prepared inputs are rejected or explicitly recovered in every authored case.
- **SC-006 — Operational fit**: A clean mounted-bundle rehearsal reports cold and warm costs within the runner's **2-CPU, 8-GB** envelope and a predeclared extraction budget, without developer artifacts or model calls. Planning MUST allocate that budget within existing case/run limits before testing and reserve downstream completion capacity. Report whether the measured result fits; claim no unmeasured speedup or judging compliance.
- **SC-007 — Isolation/compatibility**: All seven task projections, repeated windows, and multi-failure fixtures preserve scope/case associations. Trapped answer paths and network calls are never invoked. Missing evidence arrives as uncertainty; downstream count/order/name tests remain with their owning feature.

The [acceptance matrix](acceptance.md) maps every requirement to verification evidence. These are acceptance obligations, not completed production-feature results.

## Assumptions

- [ADR 0009](../../docs/adr/0009-track1-trace-extraction.md) specializes [feature 003](../003-contextual-telemetry-evidence/spec.md)'s retrieval boundary; its baseline estimator and resource-linking work remain separate. [Feature 004](../004-prompt-anomaly-integration/spec.md) can consume this evidence; [feature 002](../002-final-demo-runner/spec.md) owns CLI, resource envelope, final answers, evaluation, and release.
- Track-1's layout/fields are the compatibility target. The development bundle has two days and 70 prompts representing 57 windows; other deployments are discovered, not required to reproduce those values. Unsupported schema changes require explicit adapter revision.
- Official sources are pinned in [source-notes.md](source-notes.md). Sample field cardinalities and “filter the window first” advice do not override observed CSV ordering, trace-ID recovery, or raw-value preservation. Timestamp units are documented; duration interpretation is independently qualified.
- The first consumer remains frontend-root structure/duration, but extraction retains arbitrary selected recorded traces. Service-span baselines, metric/log ingestion, generic exporter adapters, live collection, anomaly thresholds, root-cause classification, and new comparison defaults are outside this feature.
- The research implementation is a reuse candidate. Coupled quality handling, fixed dates/paths, cache publication, portability, resource budgets, and integration require new acceptance evidence; experimental results do not prove production compliance.
- This request produces an ADR and specification only. Planning, tasks, implementation, new benchmarks, paid runs, commits, and deployment remain subsequent work. It follows the constitution's specification-first sequence without claiming downstream completion.
