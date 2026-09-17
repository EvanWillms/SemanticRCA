# Resource relationship and expansion contract

**Version**: design v1, 2026-09-17. **Authority**: [ADR 0005](../../../docs/adr/0005-evidence-backed-resource-relationships.md), [spec](../spec.md).

## Identity and relationship kinds

Entities retain deployment namespace, original identity, kind, supported aliases, and mapping evidence. Recording component, logical service, replica, host, and endpoint are distinct. Names are parsed under source-specific rules; replicas or services that contain similar digits are not automatically aliases.

| Kind | Required evidence | Unsupported promotion |
|---|---|---|
| Recorded span ancestry | Matching parent/span IDs within the same deployment and trace; conflict checks | Every parent edge is a network call or a causal fault edge |
| Service dependency | Source/destination traffic identities or validated endpoint/service evidence | One service-level observation identifies the receiver of a particular request |
| Resource placement | Explicit container/host identity or independently supported placement mapping | Placement holds forever or a host condition affected every colocated request |
| Endpoint association | Endpoint and entity evidence with observed time support | An IP address is a permanent resource identity |
| Temporal association | Related observations with normalized clocks and stated time resolution | Coincidence establishes a request join or causal direction |

A relationship record includes source, target or unresolved target, kind, scope (request/service/resource/temporal), observed times or supported interval, evidence locators, derivation version, qualifications, alternatives, and any unresolved mapping fields. Repeated point observations do not automatically establish continuous validity between them.

## External-call handling

First retrieve the available recorded trace and qualify missing ancestry/receivers. An observed client operation can remain valid evidence even when its target is unresolved. The absence of a receiver does not distinguish uninstrumented work, partial retrieval, trace propagation loss, or a failed call without further evidence.

A trace `HGET` span recorded by cartservice may justify investigating a database operation. Mesh cartservice→Redis evidence can justify expansion to Redis service/pod telemetry; container identity can justify inspecting its observed host. This combined chain remains contextual unless validated request-level evidence identifies the exact target. Preserve multiple possible replicas rather than choosing one because it has the largest anomaly.

Proxy/service log payloads may contain request IDs or endpoints. Verify their semantics and mapping before equating them to trace IDs. Persistent connections may carry many operations. Resource metrics and timestamps alone do not supply a per-operation foreign key.

## Expansion result

Accept seed entities/observations, allowed relationship kinds, a temporal policy, and budgets for depth, entity count, records, and time. Return visited entities, the relationship evidence justifying each expansion, retrieved telemetry, unresolved targets, candidate alternatives, and an unvisited frontier with stop reasons. Deduplicate shared evidence by provenance; do not infer independent corroboration from different presentations of the same source.

All source and mapping qualifications propagate to downstream evidence. Exact span ancestry and inferred resource associations remain distinguishable in the explanation even if displayed in one graph.
