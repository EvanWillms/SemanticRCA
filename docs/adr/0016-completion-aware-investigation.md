---
status: accepted
date: 2026-09-17
---

# Assess completion before ending a bounded investigation

## Context

The architecture separates evidence preparation, investigation and answer
assembly, but its stop condition combines sufficient evidence with exhausted
budget. An answer artifact cannot distinguish a supported conclusion from a
forced best guess or an investigation that cannot proceed.

The [primary-source review](../research/minimal-agent-loop-sources.v1.md) records
Google's sufficiency/gap reflection, LangChain Open Deep Research's explicit
completion decision, and smolagents' final-answer checks and bounded execution.
Some upstream paths share a finalizer for sufficiency and iteration exhaustion.
We adopt the control pattern and preserve different reasons for stopping; these
sources do not prove causal accuracy.

## Decision and trade-offs

- Use one investigating agent and one accumulating state containing scope,
  source-linked evidence, current hypotheses, attempts and budgets. Planning,
  answer revision and sufficiency assessment share one assessment step.
- Assess initial evidence before follow-up and reassess after each attempted
  operation. Propose `complete`, `continue` or `blocked` with supporting reasons.
  A deterministic controller validates proposals and may stop independently on
  resource exhaustion or provider failure.
- Accept completion only when the requested projection/count is legally
  assemblable, each selected incident has a source-linked explanation, material
  contradictions and plausible alternatives are addressed, and no unresolved
  gap prevents the requested conclusion. Code validates reference integrity and
  answer legality; semantic adequacy remains fallible model judgment.
- Continue through exactly one declared operation that could resolve a named
  gap. Retain unsuccessful, empty, rejected and truncated attempts. Frozen
  comparison policies and ADR 0006's operation boundary remain unchanged.
- Preserve distinct terminal reasons: `evidence_sufficient`, `missing_source`,
  `missing_capability`, `no_useful_action`, `stalled`, `provider_failure`,
  `invalid_assessment`, `budget_exhausted`, `unsupported_scope`, and
  `no_legal_answer`. Inability is relative to this run's evidence and capabilities;
  missing one source does not preclude other useful operations.
- Start the toy profile with at most three attempted follow-up operations and
  four assessment-provider attempts, including repairs/retries. Reserve time/cost
  for reassessment and finalization before dispatch. Timeouts and case/run caps
  still apply. These are initial test defaults, not measured optimal limits.
- Reject identical operations against unchanged sources, scope and policies,
  except bounded retries for recorded transient failure. Two consecutive
  operations with no new evidence, coverage knowledge or source-backed gap
  resolution constitute `stalled`. Rephrasing or increased confidence is not
  progress; a valid empty selection can add coverage knowledge.
- Finalize from retained state without requiring another live model call. Keep
  terminal reason separate from execution status and evidence adequacy. ADR 0007
  still requires legal best guesses for valid judged cases. Forced assembly
  cannot turn incomplete investigation into evidential completion.

This adds an inspectable decision boundary and predictable work limits without
introducing a general agent framework. The model can still misjudge its answer;
controlled tests verify behavior, while held-out evaluation measures diagnosis
quality. Conservative sufficiency criteria may increase qualified best guesses,
which must remain visible rather than being hidden by formatting.

## Alternatives not selected

A fixed step count cannot establish completion. An unconditional final-answer
action trusts the agent without checking evidence or legality. Treating every
non-success as abstention conflicts with the benchmark. A separate critic,
researcher swarm, planning tree or framework dependency adds complexity the toy
does not need.

## Consequences and verification

[Feature 011](../../specs/011-completion-aware-investigation/spec.md) owns the
assessment loop, terminal reasons, progress rules and controlled trajectories.
[Feature 007](../../specs/007-evidence-backed-diagnosis/spec.md) retains diagnosis,
incident selection, output legality and evaluator compatibility; features 003–004
supply evidence and operations. Feature 002 retains provider, runtime,
comparative evaluation and release authority.

Verify initial completion without tools, useful follow-up, unsupported completion,
missing evidence with/without alternatives, repetition, malformed assessments,
provider failure and budget exhaustion. Terminal paths preserve uncertainty,
audit records and legal best-guess obligations. This ADR specifies future behavior;
it does not certify implementation, benchmark correctness or release readiness.
