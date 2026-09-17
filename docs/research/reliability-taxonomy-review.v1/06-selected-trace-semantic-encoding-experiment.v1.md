# Selected-trace semantic encoding: review and experiment

Date: 2026-09-17. Status: proposed experiment; four existing traces checked read-only in the local index. No encoder or LLM evaluation was run in this review.

## Decision

Test a **deterministic evidence packet with a separately scored LLM annotation layer**. Begin with the already specified three synthetic structural fixtures; then use four materialized traces and controlled counterexamples to test feature preservation, error interpretation, and unsupported labeling. Do not start by asking an LLM to assign a reliability-behavior class to every trace.

“Deterministic versus LLM” and “descriptive versus interpretive” are different axes. Imperative code can produce descriptive symbols or unsupported diagnostic labels. An LLM can describe observations or infer a mechanism. The experiment must identify both **the producer of a claim** and **the evidence required by its meaning**.

Here, semantic encoding means a versioned, inspectable structured representation with a decoder and evidence links. Vector embeddings are outside this experiment: they would require a separate retrieval/similarity objective and evaluation.

## Re-grounding against the official data guide

The controlling dataset description for this revision is [Track 1 data.md](/Users/nonadmin/Development/mantisgrid-hackathon/hackathon-2026-official/track-1/docs/data.md), read on 2026-09-17 (SHA-256 `c3813bb8447c28af56940027da3521c54d8b1b9fed6882f3235c01c998c24bda`). This is local-source review, not a new telemetry scan. The guide contains an illustrative case answer, so this review has additional documented development-answer exposure. No `query_dev.csv` or upstream evaluation dataset was opened.

| Official statement | Consequence for the experiment | Remaining boundary |
| --- | --- | --- |
| Metrics/log timestamps use seconds; trace timestamps use milliseconds; answer times use UTC+8 | Normalize timestamps deterministically, preserve raw units, use UTC+8 for query/answer calendar parsing, and test cross-channel conversion. Unix epoch values remain absolute instants; do not add eight hours to them. | The guide says traces are in milliseconds but does not separately define `duration`. It does not establish the microsecond duration interpretation used by current code. Record that discrepancy/ambiguity explicitly; do not apply the timestamp rule to duration automatically. |
| Network faults can be poorly reflected in metrics; parent–child span latency is useful | Make parent–child start offsets a required trace feature, alongside root duration, operation counts and interval accounting. Include same-emitter versus cross-emitter qualification and preserve direction/sign. | A timestamp offset is not pure network transit time. Clock differences, application scheduling and instrumentation boundaries remain alternatives. The guide motivates a feature, not an exact reason classifier. |
| Topology is encoded in names; container IDs bind pods to nodes and mesh IDs contain source/destination information | Parse documented container and mesh naming structures in code, preserving raw names and mapping provenance. Treat this as available dataset context, not something the LLM must guess. | A trace recording component alone does not identify every called resource. Name-derived service/placement relationships do not prove which backend served an individual span; mappings need observed time support. |
| Faults are operator-injected and labeled; there are 15 named reasons | Distinguish an observed status/error indicator, a measured symptom, a hypothesized mechanism, and an organizer fault-reason label. Preserve the official reason strings for a later diagnostic adapter. | The 15 reasons are a diagnosis vocabulary, not a span-error codebook. Latency does not uniquely identify packet loss, corruption, retransmission or injected latency. |
| All 70 supplied cases are development data; evaluation uses 20 cases from another deployment with different components | Use this selected-trace study as development engineering. Add identity-renaming checks and avoid component allowlists in reusable encoding rules. A later generalization claim needs deployment-separated evidence. | Keeping gold out of encoding inputs isolates this experiment; it is an experimental design choice, not a competition ban on using development labels. Existing exposure prevents calling these controls held out. |
| Each query supplies a 30-minute window and failure count; some windows have multiple independent failures | Keep query scope separate from trace facts. A later diagnostic adapter preserves each incident tuple and emits chronological order. | Do not force trace labels into the supplied number of failures or equate trace start with fault onset. Sampled telemetry may only bound onset. |
| Files are large and CSV fields may be quoted; filter to the window | Use CSV-aware bounded indexed retrieval, then complete the selected trace's recorded membership by exact ID. | The local audit shows unsorted rows, so window filtering cannot mean stopping a source scan at the first out-of-window row. Record any retrieval beyond the window. |
| Trace type/status fields are nonuniform, including db status `Ok` | Preserve strings and context; do not use nonzero-is-error rules. | The guide supplies examples, not a producer-specific success/error mapping. Its summary lists 27 operation names and four statuses; the local March 20 audit measured 29 and eight. Use source-versioned observed inventories rather than fixed category counts. |

