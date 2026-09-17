---
status: accepted
date: 2026-09-17
---

# Separate investigation decisions from bounded telemetry operations

OpenRCA's controller/executor split provides a useful investigation scaffold: choose one operation, inspect its observation, and decide what to investigate next. Its generated Python runs in a persistent IPython shell, while dataset knowledge and diagnostic rules live largely in prompts. SymbolicRCA needs independently verifiable retrieval, portable resource identities, predictable budgets, and source-linked evidence.

## Decision and trade-offs

- Retain the existing runner, `solve()` seam, output checkpointing, and submission contract. Adapt the investigation pattern rather than copying OpenRCA's runner or unrestricted executor.
- Interpret the instruction before accessing telemetry. Use the seven task projections as a compatibility reference; the actual instruction remains authoritative for scope, with metadata used only for consistency checks.
- Expose declared, typed operations for inventory, scoped retrieval, qualified comparison, supported relationship expansion, and targeted log inspection. Each operation receives explicit scope, policy identity and remaining limits; it returns structured observations, provenance, coverage, qualifications and a stop reason.
- Discover available resource identities and KPIs from the mounted bundle. Convert the Market schema guide into validated adapter rules, retaining raw values, source fields, timestamp units and UTC+8 interpretation. Do not transplant component lists, absolute paths, fixed replica counts or undocumented duration-unit assumptions.
- Record operation requests and outcomes, including failures and empty results. An empty result must distinguish a valid empty selection from an invalid field/resource, missing source or exhausted budget.
- Use deterministic orchestration for feature 004. Later model-directed decisions may select only declared operations, with bounded repair/retry and finalization reserves. Keep retrieval/comparison policies fixed within an investigation; changed investigation focus does not authorize changing thresholds to obtain a desired answer.
- Metric and trace discovery are independently available. Logs answer a bounded question. A normal service aggregate or absent frontend anomaly must not prevent resource investigation.

This costs adapter and contract work and limits improvised analysis. In return, retrieval can be verified without a model, repeated observations need not consume model context, and operation results can feed different diagnosis policies without changing their provenance.

## Alternatives not selected

Copying the IPython executor would leave scope and resource limits dependent on generated code. Copying only the prompts would leave schema validation and access control implicit. A mandatory metrics-first filter would hide trace-only or masked replica effects. Building a general-purpose agent/tool platform exceeds the Track 1 scope.

## Consequences and verification

[Feature 004](../../specs/004-prompt-anomaly-integration/spec.md) owns deterministic discovery and the operation record. [Feature 007](../../specs/007-evidence-backed-diagnosis/spec.md) consumes these operations for diagnosis. [ADRs 0003](0003-indexed-telemetry-retrieval.md), [0004](0004-qualified-contextual-baselines.md) and [0005](0005-evidence-backed-resource-relationships.md) continue to govern the underlying evidence.

Acceptance must cover renamed deployments, mixed units, invalid operation arguments, empty results, deadline exhaustion, unchanged-source replay and source-pointer resolution. This decision does not assert that these operations exist yet. OpenRCA source provenance is recorded in the [adoption notes](../openrca-adoption.md).
