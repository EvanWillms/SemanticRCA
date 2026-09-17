# Demo integration code review

Review boundary: this task's additions and the integration delta from the exact
18-file starting snapshot, separately committed as `5487b25`. Other owners'
domain implementations and unrelated shared-checkout edits are excluded from
this task's commit. Ready library handoffs were reviewed by their owners.

Parent review and an independent Luna extra-high review found no remaining
blocker for the declared minimal synthetic demo. The final review covered:

- `run.py`, `agents/discovery.py`, `rca/{contracts,inputs,outputs,scope}.py`
- `rca/discovery/{__init__,pipeline,budget}.py`
- `rca/telemetry/{__init__,inventory,paths,traces,metrics,logs}.py`
- `scripts/{validate_discovery,demo_discovery,demo_investigation}.py`
- `Dockerfile`, `.dockerignore`
- `tests/unit/__init__.py`, `tests/unit/test_{scope,inventory,traces,metrics,logs,budget}.py`
- `tests/integration/test_{discovery,demo_discovery}.py`

Fixed findings: reject source paths outside the supplied bundle; propagate
partial metric collection; retain metric reference membership and observations;
select declared frontend roots before the trace response cap; preserve all
recorded spans for selected traces. Speculative compatibility aliases were
removed. The latest root-selection regression checks 31 unrelated trace IDs
before a frontend root and verifies recovery of its child outside the window.

The independent final review checked the trace-domain and investigation adapters
and found no actionable demo blocker. Semantic encoding keeps raw evidence and
deferred meanings. The RCA callbacks are visibly scripted; their answer does not
claim causality. The official discovery prediction stays blank, with zero model
usage. `frontend_only=True` is recorded in operation arguments.

Evidence: 45 focused core tests pass on Python 3.12. The complete one-command
workflow passed in a network-disabled Docker container with 2 CPUs and 8 GB
memory. The execution log records the exact image and report location.

Deferred acceptance findings: the operation journal and run metadata do not yet
provide the complete planned replay/resource contract; complete pagination,
controlled partial replay and scheduler-wide prepared-source reuse remain open.
The 30-trace demo cap can withhold query evidence in larger source windows and
is reported as partial. The scripted loop has no hard callback cancellation or
validated causal assessor. Full real-data cold-20 gates, semantic evidence graph
validation and default promotion are not certified by this review.
