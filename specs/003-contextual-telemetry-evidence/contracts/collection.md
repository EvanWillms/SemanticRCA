# Telemetry collection and retrieval contract

**Version**: design v1, 2026-09-17. **Authority**: [ADR 0003](../../../docs/adr/0003-indexed-telemetry-retrieval.md), [spec](../spec.md).

## Inputs and outputs

Inputs are a source snapshot, deployment-scoped investigation window, and declared retrieval/reference policies. Runtime paths are supplied by the caller; developer-local paths are not required. Outputs contain observations, reproducible selection criteria, source locators, coverage, and unresolved/conflicting records.

Selection identifies executions from request-entry observations in half-open time intervals. The entry-point rule may be based on validated operation/role metadata; it must not hard-code the expected fault component. Missing roots or unknown entry-point semantics are explicit limitations, not evidence that no activity occurred.

Expansion resolves selected execution IDs across the available source inventory independently of the selection time range. It retrieves spans that start outside the original window or in an adjacent available partition. A partition absent from the bundle remains unavailable. The system must not infer its content or obtain a hidden answer-containing dataset.

## Required guarantees

- Parse source records with format-aware readers; never use line counts as logical CSV record counts. Do not stop scanning unsorted input at an out-of-window timestamp.
- Scope trace IDs to deployment and span IDs to trace. Preserve original identifiers as strings and retain conflicts instead of overwriting them.
- Store enough source identity and logical record location to recover each observation. Preserve raw values and separately identify supported conversions; timestamps in different units must not be joined without normalization.
- A time margin may reduce follow-up retrieval, but does not establish complete traces. Report completeness relative to the sources actually searched and separately report unresolved ancestry/instrumentation uncertainty.
- Reference membership declares whether it uses request start or requires a completed execution before the cutoff. A request starting before the cutoff but ending after it cannot enter a strict pre-cutoff duration baseline. If end time cannot be established, qualify or exclude it under the stated policy. Static-file timestamps do not establish online arrival time.
- Source inventory/fingerprints, extraction version, and build completion govern prepared-view reuse. Queries must not mistake an interrupted build or stale data for a complete snapshot. A valid old view may remain available under its own identity while a new one is built.
- Missing partitions, unreadable rows, sample limits, or exhausted budgets appear in coverage with counts and reasons. A bounded response provides continuation or explicit truncation, not a silently complete-looking result.
- A scan reference remains available for correctness comparison. Prepared views are derived, rebuildable artifacts; source telemetry is not modified.

## Index choice and operational boundary

ADR 0003 chooses reuse of the existing SQLite approach for repeated queries by time, trace identity, and component/time. These are access paths, not cohort, normality, or causality rules. Source coverage can grow by modality/partition as needed; trace work need not await full log ingestion.

Measure construction, warm-query time, storage, peak memory, and the number of full-source parses separately. Record failure/recovery behavior and source compatibility. No fixed speedup is required or claimed before measurement. When integrated with the runner, generated artifacts reside under its permitted output location and preparation is charged to its runtime/resource budget.
