# Investigation loop ownership

Owner: [Sketch toy agentic completion loop](codex://threads/01a0b128-5479-7042-9de2-80514655a78a)

Task ID: `01a0b128-5479-7042-9de2-80514655a78a`.

## Owned paths

- `libraries/rca_domain/` — planned standalone library, its tests, examples and packaging.
- `specs/011-completion-aware-investigation/`.
- `docs/adr/0016-completion-aware-investigation.md`.
- `docs/research/minimal-agent-loop.v1.md` and `minimal-agent-loop-sources.v1.md`.
- `coordination/investigation-loop/`.

## Public interface

Proposed: `from_semantic_traces(envelopes, scope) -> EvidencePacket`, followed by
`investigate(evidence, assessor, operations, answer_policy, work_policy) -> InvestigationResult`.
Input is serialized `trace-description-v1` data with packet/source identity;
S01 packet-plus-sidecar compatibility is also planned. Output retains evidence,
qualifications, incident selections, audit history, usage and separate stop reason,
execution status and evidence adequacy. These interfaces are not implemented yet.

## Dependencies and exclusions

Depends on trace-domain's versioned semantic output, integration's interpreted
scope and declared operations, and caller-supplied legal-answer/provider policies.
Baseline comparisons and GLM annotations are qualified evidence suppliers, not
causal verdicts. Runtime persistence and `solve` remain integration-owned.

Excludes trace encoding, baseline production, live provider experiments, raw
telemetry retrieval, benchmark scoring, default runner changes and publication.
Changes to `docs/architecture.md` and feature 007 are shared integration edits;
this owner does not claim exclusive ownership of those files. Temporary Luna
subagents report through this task and do not own coordination folders.
