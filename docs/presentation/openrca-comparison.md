# SymbolicRCA additions relative to OpenRCA

“OpenRDA” in the presentation request is interpreted as OpenRCA, the locally available reference project. Comparison date: September 17, 2026. Upstream inspection is pinned to revision `c1bd4af7f635171a1c31cdd567c07d698dff6abc`. This compares source and proposed architecture; it is not a benchmark run or a claim of field-wide novelty.

## Existing upstream foundation

OpenRCA provides a benchmark for natural-language RCA queries over metrics, traces, and logs. Its RCA-agent baseline already performs iterative investigation using Python retrieval and analysis to avoid putting all telemetry into the model context. The controller issues atomic instructions, the executor runs generated Python in a stateful IPython kernel, and observations feed subsequent steps. The controller has a step limit and the executor has bounded retries. [README](https://github.com/microsoft/OpenRCA/blob/c1bd4af7f635171a1c31cdd567c07d698dff6abc/README.md), [controller](https://github.com/microsoft/OpenRCA/blob/c1bd4af7f635171a1c31cdd567c07d698dff6abc/rca/baseline/rca_agent/controller.py), [executor](https://github.com/microsoft/OpenRCA/blob/c1bd4af7f635171a1c31cdd567c07d698dff6abc/rca/baseline/rca_agent/executor.py).

## Proposed additions

| Area | Inspected OpenRCA baseline | SymbolicRCA target | Intended benefit to evaluate |
| --- | --- | --- | --- |
| Evidence representation | Python execution results, summaries, and recorded trajectories | Versioned symbolic descriptions retaining observations, temporal relationships, provenance, and explicit limitations | More compact evidence without losing information needed for diagnosis |
| Reference selection | Prompt instructions for whole-file KPI thresholds, threshold relaxation, and localization heuristics | Eligible contextual reference cohorts with fixed policies and qualified or unavailable comparisons | More defensible comparisons when context or coverage differs |
| Tool interface | Model-generated Python in a stateful kernel, bounded by step/retry limits | Declared deterministic retrieval and comparison operations with bounded scope, structured outcomes, and stop reasons | More repeatable operations and inspectable failures |
| Reasoning records | Iterative analysis and instruction history with final incident selection | Separate observations, comparison findings, hypotheses, contradictions, and selected incident tuples | Clearer evidence support and uncertainty accounting |

The upstream comparison policy is described in its [diagnosis prompt](https://github.com/microsoft/OpenRCA/blob/c1bd4af7f635171a1c31cdd567c07d698dff6abc/rca/baseline/rca_agent/prompt/agent_prompt.py). SymbolicRCA's additions are specified in the [target architecture](../architecture.md) and [adoption decisions](../openrca-adoption.md).

## Presentation wording

“OpenRCA already gives us the benchmark and an agent that investigates telemetry with Python. Our proposed contribution is a symbolic evidence layer with qualified comparisons and bounded, repeatable operations. We still need to measure whether that improves diagnosis and efficiency.”

Multimodal RCA, agentic follow-up, tool use, and execution bounds are inherited concepts, not standalone novelty claims. The user’s client-side tool idea extends the delivery of investigations when initial evidence is insufficient. Prompt optimization via auto-research is another future direction; no novelty or performance claim is established for it.

## Implementation boundary

The repository's [README](../../README.md) and [report](../../REPORT.md) currently document an offline, empty-output harness. Experimental code and accepted specifications do not establish a completed diagnoser. Describe the items above as proposed additions until integration and validation support a stronger statement. Accuracy, evidence quality, token usage, cost, and latency improvements remain unmeasured.
