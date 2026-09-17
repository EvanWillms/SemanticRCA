# SymbolicRCA Constitution

## Project Vision and Success Criteria

SymbolicRCA builds an unattended root-cause-analysis agent for the labelled
incidents in the supplied Track 1 microservice benchmark.

**A failure is a labelled incident in the supplied benchmark, represented by its
occurrence time, root-cause component, and fault reason.** Occurrence time means
the fault's start time. Dataset operators establish the incidents by injecting
and labelling faults; each query supplies a 30-minute window and failure count.
The agent MUST reconstruct when each failure began, which component caused it,
and why from telemetry, returning the fields requested by the task and a
defensible explanation with supporting evidence. It is not required to establish
that a customer-visible outage or reliability/SLO breach occurred.

The complete deliverable MUST diagnose those incidents and explain its evidence.
The first experiment tests only one necessary part: whether the correct component
reaches the shortlist. Candidate recall alone does not establish complete diagnosis,
onset accuracy, fault-reason accuracy, or completion of the deliverable.

See [ADR 0001](../../docs/adr/0001-benchmark-failure-definition.md) for the source
contract and the distinction from MantisGrid's broader product framing.

The project optimizes the joint outcome of accuracy, evidence quality, cost, and
wall-clock time. A solution is successful only when it performs credibly on
unseen cases, explains each conclusion from telemetry, compares meaningful
configurations, and can be built and run by the evaluation environment.

## Core Principles

### I. Evidence-First Root Cause Analysis

Every predicted root cause MUST be tied to concrete telemetry observations and
an explicit causal explanation. The agent MUST preserve enough case-specific
evidence for an evaluator or engineer to understand why the answer was reached.
When evidence is incomplete or contradictory, the output MUST represent that
uncertainty rather than inventing support. This keeps the system useful even
when the final diagnosis is wrong.

### II. Query-Bounded Telemetry Access

The agent MUST operate under the assumption that telemetry is too large to read
in one model context. It MUST query, filter, aggregate, or otherwise retrieve
only the information needed for each decision. Data access logic MUST remain
separate from reasoning logic so retrieval behavior can be tested and improved
without silently changing the diagnosis contract.

### III. Cost-Aware Model Routing

The agent MUST treat model selection as part of the solution. Cheap and fast
models SHOULD handle filtering, extraction, and formatting when they are
adequate; stronger models SHOULD be reserved for decisions that require deeper
reasoning. Any routing strategy MUST be measurable in dollars, latency, and
diagnostic quality, and MUST never trade away required evidence merely to reduce
cost.

### IV. Reproducible Evaluation on Unseen Cases

The project MUST include an evaluation harness that compares at least the
routed agent with the same agent running on a single model. Evaluation MUST
use cases separated from development or tuning data, record configuration and
cost inputs, and produce repeatable metrics for accuracy, evidence, cost, and
wall-clock time. Changes to the agent MUST be judged against a documented
baseline rather than anecdotal examples.

### V. Explicit Runtime and Submission Contract

The deliverable MUST run unattended in the provided evaluation environment,
include a Dockerfile, read credentials only from `FEATHERLESS_API_KEY`, and
write the required `predictions.csv` plus one
`evidence/<row_id>.md` file per case. Runtime behavior MUST be deterministic
enough to debug, must not depend on developer-local paths or interactive input,
and MUST avoid committing credentials, private telemetry, or generated artifacts
that are not part of the source deliverable.

## Operational Constraints

The implementation targets the GLM model family on Featherless and MUST honor
the model prices, routing rules, rate limits, and submission contract documented
by the challenge materials. The agent MUST not assume that judging will reuse
the developer's account, local data, network configuration, or uncommitted
state. The repository MUST retain the scripts, configuration, and evaluation
instructions needed to reproduce a submitted run without spending the judge's
credits during evaluation.

The challenge's participant agreement and scoring documents govern any conflict
between this constitution and external judging requirements. Secrets belong in
the runtime environment, never in source, specifications, evidence fixtures,
or version history.

## Development Workflow

Work MUST proceed through the Spec Kit sequence:

1. `$speckit-specify` records a testable feature specification.
2. `$speckit-clarify` resolves material ambiguity when needed.
3. `$speckit-plan` defines the technical approach and evaluation impact.
4. `$speckit-tasks` produces dependency-ordered implementation work.
5. `$speckit-implement` executes the approved tasks.
6. `$speckit-analyze` and `$speckit-converge` check consistency and remaining
   work before the feature is considered complete.

Each feature MUST identify its acceptance evidence, including the relevant
evaluation, contract, or regression checks. A change that improves accuracy but
breaks evidence generation, cost accounting, reproducibility, or the submission
interface is incomplete. Constitution amendments MUST be reviewed for their
effect on existing specifications, plans, tasks, and evaluation comparisons.

## Governance

This constitution is the highest-level project agreement for repository work.
Feature specifications, implementation plans, tasks, and code MUST comply with
it. Exceptions MUST be documented in the applicable plan with the reason,
impact, and a follow-up task or approval owner.

Amendments MUST state the affected principles or sections, explain the rationale,
update the semantic version, and record the amendment date. Versioning follows
semantic rules: MAJOR for incompatible removals or redefinitions, MINOR for new
principles or materially expanded obligations, and PATCH for clarifications that
do not change project governance. Before an amendment is committed, the sync
impact report MUST be reviewed and removed from the file.

Every review of a specification, plan, implementation, or submission MUST
include a constitution-compliance check. The project maintainer or designated
reviewer is responsible for resolving conflicts and confirming that the
evaluation evidence supports any claimed improvement.

**Version**: 1.0.1 | **Ratified**: TODO(RATIFICATION_DATE): Set when the team formally adopts this constitution. | **Last Amended**: 2026-09-17
