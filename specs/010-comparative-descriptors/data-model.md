# Data model: Reference-relative comparative descriptors

[descriptors.md](contracts/descriptors.md) governs semantics. The [feature 009 model](../009-qualified-short-baselines/data-model.md) owns source, observation, policy, baseline and structural-population identities; consume those types rather than copying their definitions into a second source of truth.

## Entities

| Entity | Required fields and relationships | Validation |
| --- | --- | --- |
| ComparisonDefinition | definition_id/version, measurement family, arithmetic version, optional diagnostic flags, label definitions | Initial family is frontend root duration in ms plus recorded direct-child structure. No failure count, health threshold or causal taxonomy. |
| FieldResult | status, value, unit/definition where applicable, reason codes, evidence references | `available` requires a value of its declared kind: finite number, boolean or defined categorical label; `not_requested`, `undefined` and `unavailable` require null value. Reasons explain unsupported input or undefined arithmetic. Optional fields default to not_requested. |
| DurationComparison | observed field, reference median field, signed excess field, optional ratio/MAD-departure fields, ordering label, baseline_id | Supported compatible inputs permit arithmetic. Zero MAD/median only disable the defined fields. Unsupported audit summaries remain outside eligible reference fields. |
| PatternDifference | pattern_id, reference count/known denominator/frequency, member evidence, signed operation/type count deltas | Deltas compare against this exact named multiset. Additions/removals are positive/negative portions of the signed map. Zero deltas may be omitted from the map without dropping the pattern or match result. |
| StructuralComparison | query structure state, C0 population ID, known/unknown/excluded counts, pattern differences, matching-pattern count, absent-from-reference field | Unknown query structure makes differences/absence unavailable. Known empty is a valid map. Zero known denominator makes frequencies and finite-reference-absence unavailable. |
| ComparativeDescriptor | descriptor_id/schema version, occurrence_id, observation_id, baseline_set_id, definition_id, duration/structure subresults, qualifications, evidence refs, validation status | Exactly one envelope per resolved query assignment, including unavailable comparisons. Qualification coverage cannot be weaker than the consumed baseline/observation evidence. |
| DescriptorQualification | code, scope, supporting evidence or unverified-assumption designation | Preserve support/stability and unverified health, replica/workload equivalence, provisional units, source-relative coverage and retrospective availability. A display label cannot remove them. |
| EvidenceReference | source/derived kind, snapshot/artifact ID, actual record selector, entity ID, measurement/statistic selector, normalization/definition ID | Must resolve to the claimed value and entity. A pointer that exists but selects another measurement fails. |
| ValidationResult | status, descriptor/baseline IDs, checked source/evidence IDs, failure codes, work counters | Validation is not inferred from nonempty fields or matching hashes alone. No partially validated descriptor is presented as fully validated. |
| ReviewView | view_id/version, baseline_set_id, slice_index, ordered descriptor IDs, sort definition, total eligible count, full population reference | At most five available positive signed excesses; one source/unit/profile scope. Ties use deployment, trace and span strings. Qualifications remain accessible for each entry. |
| DescriptorCoverage | assignment/descriptor counts, unique observations, occurrence counts, field-state counts, structural known/unknown counts, cohort IDs, inspection status and withheld counts | Descriptor count equals resolved assignments processed; unavailable is a result. Missing unprocessed assignments remain explicit. Zero denominators yield unavailable ratios. |

## Field states

| Situation | Observed duration | Median / excess | Optional ratio | Optional MAD departure |
| --- | --- | --- | --- | --- |
| Compatible supported positive center/MAD | available | available | available if requested | available if requested |
| Supported constant positive center | available | available | available if requested | undefined if requested |
| Supported zero center/MAD | available | available | undefined if requested | undefined if requested |
| Unsupported reference | available when valid | unavailable | unavailable if requested | unavailable if requested |
| Invalid/incompatible observation | raw text retained; normalized value unavailable when invalid | unavailable | unavailable if requested | unavailable if requested |
| Optional diagnostic disabled | unchanged | unchanged | not_requested | not_requested |

A valid observed normalized duration may remain available when only cross-reference unit compatibility fails; the difference still becomes unavailable. Supported instability changes qualifications, not these arithmetic availability states. Ordering label is unavailable when excess is unavailable; it is not inferred from displayed rounded values.

## Evidence graph and validation

A descriptor links to its query assignment, raw observation measurement and the same baseline set. An assignment with a producer MissingContext outcome retains that typed outcome and frozen-set evidence, with affected numerical/structural fields unavailable; it does not invent a baseline object. A duration subresult with an available comparison links to the supported C1 baseline/statistics; a structural subresult links to the C0 population and every referenced pattern. Baseline statistics link to exact source members through the producer bundle. Derived references include calculation versions as well as values.

Validation traverses this graph within the declared source and artifact inventory. It verifies digests, scoped entities, original values, normalization, membership/statistics and derived arithmetic. Recompute distinct baseline statistics once in the validation session; this checks the producer result, not permission to reselect members or tune support. The initial CSV resolver honors logical-record numbering; a declared JSON-array representation uses an actual member selector, never an invented trace-ID key.

Bundle/schema/hash failure is an input-integrity failure. A localized missing or wrong measurement yields a recorded invalid-evidence outcome with unavailable affected comparison fields; independent valid raw/structural fields may remain. A validation report distinguishes failed source evidence from ordinary baseline support abstention.

## Identity and lifecycle

Descriptor identity hashes observation revision, baseline-set/baseline/population identities, occurrence, comparison definition, result fields and qualifications using the declared canonical serializer. Source hashes and versions make changed measurements distinct even if entity names remain equal. Absolute filesystem paths, timestamps of processing and measured cost do not determine content identity.

An observation can have multiple descriptor versions under different baselines. One observation can also have multiple occurrences across overlapping windows. Do not deduplicate away those contexts or count them as independent requests/incidents.

Lifecycle: validated inputs → constructed outcome → semantic validation → published complete or explicitly partial bundle. Integrity failures cannot become valid comparisons through ranking. New source, baseline or definition creates new records; old records remain immutable. Review views reference descriptors and never mutate their fields or qualification state.
