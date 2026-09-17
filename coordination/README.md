# Task coordination

Each owning task maintains its own `scope.md` and `status.md`. Temporary
subagents report through their owner. Update status at checkpoints, blockers
and handoffs. Stable ownership belongs in scope, not in transient status.

| Area | Owner task | Ownership | Current handoff |
| --- | --- | --- | --- |
| Integration | [Implement prompt anomaly integration](codex://threads/01a0b11d-e8cc-7900-a614-c4a8ff69bf06) | [scope](integration/scope.md) | [status](integration/status.md) |
| Trace domain | [Refactor deterministic trace library](codex://threads/01a0b12d-bf7a-7ca3-89e7-f57c076cd47f) | [scope](trace-domain/scope.md) | [status](trace-domain/status.md) |
| Baseline comparison | [Implement baseline descriptor plans](codex://threads/01a0b13b-d809-7c80-a199-c868d40b8781) | [scope](baseline-comparison/scope.md) | [status](baseline-comparison/status.md) |
| Investigation loop | [Sketch toy agentic completion loop](codex://threads/01a0b128-5479-7042-9de2-80514655a78a) | [scope](investigation-loop/scope.md) | [status](investigation-loop/status.md) |
| GLM semantics | [Plan GLM trace classification](codex://threads/01a0b111-80cb-71c3-96f9-39a179706944) | [scope](glm-semantics/scope.md) | [status](glm-semantics/status.md) |
| Experiments | [Run incremental experiments handoff](codex://threads/01a0b11c-9d3b-7f80-95af-7679e2420aae) | [scope](experiments/scope.md) | [status](experiments/status.md) |

For demo coordination, **ready** means an available interface and one passing
happy-path check. It does not mean full acceptance, scientific generalization,
or production readiness; those gaps remain explicit in status.

Use this short status format:

```yaml
State: working | ready | blocked | paused
Updated:
Latest checkpoint:
Working now:
Demo evidence:
Next handoff:
Blocker / overlap:
```