This changes feature priority: **edge timing and dataset-supported identity relationships deserve explicit deterministic extraction**. It does not authorize causal labels from timing alone. No additional external research is needed to make these dataset-specific revisions.

## Materialized work and its implications

This review covers the supplied eight-file taxonomy package, the active representation and contextual-evidence contracts, trace audit and case-25 artifacts, and relevant experiment implementations and run summaries. It inventories broader research notes but does not revalidate every cited paper or rescan the multi-gigabyte telemetry corpus. The five numbered review chapters overlap the consolidated report and are not independent corroboration; the handoff is the research brief. Existing test counts below are recorded results, not tests rerun for this review. In the initial review no answer-key file was opened; the existing case-25 narrative and now the official guide expose development answers as recorded above.

| Material | What exists | Implication for this experiment |
| --- | --- | --- |
| [Taxonomy package](README.v1.md), especially [synthesis](04-candidate-synthesis.v1.md) and [falsifiers](05-research-gaps-and-falsifiers.v1.md) | Literature review and proposed recognition contracts; no evaluated recognizer | Adopt separate temporal-form, mechanism, participants, outcome, and evidence facets. Do not turn the proposed hierarchy into mandatory classes. |
| [ADR 0002](../../adr/0002-descriptive-semantic-compression.md), [semantic contract](../../../specs/001-candidate-recall-experiment/contracts/semantic-evidence.md), [plan](../../../specs/001-candidate-recall-experiment/plan.md) | Explicit encoder/decoder design and A1 three-fixture gate | The semantic serializer is still planned. Reuse its fidelity contract rather than claiming the existing summaries implement it. |
| [Trace audit](../track-1-trace-audit.md) and [audit scripts](../trace-audit/README.md) | Full March 20 lexical audit and a reconstructed 37-span trace | Mixed statuses, noncontiguous storage, unknown instrumentation coverage, and provisional duration units are mandatory qualifications. |
| [Case-25 trace analysis](../examples/track-1-case-25-trace-causality.md) and [selected rows](../examples/track-1-case-25-pyod-results/selected-traces.json) | Concrete duration contrast, parent links, repeated operations, and raw rows | Useful exposed controls. Latency accounting does not identify the underlying runtime or memory mechanism. |
| [Frontend trace evidence](../../../experiments/frontend_blind_v1/trace_evidence.py) | Span retention, graph flags, interval unions, ranked paths and component shortlists | Reuse arithmetic and retrieval ideas after qualification; a shortlist is not a semantic codebook. Names such as `linked_receivers` and `dependency_reachability` are stronger than an unvalidated parent relation warrants. |
| [Baseline observations](../../../experiments/short_window_baselining_v1/observations.py) and [contracts](../../../experiments/short_window_baselining_v1/contracts.py) | Root observations, quality flags, direct-child C0/C1/C2 signatures and numeric comparison | Reusable input infrastructure. C1 ignores multiplicity; C2 retains direct-child multiplicity but neither preserves the full descendant graph, timing, and identity relationships required here. |
| [Baseline selection](../../../data/experiments/short-window-baselining-v1/selection.json) and [run summary](../../../data/experiments/short-window-baselining-v1/run_summary.json) | Frozen five-minute C1 pooled policy; 18,160,322 indexed spans; 180,850 observations; selection records 34 passing package tests and 432 controlled cells | Materialized baselining has advanced beyond older “planning only” notes. This validates neither semantic encoding nor error classification. Retain qualifications and use a separate comparison layer. |
| [Frontend investigation execution](../experiments/frontend-blind-v1/EXECUTION.md) | Deterministic inputs and staged investigations; scope reduced to eight random prompts | Do not infer final benchmark accuracy from prepared evidence or partially completed case artifacts. |
| [Root README](../../../README.md) and [report](../../../REPORT.md) | Empty-output runtime harness | Experiment code is separate from the shipped diagnoser, which remains unimplemented in this milestone. |

