# Integration ownership

Owner: [Implement prompt anomaly integration](codex://threads/01a0b11d-e8cc-7900-a614-c4a8ff69bf06)
(task ID `01a0b11d-e8cc-7900-a614-c4a8ff69bf06`).

Owned implementation: `run.py`, `agents/discovery.py`, `rca/{contracts,inputs,outputs,scope}.py`, `rca/discovery/`, the existing discovery adapters `rca/telemetry/{inventory,paths,traces,metrics,logs}.py`, `scripts/{validate_discovery,demo_discovery,demo_investigation}.py`, `docs/demo-discovery.md`, Docker packaging, feature 004 execution artifacts, and this coordination folder. Tests owned here: `tests/integration/test_{discovery,demo_discovery}.py` and `tests/unit/test_{scope,inventory,traces,metrics,logs,budget}.py`.

Public interface: supplied dataset + query CSV → interpreted scopes → deterministic preparation and comparison → per-case findings, operation journals, evidence, zero model usage and blank discovery predictions. Current explicit demo command: `python run.py --dataset DATA --queries QUERIES --out OUT --agent agents.discovery`. Following the user’s later demo/submission direction, the three-flag default is now `agents.routed`: bounded metric discovery with permitted GLM calls and explicit unknown answers. Full feature 004 acceptance remains separate from this published demo checkpoint.

Dependencies: consume domain-owner interfaces through adapters when their handoffs are ready. Baseline/comparison owns `rca/baselining/`, `rca/comparisons/` and its new `rca/telemetry/trace_index.py`; trace-domain owns `libraries/trace_semantics/`; GLM and experiment owners retain their respective experiment code. Do not duplicate or stage those paths. Trace-domain caller assumptions, including fault association, must be respected during integration.

Exclusions: standalone trace semantic encoding, new baseline/descriptor policy implementations, GLM experiments, S01–S09 experiments and investigation-loop domain implementation. Integration owns wiring these into the executable workflow, not rewriting the owners' internals.

Commit boundary: initial runner/contracts/input/output files were already untracked. The user explicitly approved a separate prerequisite baseline commit from the saved starting snapshot, followed by integration changes. The exact 18-file snapshot was committed as `5487b25`; current integration edits were preserved. Do not stage unrelated current worktree content. Temporary subagents report through this owner.
