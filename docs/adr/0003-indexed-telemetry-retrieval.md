---
status: accepted
date: 2026-09-17
---

# Separate indexed telemetry retrieval from evidence selection

Repeated investigations require time-range lookup, complete recorded-trace retrieval, and component-level telemetry across unsorted files. Reuse the repository's SQLite indexing approach as a rebuildable, provenance-preserving access layer; reference selection and diagnosis operate above it and never determine which raw records are considered to exist.

## Decision and trade-offs

- Select candidate requests by the prompt's deployment/window and an explicit reference policy, without knowing the fault component or onset. Retrieve their recorded spans by deployment and trace ID across the indexed source inventory, including spans outside the selection interval and in adjacent available partitions.
- Preserve raw identifiers, values, source fingerprints and record locators. Declare units, conversion rules, source coverage, duplicate/conflicting records, and unresolved ancestry. Retrieval completeness concerns the indexed records, not instrumentation completeness.
- Reuse [the existing builder](../../experiments/frontend_blind_v1/build_index.py) rather than introduce another database system. Treat its current behavior as an implementation starting point, not proof that this ADR's contracts are satisfied.
- Scope construction to the sources needed by the investigation; adding logs or another partition extends a declared coverage manifest. Reuse requires compatible source and extraction identities and a completed build. An interrupted or stale build cannot silently serve as a complete index.
- Retain streaming scans as the correctness reference and a permitted one-off fallback. Measure initial construction, storage, memory, and amortized repeated-query cost. Building every modality up front is not a prerequisite for trace analysis; startup work remains subject to the runner's resource and time limits.

Full scans are simple and worked for the exploratory case. They repeatedly parse gigabytes for adaptive queries. Time-only partitioning helps find candidates but can truncate their traces. The chosen approach pays an initial construction/storage cost to support both time selection and trace-ID expansion, with an independently testable retrieval contract.

## Resulting specification

See [feature 003](../../specs/003-contextual-telemetry-evidence/spec.md), its [collection contract](../../specs/003-contextual-telemetry-evidence/contracts/collection.md), and acceptance cases R1–R5. [ADR 0002](0002-descriptive-semantic-compression.md) continues to govern observation meaning. No new index build or performance result is implied by this decision.

[ADR 0009](0009-track1-trace-extraction.md) specializes this access-layer contract for Track-1 trace extraction following the short-window experiment, including deployment discovery, independent quality dimensions, and explicit adoption checks. Its [feature specification](../../specs/005-track1-trace-extraction/spec.md) leaves baseline selection and diagnosis above extraction.