There are two implementation hazards to avoid copying into a new encoder. `trace_evidence._span` unconditionally treats duration as microseconds, while the audited evidence and frozen baseline policy call that interpretation provisional. Also, duplicate identities are flagged but some graph helpers then select one row per span ID. An encoding contract must retain conflicts and mark unresolved relations rather than quietly choosing an authoritative edge. Graph resolution alone also cannot certify retrieval coverage or full instrumentation.

## Feature ownership and labeling taxonomy

Every claim has `semantic_layer`, `producer_kind`, `definition_version`, `evidence_ids`, `scope`, `limitations`, and `validation_state`. Producer values are `code`, `llm`, or `human`; being produced by a model is not an evidence grade. Preserve a separate support grade such as observed, derived, hypothesized, or intervention-supported.

| Semantic layer / feature | Deterministic responsibility | Permitted LLM responsibility | Required restraint |
| --- | --- | --- | --- |
| Source and quality | Parse raw strings; composite `(trace_id, span_id)` identities; source pointers; duplicates, roots, missing parents, cycles; declared retrieval bounds | Explain qualifications with evidence IDs | Resolved parents do not prove complete execution instrumentation. |
| Operation identity | Preserve exact names and types; apply only approved, versioned aliases; keep unknown names distinct | Propose operation meanings and alias candidates for later review | Do not silently strip `grpc.`, slashes, case, or component suffixes. A proposed mapping cannot change a scored packet. |
| Recorded structure | Parent-reference graph, depth where resolved, operation counts, participants, same/different-emitter relationships, repeated subgraphs | Describe supported motifs in plain language | Parentage is not automatically RPC, dependency, blocking, or cause. Repetition is not retry. |
| Measurements | Raw starts/durations, absolute anchor, precision; signed parent–child start offsets in milliseconds; conditional interval unions and gaps under an explicit duration-unit policy | Describe measurement relationships | Start offsets do not require duration units but are clock-qualified across emitters. Unknown duration units prevent authoritative end times; uncovered duration is not CPU self-time. |
| Dataset topology | Parse documented pod/node and mesh source/destination names when supplied, retaining exact raw identities, observation times and mapping provenance | Explain the supplied relationships | No guessed backend for an individual DB operation; do not merge distinct service names such as `adservice` and `adservice2`. |
| Status/error evidence | Preserve status, producer context and mapping state; apply a verified producer-specific status dictionary if available | Suggest an interpretation as a hypothesis; identify missing mapping evidence | Type `http` alone cannot select HTTP semantics. No universal nonzero-is-error rule. |
| Comparison | Frozen eligible reference and numeric/structural difference, when supplied | Summarize differences and qualifications | A larger duration is not an error or fault. C1 matching must not erase multiplicity change. |
| Temporal behavior | Evaluate explicit temporal predicates once their definitions and evidence requirements exist | Propose a multi-label temporal description, cite predicates, preserve alternatives | One trace ordinarily cannot establish population synchronization, controller oscillation, recovery cycles, or metastability. |
| Mechanism and diagnosis | Validate references/schema, not causal truth | Hypothesize mechanisms with missing and contradicting evidence | Cascade, retry amplification, memory pressure and common cause require additional evidence. Keep outside the initial encoder target. |

