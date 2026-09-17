# Planned descriptive evidence model

**Status**: Design v1; no implementation. [Contract](contracts/semantic-evidence.md) and [ADR 0002](../../docs/adr/0002-descriptive-semantic-compression.md) govern meanings. The [previous ranking model](deferred-data-model.md) is historical.

| Entity | Required content | Invariants |
| --- | --- | --- |
| CodingPolicy | schema/codebook/extraction versions; definitions; source mappings; compatibility | Meanings fixed before validation; unknown operations stay distinguishable; changes require migration or refused comparison. |
| FidelityPolicy | retained facts/questions; omitted fields; quantization/aggregation; decoding dependencies | Loss stated explicitly; raw fallback does not make packet lossless. |
| EquivalencePolicy | compared structure/attributes; permitted nuisance transformations; entity/context rules | Structural equivalence does not imply equal outcomes, equivalent context, or equal measured attributes. |
| EvidencePacket | ID; source fingerprints; policies; scope; dictionaries; observations; quality; provenance references | No gold, diagnostic answer, or reference-relative judgment in descriptive facts. |
| ExecutionScope | trace/episode IDs; deployment; absolute time anchor; interval; context fields with availability | Trace, episode, incident, and investigation window remain distinct; episode may span traces. |
| OperationDefinition | stable ID; observation meaning; mappings with evidence; retained raw distinctions | Operation observed does not imply business success; raw-name aliasing must be justified. |
| EntityBinding | alias; original ID/namespace; service/replica/node/role mappings and evidence | Alias substitution preserves equality/distinctness; unresolved identity remains unresolved. |
| SpanObservation | scoped span ID; trace; recording entity; operation; raw type/status; start/duration; provenance | No inferred DB target or RPC role masquerades as recorded identity; zero durations and blank types retained. |
| ObservationRelation | endpoints; observed/inferred kind; parent resolution; temporal support/precision | Parent link is not automatically network edge or causal edge; no invented sibling order. |
| Measurement | raw value; units; converted value if justified; precision; clock uncertainty; conversion evidence | Unknown units prevent unsupported end-time/order claims. |
| StructuralPattern | ID/version; operations; graph; role variables; matching rule | Observed structure, not a healthy/fault/behavior label. |
| PatternOccurrence | pattern; observation membership; entity bindings; measurements; external links; provenance | Expansion recovers contracted facts; repeated membership is explicit, not duplicate evidence. |
| RepeatGroup | operation/pattern; members; exact count; participants; temporal/interleaving relations | Serial, parallel, and retry interpretations remain distinguishable where evidence permits; repetition alone is not retry evidence. |
| ProvenanceRecord | source fingerprint; record key/locator; raw IDs/values; extraction rule/version | Every assertion auditable; aggregate links identify members; immutable source mapping. |
| ObservationQuality | retrieval coverage; boundaries; completion; sampling; missing parents; duplicates/conflicts; instrumentation limits | Retrieval completion and instrumentation completeness are different claims. |
| SuccessVerification | criterion/version; outcome; execution/workload scope; verifier/source; evidence | Independent of generated symbols and comparative normality; unknown is allowed. |
| ReferenceCohort | members; selection/version; context; allowed variants; distributions; sample sizes; eligibility | Typical is not synonymous with successful; no selection using evaluation gold. |
| ComparisonFinding | kind; observed values/IDs; reference; rule/version; context; uncertainty; evidence | Derived, recomputable without changing descriptions; anomaly does not establish cause. |
| BehaviorInterpretation | operational definition/version; episode interval; support/conflicts; mechanism hypothesis separately | Temporally extended behavior and sustaining mechanism are distinct; finite cycling does not prove nonconvergence. |
| Investigation | request/task ID; deployment/window/timezone; supplied failure count; requested projection | Scope only; no scoring points. |
| IncidentHypothesis | hypothesis/incident IDs; onset estimate/interval; exact component; reason; confidence; evidence/alternatives | Internal unrequested fields may be unknown; field association survives projection; evidence can be shared. |
| AssertionResult | assertion ID; fixture/reference provenance; frozen policy; answers; mismatches; size; status; limitations | not_tested / supported_within_scope / falsified / inconclusive; no aggregate success hides a failed claim. |

Descriptions are immutable with respect to downstream policy changes. New extraction/codebook versions produce new packet versions; new cohort or threshold versions produce new comparison findings. A new hypothesis may cite existing observations without rewriting them.

The evidence sidecar is separately measured supporting storage. The model-visible packet includes enough provenance keys and quality information to make claims inspectable, even when full raw values require retrieval. The first experiment expands retained structural facts from the packet and its declared dictionary only.
