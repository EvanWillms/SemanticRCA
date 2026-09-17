# Planned model: contextual telemetry evidence

**Status**: logical design; not an implemented schema. Governed by [the specification](spec.md) and ADRs 0003–0005.

| Entity | Required content | Invariant |
|---|---|---|
| InvestigationScope | Dataset/deployment identity; query interval and timezone; requested fields; supplied count | Scope contains no expected diagnosis. |
| SourceSnapshot | Source locators/fingerprints; date/modality inventory; schema/extraction versions; build completion | Changed inputs cannot silently reuse earlier derived results. |
| RetrievalPolicy | Entry-point/operation selection; reference/query intervals; cross-partition policy; budgets; availability mode | Membership is distinct from subsequent trace expansion. |
| ExecutionIdentity | Deployment namespace and trace ID; span ID within execution | Same-looking IDs in other executions/deployments do not collide. |
| RetrievalResult | Observations; locators; source snapshot; selection/expansion provenance; coverage | No silent truncation or implied completeness beyond sources searched. |
| CoverageStatement | Requested/searched partitions and intervals; absent/unreadable sources; conflicts; missing parents; sampling/instrumentation unknowns | All available recorded links resolving is not proof of complete instrumentation. |
| Observation | Existing descriptive evidence identity; raw and interpreted measurements; recording entity; time precision; source | Reuses the descriptive evidence model; comparison never changes its meaning. |
| ReferencePolicy | Comparison question; context keys; source views; lookback/fallback limits; cutoff mode; support/estimator rules | Does not condition away the feature under investigation or consume answer labels. |
| ReferenceCohort | Snapshot of members or reproducible membership; context; time span; counts/exposure; qualifications | Typical, peer, and independently verified-success memberships remain distinguishable. |
| Baseline | Cohort/version; supported numerical distributions or structural variants; estimator and variation policy; eligibility | No zero-denominator score or health claim is implied. |
| ComparisonFinding | Observation/reference IDs; kind; differences; direction; magnitude; persistence; uncertainty; rule version | Unavailable or qualified comparisons cannot masquerade as unqualified results. |
| PriorityPolicy | Within-family ranking; review allocation; magnitude/scope/quality treatment; deduplication rule; version | An uncalibrated score is not a probability or universal cross-family scale. |
| ResourceEntity | Deployment and original ID; kind; supported aliases; observation-time support; mapping provenance | Logical service, replica, host, endpoint, and recording entity remain distinct. |
| ResourceRelationship | Source/target or unresolved target; kind; scope; evidence locators; observed times; rule/version; ambiguity/qualifications | No transitive promotion from contextual association to exact request identity. |
| ExpansionResult | Seed entities/relationships; visited frontier; retrieved evidence; limits and truncation | Unvisited resources remain unassessed, not ruled out. |

## Lifecycle

A prepared source view is building, complete for its declared coverage, or unusable/incompatible. New sources or extraction rules create a new view identity. A partially covered source inventory can be queryable only with explicit qualifications.

A baseline is a frozen derived object for an investigation. New membership or comparison semantics creates a new version. Old observations and findings remain reproducible. Eligibility is assessed for the particular comparison question and can be eligible, qualified, or unavailable.

Resource relationships state observation times or supported intervals rather than inventing permanent validity. Point observations do not certify the interval between them. Conflicting aliases and unresolved endpoints remain alternatives until evidence supports resolution.