The initial vocabulary should be small: `operation_occurrence`, `parent_reference`, `repeated_operation`, `same_recording_entity`, `distinct_recording_entity`, `raw_status_observed`, `unresolved_parent`, `conflicting_identity`, `parent_child_start_offset`, and qualified timing facts. Name-derived relationships remain a separate context sidecar when supplied. These are proposed engineering symbols, not a new reliability taxonomy.

## Error extraction contract

Separate **telemetry error evidence** from **encoder mistakes**. A malformed record, ambiguous parent, or wrong unit conversion is an extraction-quality finding; it does not establish that the service failed.

For each span emit:

```text
raw_status: original string
status_context: recording entity + raw operation + raw type + known producer/version
status_interpretation: reported_error | reported_non_error | unknown | conflicting
mapping_id: versioned rule, or null
mapping_evidence_ids: sources establishing this producer's semantics
business_outcome: unknown unless independently verified
source_evidence_ids: original record locations
```

A status dictionary entry must specify its applicability, exact matching predicate, interpretation and supporting producer documentation/code. Generic protocol knowledge can suggest a rule but cannot establish that this export uses it. For the real pilot, leave interpretation unknown wherever that mapping is unavailable, including familiar-looking values. Distinguish explicit unknown from missing output.

If mappings are available, report error counts alongside mapped and unmapped denominators. An error fraction over mapped spans must state that population and mapping coverage; do not count unknown spans as successes. Do not add together caller and receiver error reports as independent failed requests. Request-level failure needs its own boundary and aggregation definition.

This nine-column trace export has no error message, exception stack, retry-attempt marker, request payload, or business-success verifier. Log-based exception extraction is a later linked-evidence experiment. An LLM must not manufacture those fields from operation names.

## Selected real traces

Read-only queries against `data/experiments/short-window-baselining-v1/trace.sqlite3` on this review verified the following counts. These are indexed records, not a fresh raw-source checksum audit.

| ID | Trace ID | Recorded spans / entities | Root raw duration | Purpose |
| --- | --- | --- | --- | --- |
| R0 | `9451fd8fdf746a80687451dae4c4e984` | 37 / 13 | 93829 | Previously audited mixed-type, repeated-operation trace. |
| R1 | `958208cb1d31eae52efe9ce0770b19f6` | 37 / 12 | 91029 | Earlier case-25 comparison trace. |
| R2 | `328e653dddef2f29d419a46895d85d12` | 37 / 13 | 428249 | Larger-duration case-25 trace with similar operation structure. |
| R3 | `33ac121d12f9d81f70a93424c7312544` | 1 / 1 | 929 | Root-only recorded trace; test empty recorded children versus unknown instrumentation. |

Each has one blank-parent root and no unresolved parent references in the retrieved rows. R0–R2 each have 33 `0`, two `200`, and two `Ok` statuses; R3 has one `0`. The repeated status histogram cannot distinguish their timing differences or certify successful outcomes. R1 and R2 have different participant counts: compare their actual bindings rather than asserting full structural/identity equivalence.

The selected-traces JSON materializes R2 and R3; R0 and R1 can be retrieved by exact trace ID from the existing index. Freeze source-file fingerprints, every selected source record, raw values, and extracted-file hashes in the run manifest. No full-day rescan is needed for selection; source verification is a separate recorded step. All four are exposed engineering controls, with selection bias. No prevalence, held-out accuracy, or generalization estimate follows from this pilot.

## Experiment SE-1: preserve facts, then test descriptive labeling

**Question:** Can the symbolic packet preserve independently specified features and error uncertainty, and can an LLM describe them without promoting observations into unsupported failure or mechanism labels?

### Stage 0 — freeze and pass the existing structural gate

