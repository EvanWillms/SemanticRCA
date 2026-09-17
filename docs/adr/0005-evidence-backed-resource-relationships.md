---
status: accepted
date: 2026-09-17
---

# Represent external resource relationships with explicit evidence and scope

The trace export can record a client database operation without naming its target, while mesh metrics, proxy logs, and container identities supply related service, endpoint, and host evidence. Maintain typed, time-supported resource relationships alongside span ancestry; never promote a service-level or temporal association into an exact request edge without supporting identifiers.

## Decision and trade-offs

- Preserve recording entity, logical service, replica, host, and endpoint as distinct identities. Resolve aliases only through explicit mapping rules with source evidence and observed time support. Endpoint reuse or placement changes invalidate timeless identity assumptions.
- Keep recorded span ancestry, observed service dependency, resource placement, endpoint association, and temporal association distinguishable. A cross-component parent link alone does not prove a particular network mechanism or fault.
- A client span with no resolved receiver/target remains an observed operation with an unresolved target. Search the available full trace before assigning retrieval gaps to absent instrumentation or an external resource.
- Use mesh source/destination identities and log endpoint evidence to expand an investigation to related resources. Preserve service-level ambiguity and candidate targets. Shared timing, operation names, or similar-looking request IDs cannot establish an exact call join.
- Every derived relationship carries evidence locators, derivation version, temporal support, ambiguity, and qualification. Repeated observations of the same connection or derived signal do not become independent corroboration automatically.

Trace-only topology would omit useful resource and host context. Guessing targets from familiar operation names or collapsing everything into untyped edges would create false precision. The chosen model supports bounded expansion while retaining the difference between exact recorded ancestry and contextual resource evidence.

## Resulting specification

See [feature 003](../../specs/003-contextual-telemetry-evidence/spec.md), its [relationship contract](../../specs/003-contextual-telemetry-evidence/contracts/resource-relationships.md), and acceptance cases L1–L5. The [resource audit](../research/track-1-resource-relationships.md) supplies the cartservice→Redis→host example and its request-level linkage limits. A derived relationship lookup is planned; the source dataset does not provide a universal resource foreign key.
