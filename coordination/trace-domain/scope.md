# Deterministic trace domain ownership

Owner: [Refactor deterministic trace library](codex://threads/01a0b12d-bf7a-7ca3-89e7-f57c076cd47f)
(`01a0b12d-bf7a-7ca3-89e7-f57c076cd47f`).

Owned paths:

- `libraries/trace_semantics/`
- `specs/011-deterministic-trace-domain/`
- `coordination/trace-domain/`

Public interface: caller-selected fault-related recovered trace envelopes
(`trace_id`, `deployment`, `spans` with exact Track-1 `raw` fields and `locator`)
and explicit `EncodingPolicy` → `partition_traces` returns accepted facts,
retained raw evidence and deferred items → `describe` returns a deterministic
versioned description set. `encode_traces` composes both stages;
`canonical_json` and `description_digest` support serialization and audit.

Dependencies: Python standard library at runtime, setuptools for packaging.
Caller owns fault association, retrieval completeness, source identity and
operation/unit policy declarations. The original source trace remains retained.

Exclusions: telemetry retrieval, baselining, model/GLM calls, diagnosis, experiment
runners and application integration. No modifications to `rca/`, `agents/` or
`experiments/`. Other tasks may consume the interface after a ready handoff.
Temporary Luna TDD and review subagents report through this owner; this owner
alone stages and commits its implementation files.