Use A1's authored seven-span T0, renamed/reordered T1, and T2 with one added catalog operation, exactly as the [active plan](../../../specs/001-candidate-recall-experiment/plan.md) specifies. Freeze fact sheets, codebook, equivalence rules, and hashes before implementing the encoder. All contracted facts must expand exactly without reading raw telemetry. This remains the first implementation step; later stages below are an explicitly proposed extension, not a claim that A1 is already passed.

### Stage 1 — selected traces and controlled contrasts

Use R0–R3 unchanged plus the following ten authored variants. Keep synthetic variants visibly separate from real telemetry and preserve a transformation manifest. Two independent annotators prepare/review expected facts from source rows before seeing encoder outputs; unresolved disagreements remain unknown and are reported separately.

| Variant | Intervention | Expected preserved distinction |
| --- | --- | --- |
| V1 | Bijectively rename trace/span IDs and shuffle R0 rows | Equivalent semantic graph; provenance/aliases may differ. |
| V2 | Add one distinct catalog operation under an existing parent | Exactly one additional occurrence and edge; no retry conclusion. |
| V3 | Rebind one repeated occurrence to a new recording entity | Entity equality/distinctness changes even when operation counts do not. |
| V4 | Remove a referenced parent and declare retrieval incomplete | Unresolved ancestry and collection qualification; not a new root or failed call. |
| V5 | Add a duplicate identity with conflicting parent/status | Both source records retained; no arbitrary winner. |
| V6 | Change one status to `14` without establishing producer mapping | Raw-status contrast; error interpretation stays unknown. |
| V7 | Supply an authored producer contract defining that same status as reported error | Correct mapped-error extraction under that synthetic contract; business outcome still unknown. |
| V8 | Remove duration-unit support while preserving raw numbers | Raw durations survive; authoritative derived endpoints/order become unavailable. |
| V9 | Extend V7 with an independently authored verifier of successful enclosing-request outcome | Child reported error and verified request success coexist at different boundaries; neither overwrites the other. |
| V10 | Shift a linked child start by a declared amount, leaving its raw duration, status, identity and parent fixed | Signed edge-start offset changes exactly; no automatic network-fault label. Retain any resulting interval inconsistency rather than repairing timestamps. |

V6/V7 form the positive/negative status-mapping control. V7 and V9 supply synthetic truth, not evidence about the benchmark producer or real business outcomes. Provide the synthetic verifier equally to every V9 arm. The real selected set contains no independently verified positive error cases, so real-data error precision/recall is **not estimable** here. A later error-enriched sample must first verify producer semantics, then sample positive, negative, and unknown cases using a frozen rule and retrieve full recorded traces.

Before model calls, add code-only contract checks for seconds-to-milliseconds conversion, UTC+8 calendar round trips, documented container/mesh name parsing, and consistent renaming of previously unseen components. These context checks use authored records, not a claim that metrics/logs have already been joined to the four traces. The required identity and timestamp facts must be exact; parsing failure stays explicit. They do not add LLM cases.

### Stage 2 — separate producer and representation effects

Prepare the same required facts in three forms: original selected rows with a qualification envelope, compact normalized graph JSON, and symbolic packet with all required dictionaries. No condition receives the case narrative, case-specific fault reason, benchmark onset, or gold answers. Dataset schema and naming rules are supplied equally across arms. The official 15-reason vocabulary is permitted development knowledge but unnecessary for this descriptive task; if supplied in a later diagnostic arm, provide it equally to every comparator. Preserve necessary identities for factual questions; retain the exposure limitation even if identifiers are masked.

1. **Code-only reference:** deterministic extraction and symbolic expansion, scored against independent facts. This answers whether the encoding works.
2. **LLM on normalized facts versus LLM on symbolic facts:** identical questions, model/settings and information; only representation changes. This isolates the packet's usefulness.
3. **LLM on raw rows:** same questions and qualification envelope. Compare with the other forms to measure extraction burden separately.

