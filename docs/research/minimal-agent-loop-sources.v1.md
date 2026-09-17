# Minimal agent loop: primary-source notes

Verified online 2026-09-17. These are concrete open implementations of modern deep-research patterns, not a claim that one is the current benchmark leader. Source links track upstream `main` and may change. This note supports [the project toy-loop design](minimal-agent-loop.v1.md); it proposes no framework dependency.

## Three patterns worth borrowing

| Implementation | What the source actually does | Transfer to a toy RCA loop |
| --- | --- | --- |
| Google Gemini fullstack LangGraph quickstart | A `reflection` node produces structured `is_sufficient`, `knowledge_gap`, and `follow_up_queries`. A deterministic `evaluate_research` router searches again or finalizes when either sufficiency is true **or** the configured loop cap is reached. Both exits share the finalizer. [Source: graph.py](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart/blob/main/backend/src/agent/graph.py) | Assess the current evidence, name a remaining gap, and choose the next action. Keep the routing in ordinary code. Record *why* the loop ended separately from producing an answer. |
| LangChain Open Deep Research | The supervisor can call `ResearchComplete`. Its tool node ends research on that call, absence of tool calls, or iteration-limit exhaustion. The prompts ask for assessment after research, narrower searches for gaps, and stopping on repeated information. These are prompts and control-flow rules, not proof that findings are correct. [Source: deep_researcher.py](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/deep_researcher.py), [source: prompts.py](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/prompts.py) | Reassess after every observation. Track unfilled requirements and avoid repeating an exhausted action. Do not treat silence, a stop tool, repeated results, or a resource cap as evidence of completion. |
| Hugging Face smolagents / Open Deep Research | `MultiStepAgent` repeats action/observation steps until a final answer or `max_steps`. Optional `final_answer_checks` validate proposed answers; failed checks raise an agent error. At the cap it generates a best-effort answer, while the full `RunResult` can record `max_steps_error`. The Open Deep Research example uses bounded manager and browser agents and allows clarification requests through `final_answer`. [Source: agents.py](https://github.com/huggingface/smolagents/blob/main/src/smolagents/agents.py), [API docs](https://huggingface.co/docs/smolagents/main/reference/agents), [example: run.py](https://github.com/huggingface/smolagents/blob/main/examples/open_deep_research/run.py) | Gate a proposed result before accepting completion. Preserve a legal best-effort answer on unsuccessful termination, with the unsuccessful stop reason recorded separately. |

## Design inference for SymbolicRCA

The following is a synthesis for this project, not an upstream framework guarantee:

1. Keep one state record: task requirements, observations, current candidate answer, remaining gaps, attempted actions, and remaining budget.
2. Before returning, run an explicit assessment: does the current evidence satisfy the completion requirements? Require evidence references and pass deterministic validity checks; model confidence alone is insufficient.
3. If incomplete, identify one available action that could close a named gap. Perform it and assess again.
4. If no useful feasible action remains, stop with an explicit inability reason and the unresolved gaps. This means inability **with the present evidence and capabilities**, not a proof that the underlying problem is impossible.
5. If a budget ends the run, record budget exhaustion separately. An iteration cap bounds work; it does not establish inability or success.
6. Keep outcome status distinct from the answer payload. For a valid judged case, the project requires a legal best guess even when evidence is insufficient; emitting that guess must not change the status to evidential completion. This is the local requirement in [ADR 0007](../adr/0007-evidence-backed-incident-diagnosis.md).

For a toy implementation, this reduces to `assess → complete / cannot continue / one action → observe → assess`, with a separately enforced budget. A framework, parallel researchers, planning tree, and independent critic agent are unnecessary to express that control flow. The same model may assess and choose actions; deterministic code should enforce valid outputs, evidence-ID existence, action availability, budget accounting, and terminal status.

The chief limitation is that a model-based sufficiency assessment can still be wrong. None of the cited control loops alone proves a causal diagnosis. The toy design should make that assessment inspectable and testable rather than promising that reflection guarantees correctness.
