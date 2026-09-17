# GLM semantics ownership

Owner: [Plan GLM trace classification](codex://threads/01a0b111-80cb-71c3-96f9-39a179706944)
(task ID `01a0b111-80cb-71c3-96f9-39a179706944`).

Owned paths:
- `docs/adr/0015-featherless-trace-semantics-and-prefix-caching.md`
- `specs/008-featherless-trace-semantics/`
- `experiments/semantic_encoding_v1/{featherless_p01,run_p01,score_p01,test_p01}.py`
- `docs/research/experiments/semantic-encoding-v1/P01-*.md`
- Local ignored `data/experiments/semantic-encoding-v1/P01/` and P01 preflight evidence.
- `coordination/glm-semantics/`

Public interface: frozen authored normalized/symbolic trace packet plus the
structural prompt → bounded Featherless response, immutable attempt evidence,
source-grounded fidelity score and qualified token/cache/cost summary.
`run_p01` provides prepare, run and offline score commands. It is an experiment
interface, not the application's production classifier.

Dependencies: experiment owner's S01 source fixtures/codebook, frozen P01
manifest, optional Featherless credentials for explicitly requested new live
runs. Offline tests/scoring require no credentials or model access.

Exclusions: standalone trace library and spec 011, S01/S02–S09 implementation,
production integration, baseline comparison and investigation loop. Broader
status/causal interpretation and cross-trace prefix effectiveness are not
established by P01. Subagents report through this owner.