The model's task is to return structured descriptive claims, evidence IDs, explicit unknowns, and unsupported interpretations it cannot establish. It cannot retrieve more data, change the codebook, repair source facts, or use another arm's answer. Deterministic schema/citation validation checks formatting and pointer resolution; it does not by itself verify semantic entailment.

Freeze the exact available model identifier, prompt, settings, output budget and tokenizer in the run manifest before calls. Use three repetitions and counterbalance format order. The 14 real/variant cases × three representations × three repetitions require 126 bounded calls. This is a pilot count, not a statistical power calculation. A1 remains code-only. If no model is configured, complete the deterministic stage and report the LLM stage as not run.

Ask fixed questions: What operations and multiplicities are recorded? Which parent links resolve? Which occurrences share an entity? What are the signed parent–child start offsets and their clock qualifications? What timing facts are supported and under which unit assumption? Which statuses are observed and which have verified mappings? What is unknown about errors, success, targets, retries and coverage? For R1/R2, compare timing and participant differences using the same supplied pair in every arm.

## Scoring and stopping rules

- **Deterministic fidelity gate:** 100% exact recovery of contracted operation identities, parent references, counts, participant equality/distinctness, raw values, signed edge-start offsets, qualifications and evidence references. Any lost conflict, invented unit, status mapping, success, target or retry fails the relevant gate. Approximate timing uses an explicit predeclared precision policy, never a post-hoc tolerance.
- **Feature identification:** precision/recall by feature family, exact count/edge accuracy, and each missed contrast. Report trace-level macro averages so long traces do not dominate.
- **Error extraction:** raw-status preservation; mapped-label accuracy on authored positive/negative controls; unknown retention; false definitive error and success labels. Report undefined metrics when a class has no positives.
- **LLM labeling:** supported-claim precision, required-fact recall, evidence entailment, inappropriate abstention, unsupported mechanism assertions, and run-to-run consistency. Human adjudication distinguishes ambiguous facts from model mistakes.
- **Compression:** bytes and actual model tokens including codebook, context, prompt and qualifications; cold cost and explicitly declared dictionary reuse. Keep provenance storage and retrieval cost separate. Compare against normalized JSON as well as raw rows. No fixed-budget truncation in the equal-fidelity test.
- **Decision:** accept the deterministic packet only if its exact gates pass. Treat the LLM layer as an optional descriptive aid only if it makes zero forbidden promotions in this pilot and preserves required categorical facts across repetitions. Claim representation benefit only if symbolic input reduces tokens relative to normalized input without a factual regression on the same cases; otherwise report no demonstrated benefit. Small pilot success does not estimate a population error rate.

Attribute failures to parsing, identity/graph resolution, operation mapping, status mapping, compression, model omission, or unsupported interpretation. Keep the first violated boundary and downstream effects; a good diagnosis cannot compensate for an incorrect packet.

## Deliverables and next action

A future run should produce `manifest.json`, `codebook.json`, `status-mappings.json`, raw selected fixtures, independent fact sheets, normalized graphs, symbolic packets, decoder comparisons, model outputs, a claim-level adjudication table, and a compact report. Expected-answer files stay outside encoder/model inputs. Version any revised rule and rerun the fixed contrasts without rewriting earlier results.

Implement and run A1 first. Then run the selected-trace fidelity and status controls before spending model calls. Leave baseline comparison, multi-request behavior recognition, multimodal exception extraction, and benchmark diagnosis as separately scoped studies. The immediate research contribution being tested is **auditable preservation of useful distinctions with explicit unknowns**, followed by a measurable descriptive-labeling benefit—not a new reliability taxonomy or a demonstrated causal reasoner.

Execution refinement: [Incremental experiments handoff](07-incremental-experiments-handoff.v1.md) splits this proposal into small hypothesis checks, beginning with S01 and deferring the full model matrix.
