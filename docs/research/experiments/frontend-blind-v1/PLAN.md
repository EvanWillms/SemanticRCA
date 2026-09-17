# Frontend-first anomaly detection: blinded development trials, v1

Status: **planning deliverable; no new trial investigations or answer-key evaluation have run**.

Prepared 2026-09-17. Requested investigator configuration: **gpt-5.6-luna, high reasoning**, fresh subagent context for each development prompt. This extends the executed [PyOD case-25 demonstration](../../examples/track-1-case-25-pyod-demo.md).

## 1. Question and claims we will test

The working assumption is that off-the-shelf anomaly detection is sufficient for finding useful starting points, leaving workload comparison and causal investigation as the substantial work.

Test three claims separately:

1. **Discovery:** Does ranking frontend latency produce trace evidence leading to the labelled incident component within a small, fixed inspection budget?
2. **Localization:** Does following explicit dependencies improve the component shortlist over blaming the frontend or simply selecting the longest dependency?
3. **Diagnosis:** Can a Luna-high investigator use the resulting evidence to answer the prompt's requested occurrence time, component, and/or reason? How much is available from traces alone, and how much requires metrics or logs?

Do not equate an unusual request with an incident, a slow receiver with an initiating cause, or symptom time with fault onset. Candidate recall, full diagnosis, and operational alert quality are different outcomes. This dataset has incident-conditioned prompts; it cannot establish production false-positive rates without independently labelled negative windows.

## 2. Scope and experimental units

The inspected label-free query file has 70 rows covering 57 distinct 30-minute windows across March 20–21, 2022. The experiment includes **all 69 rows other than case 25**, representing **56 unique windows**. There are 26 two-incident rows and 43 one-incident rows among those 69.

| Task | Requested fields | Remaining rows |
|---|---|---:|
| task_1 | Time | 12 |
| task_2 | Reason | 10 |
| task_3 | Component | 8 |
| task_4 | Time and reason | 7 |
| task_5 | Time and component | 10 |
| task_6 | Component and reason | 12 |
| task_7 | Time, component, and reason | 10 |

The generated [scope.csv](scope.csv) contains only public prompt fields, parsed time bounds, declared incident count, and exposure flags. No answer-key values are included. Prompt times use UTC+8, consistent with the prior schema audit; telemetry timestamp conversion must be explicit by source.

**One fresh Luna-high investigator per prompt: 69 investigations.** Identical windows may reuse deterministic extraction and detector output, but agents do not share hypotheses, narratives, or predictions. This honors each prompt's requested projection and allows duplicate-window consistency to be measured. For the primary unique-window summary, choose the lowest remaining row ID per window before execution. Report all 69 official row scores separately; do not count duplicate prompts as independent incidents in confidence intervals.

Duplicate-window row groups are: 6/7, 9/10, 11/31, 14/30, 16/17, 22/23, 27/28, 34/35, 37/69, 43/44, 47/48, 51/52, and 55/56.

Case 25 is an **exposed engineering control**, excluded from accuracy and discovery summaries. Case 24's query window was used as case 25's reference and is telemetry-exposed. Case 26's reference includes case 25. Keep both in the requested coverage, flag them, and provide a sensitivity summary excluding them. More generally, adjacent windows can overlap one another's reference data; these are temporally dependent development trials, not an independent held-out test set.

## 3. Blinding and separation of roles

### Investigator inputs

Each fresh agent receives only:

- Its exact public instruction, row ID, parsed window, task fields, and incident count.
- This protocol's investigator-safe extract, frozen configuration, and generic data dictionary.
- The generic Python APIs and a private case output directory.
- Label-free telemetry slices, detector rankings, and bounded retrieval functions.

Agents must use `fork_turns="none"`, model `gpt-5.6-luna`, and reasoning effort `high`. Do not pass the conversation, case-25 narrative, other case reports, or other agents' conclusions. The investigator-safe protocol extract must omit the known component, trace IDs, and numerical results from case 25.

### Prohibited inputs before sealing

- `data/track-1/dev/query_dev.csv`, especially `scoring_points`.
- Any `record.csv`, injected-fault schedule, answer keys, previous diagnosis reports, evaluation reports, or label-derived component filters.
- Arbitrary searches of research/example directories or Git history that could reveal diagnoses.
- Web searches for this benchmark's case answers.

The orchestrator may inspect label-free prompts, schema, code, and execution failures, but must not communicate cross-case diagnoses to investigators. All target predictions must be sealed before **any** trial gold values are read. Do not score and provide feedback after each case.

This is **procedural blinding**: agents share a filesystem and tool access. Directory separation and explicit instructions are not a security sandbox. Log retrieval requests and available execution records; record any known unauthorized read as exposure, preserve the original attempt, and exclude it from the blinded subset. Do not claim that unobserved file access is technically impossible. A truly access-enforced blind evaluation would require a separate runner/container exposing only allowlisted files.

### Evaluator inputs

The evaluator runs only after the seal manifest exists for every included attempt or explicit failed attempt. It may then read the dev scoring points and the official scorer. It cannot edit sealed predictions. Post-unblinding analysis is labelled as such; changes become a new protocol version, never a revised v1 score.

## 4. Frozen discovery experiment

Freeze the following before looking at any new rankings. Case 25 may verify implementation only; do not tune detector settings to new cases.

### Data selection

- Query interval: the entire half-open 30-minute prompt window.
- Reference: the immediately preceding half-open 30 minutes, whether or not it contains another incident.
- Root: blank-parent `frontend-*` span, matching the existing method. Record actual root operation names and any unexpected types.
- Cohort: multiset of recorded direct-child operation names and counts, pooled across frontend replicas.
- Initial collection margin: one minute on each side, as in the prior demonstration. Candidate full traces are recovered separately from all needed daily files.
- Minimum cohort size: 20 reference roots; positive reference median and nonzero MAD. Unsupported cohorts remain explicit coverage failures; do not silently switch to global baselines.
- Empty child signatures are retained and flagged. Missing instrumentation is not assumed to mean no downstream work.
- Query boundaries are based on root start time. Cross-midnight references and traces require both adjacent daily files where available; absent files produce completeness flags.
- Scan unsorted files completely or use a validated index. No early timestamp cutoff.

### Three fixed ranking arms

| Arm | Input and fit | Ranking policy |
|---|---|---|
| A: duration | Raw frontend duration; no fitting | Descending duration across every query root |
| B: packaged MAD | PyOD MAD fitted per reference cohort | Descending signed MAD score; inspect positive departures |
| C: packaged Isolation Forest | One pooled forest on signed reference-cohort MAD scores | Descending anomaly score among positive departures |

Use PyOD 3.6.6 and the exact dependencies in the existing pinned environment. Isolation Forest uses 100 estimators, seed 42, `max_samples="auto"`, and one worker. No feature or hyperparameter search. Default contamination affects the library's threshold machinery, but binary predictions and estimated probabilities are not used.

Arm A reports all-root coverage; comparisons with B/C also report the common eligible subset. Never credit an ineligible B/C request as an implicit miss without separately showing why it could not be scored. Deterministic ordering is score, then trace ID and span ID. Report score-tie rank ranges, not an artificial unique best rank. A sensitivity result including all requests tied at the inspection cutoff may exceed the strict budget and must be labelled separately.

The case-25 comparison showed that rarity and absolute impact can diverge. Preserve both duration and excess milliseconds in every result, but **do not add a new severity filter or retune ranking during v1**. An impact-aware policy would be a separately declared next experiment.

### Fixed inspection budget and attribution

For each arm preserve top 1, 3, 5, and 10 request prefixes. Retrieve the union of top-10 traces across arms once per window, up to 30 distinct traces. Compute every arm's results from its own prefixes; shared retrieval does not allow one arm to borrow another arm's discoveries.

For every selected trace:

1. Verify trace ID scope, unique span IDs, parent resolution, roots, cycles, and interval consistency. Preserve incomplete records and source provenance.
2. Record the slow root's largest direct child by duration and every unambiguous cross-component receiver linked to it. This is the **immediate attribution** shortlist.
3. Traverse recorded descendants to depth 8, visiting each span once, and calculate direct-child interval unions and receiver-uncovered time where duration units and timestamps permit it. Do not sum overlapping child durations as if serial.
4. Build a second **dependency reachability** shortlist: receiver components along recorded descendant paths, ordered by parent-path discovery from the ranked requests, then descending child duration, then component/span ID. Deduplicate exact component IDs. Retain all paths; evaluate component prefixes 1, 3, and 5.
5. Keep immediate attribution, broader reachability, and the agent's final diagnostic component separate. A component's presence anywhere in a large trace graph is a weaker result than accurate causal localization.

Missing links, cycles, ties, excessive depth, and large fan-out are explicit limitations. Cross-host start gaps are observations, not direct measurements of network latency. A receiver with little uncovered time may itself be waiting on another dependency.

## 5. Luna-high investigation for each prompt

Every investigator must write executable case code and run it, not just narrate the supplied summaries. The code should call the shared tested API, select the case, perform its bounded analyses, and regenerate its numerical evidence. It must not copy a diagnosis into code or change the frozen ranking arms.

### Stage T: trace-only investigation

Inspect the same fixed union of candidate traces and their reference statistics. Write:

- A ranked component hypothesis list with explicit supporting parent links and counterevidence.
- A structured incident list preserving associations between time, component, and reason.
- Separate observed symptom timestamp and inferred occurrence timestamp, with uncertainty and rationale.
- A trace-only answer to the requested fields, including explicit abstention where unsupported.

Seal the Stage T prediction before requesting metrics or logs. The stage can diagnose only what the evidence supports; absence of a latency signal is an experimental result, not permission to invent one or use a known label.

The final agent diagnosis uses the union of the arms' evidence. Therefore only the deterministic discovery/localization tables compare detector arms directly. Do not attribute an improvement in the combined agent's final diagnosis to a specific detector. A causal comparison of final diagnosis by detector would require separate isolated agent runs per arm and is outside v1.

### Stage M: bounded metrics/log corroboration

This is a separately reported diagnostic extension, not a redefinition of latency detection success.

- Initial candidates: at most five components selected in Stage T, with explicit linked hosts when mappings exist. Do not infer container-to-node placement from similar names.
- Query and reference intervals remain the same. Retrieve service, container, runtime, node, and mesh metrics only where applicable and mapped.
- Record metric units, timestamp units, sampling cadence, coverage, counter/gauge uncertainty, and missingness. Apply cohort/reference MAD descriptively where supported; counters require an explicit rate conversion with reset handling. Zero-MAD metrics get a degeneracy flag, not an arbitrary epsilon score.
- Metrics retrieval limit: 20 structured calls. Each returns at most 50 series summaries and 120 representative/time-binned values per series. Retain pointers to raw rows and state aggregation semantics.
- Log retrieval limit: 10 structured calls, at most 200 records per call, deterministically ordered. Keep truncation and searched interval/component filters visible. Do not treat absence in a capped response as proof of no event.
- One expansion to an explicitly linked neighboring component is permitted and logged, with at most five additional components. No unbounded global search for the eventual answer.
- If trace discovery supplies no component candidate, record Stage T failure. Allow one labelled **global-metric rescue** using a component-balanced summary of all available components, then the same total retrieval budgets. Rescue successes cannot count as latency-discovery successes.

After corroboration, write and seal the final incident hypotheses and prompt projection. Preserve alternatives and uncertainty. Evidence should distinguish resource changes and observed delays from the unobserved mechanism that might connect them.

### Multiple incidents

Use the prompt's supplied count only as scope. Do not automatically call the top two spans two incidents. Group repeated evidence by component, temporal episode, and dependency relationship, explaining when two anomalies are probably the same chain. Produce the declared number of incident slots with per-field support/abstention, and never combine one incident's time with another's component or reason.

All investigators record all inferred incident fields internally, while official output projects only the requested fields. Missing unsupported values remain empty with explicit abstention in the structured evidence. If the agent makes a best-effort uncertain prediction, identify it as an inference rather than observed fact. Do not fabricate certainty merely to satisfy benchmark formatting.

## 6. Implementation architecture and work ownership

Create a new experiment directory, leaving the previous case-25 script and unrelated project changes intact.

```text
experiments/frontend_blind_v1/
  config.json                 # frozen settings and allowed-input policy
  build_index.py              # label-free source indexing and schema validation
  detectors.py                # the three frozen ranking arms
  trace_evidence.py           # parent joins and interval accounting
  retrieval.py                # bounded, provenance-preserving metrics/log retrieval
  run_case.py                 # deterministic case harness
  seal.py                     # input/code/output hashes and timestamps
  evaluate.py                 # reads labels only after every case is sealed
  tests/                      # meaningful synthetic edge cases
```

Generated telemetry indexes, raw slices, and bulk run artifacts live under ignored `data/experiments/frontend-blind-v1/`; source and curated result summaries live in the repository. Do not commit raw private telemetry. Maintain an artifact inventory and relative source references; temporary paths alone are not a durable result.

Build reusable day-level indexes once so 69 agents do not each rescan gigabytes. SQLite/Parquet or another locally supported index is an implementation choice, not an experimental variable. Indexes must exclude answer files, preserve raw identifiers and source-record provenance, and produce the same extraction as the streaming baseline on the exposed control. Metric units must be checked per source, not guessed from the trace schema.

### Agent schedule

1. **Infrastructure wave:** up to three Luna-high agents independently own indexing/retrieval, detector/trace code, and sealing/evaluator/tests. Evaluator development uses synthetic labels only. They do not run new case diagnosis or read gold.
2. **Preflight:** orchestrator reviews integration; agents fix correctness issues using synthetic fixtures and case 25. Freeze source/config hashes and the investigator prompt template.
3. **Trial waves:** 69 fresh Luna-high agents, at most three active simultaneously, ascending row ID excluding 25. Each writes only its case code, evidence, retrieval log, and outputs. Agents must not mutate shared detector or retrieval code.
4. **Seal gate:** validate coverage of every scheduled row and preserve failed attempts. Hash every Stage T/final prediction and code artifact. No missing cases silently disappear.
5. **Evaluation wave:** a separate evaluator reads labels, scores the sealed artifacts, and generates tables. Fresh Luna-high review agents may audit evidence after unblinding, but cannot revise predictions.

Each case gets a 15-minute investigation budget after its data are ready, shared by Stages T and M. Runtime and retrieval counters are recorded even if the case times out. An infrastructure crash can be retried once with identical inputs/config before unblinding; preserve both attempts and use the first completed protocol-compliant attempt. A timeout or lack of evidence is not a reason for an unconstrained second diagnosis attempt.

At three concurrent investigators, 69 cases require 23 waves. The nominal upper investigation budget is 5 hours 45 minutes, plus indexing, review, scheduling, and evaluation; this is a budget ceiling, not an elapsed-time promise. Do not invent a dollar estimate for subscription-backed subagents. Record model, effort, timestamps, calls and usage when exposed; otherwise report unavailable cost data explicitly.

## 7. Per-prompt artifacts

Each case directory must contain:

- `scope.json`: exact instruction, requested fields/count, reference/query bounds, source identities, exposure flags.
- `investigate.py`: agent-authored executable case analysis using frozen shared code.
- `rankings.json` or CSV: all arm scores, eligibility, cohort counts, top prefixes, tie information.
- `trace_evidence.json`: audited candidate paths and interval measurements with provenance.
- `trace_only.json`: sealed Stage T hypotheses and prompt projection.
- `retrieval.jsonl`: Stage M queries, filters, response counts, truncation, timing, and evidence references.
- `final.json`: incident tuples, requested-field prediction, uncertainty, rescue status, alternatives.
- `evidence.md`: concise investigation narrative with observations, inference, counterevidence, and limitations.
- `run.json` and `seal.json`: agent/model/effort, runtime, errors, source/config/code/output hashes, attempt lineage.

Aggregate `predictions_trace.csv` and `predictions_final.csv` contain all 69 row IDs, with official output fields serialized in the required order: datetime, component, reason. Unknown values must not break the scorer's parser. Preserve a separate machine-readable abstention mask; blank and wrong answers may both receive zero official credit but mean different things experimentally.

## 8. Evaluation after predictions are sealed

### Coverage and discovery

Report all 56 unique windows, including failure/abstention cases:

- Frontend/root coverage; eligible reference cohorts; zero-MAD, sparse-cohort, empty-signature, and incomplete-trace rates.
- For each arm and request budget 1/3/5/10, **immediate-attribution** and **dependency-reachability** recall of exact labelled components.
- Component shortlist recall@1/3/5 and rank of the labelled component where available. Report both any-incident and all-incidents recall for two-incident windows.
- Number of requests and components inspected, absolute excess and duration of selected requests, and frequency of negligible absolute delays among highly ranked anomalies. Describe the distribution; no retroactive threshold selection.

Only score a field when the available gold actually contains it. The dev file supplies task-dependent scoring points, not necessarily full tuples for every window. Duplicate rows can provide additional projections, but do not invent pairings between disjoint time/component/reason lists. For component recall, use consistent component labels supplied by any row in the same window; flag conflicts. Use only directly associated tuples for incident-level matching. Report the denominator for every metric.

### Diagnosis

- Official mean score, fully solved count, and per-task scores for Stage T and Stage M, using the provided unchanged scoring function.
- Requested-field accuracy: exact component, exact reason, and occurrence time within the official ±60-second tolerance.
- Count correctness, abstention by field, malformed-output rate, tuple association errors, and diagnostic precision where assessable.
- Separate Stage M gains from candidate-led corroboration versus global-metric rescue.
- Duplicate-window agreement, without using one agent's answer to repair another's.
- Time error distributions only where time labels exist; inferred onset and observed symptom times remain distinct.

Reason strings must be evaluated under the official exact-match contract. Report obvious terminology mismatches in post-hoc error analysis without silently normalizing predictions using the gold answer. Any permitted taxonomy must come from pretrial public documentation, not the dev scoring points.

### Evidence and efficiency

Mechanically verify every cited source row/trace and parent link where possible. Audit all claimed complete diagnoses and all failed evidence checks, plus a fixed sample of abstentions. Classify support as direct observation, comparative inference, mechanism hypothesis, or unsupported assertion.

Report indexing separately from per-case extraction, fitting/scoring, trace retrieval, agent investigation, and evaluation. Report read volume, retrieval calls, and model usage when available. Do not present detector-only milliseconds as end-to-end RCA latency.

### Comparison and uncertainty

Primary comparisons are paired on unique windows with available labels. Publish wins/losses/ties between arms, absolute differences, and transparent denominators. If uncertainty intervals are provided, resample whole unique windows with seed 42; label them descriptive because adjacent windows share traffic and only two days are represented. Include per-day results and the sensitivity subset excluding cases 24 and 26. No generalization claim to unseen systems or cleanly held-out incidents is warranted.

## 9. Preflight correctness checks

Before the new trials:

1. Parse every prompt and verify its 30-minute window, midnight transitions, task projection, and failure count without opening scoring points.
2. Reproduce case-25 counts, package scores within tolerance, winning trace, and exact dependency links. Reuse it only as the exposed control.
3. Check streaming/index equivalence, string-preserved span IDs, unsorted inputs, duplicate IDs, missing parents, cycles, overlap-union arithmetic, zero-duration spans, and cross-file retrieval on compact synthetic fixtures.
4. Check sparse/new/zero-MAD cohorts and absence of frontend requests produce explicit coverage failures rather than crashes or silent substitutions.
5. Check query data do not affect fitted MAD/forest reference parameters; scores agree for singleton versus batch query evaluation.
6. Check the evaluator on synthetic one/two-incident outputs, absent fields, exact reason matching, ±60-second boundaries, key order, and mismatched failure counts. Validate no trial labels are opened during this step.
7. Check sealed prediction hashes fail validation after mutation and that evaluation refuses to run with unsealed/missing attempts.

These tests verify the reusable analysis, data boundary, and scoring contract. They are not tests that hard-code expected answers for blind cases.

## 10. Completion and interpretation

The experiment is complete when all 69 prompts have a sealed completed/failed attempt, every unique window appears in coverage reports, original predictions are immutable, official and discovery metrics are computed with correct denominators, and a detailed result report explains successes and failure modes with reproducible evidence.

No minimum accuracy is required to declare the experiment completed. A poor result is useful and must remain visible.

Interpret possible outcomes as follows:

- **Duration ≈ MAD ≈ forest, good candidate recall:** sophisticated anomaly scoring adds little under this setup; prioritize dependency reasoning and evidence retrieval.
- **MAD/forest materially outperform duration:** reference-aware comparison contributes value; quantify that gain before adding complexity.
- **Good component recall but poor time/reason answers:** discovery is adequate, diagnosis remains difficult.
- **Poor latency discovery but successful metric rescue:** the chosen frontend-latency channel has limited coverage; do not call this success for the original method.
- **Sparse coverage or contaminated references dominate:** fix data/cohort design in a declared v2; do not tune v1 after seeing gold.

The final report must include all-row results, unique-window summaries, exposure/missingness/error ledgers, per-case links, detector comparisons, trace-only versus corroborated diagnosis, resource usage, and actionable recommendations. Post-hoc repair experiments get separate hashes and result tables.

## 11. Project-governance scope

This is a user-requested research extension, not the complete unattended challenge submission or the symbolic-compression feature. It preserves the constitution's evidence, provenance, bounded access, and reproducibility requirements. The requested Luna-high agents are the research execution model; they do not replace the project's GLM/Featherless submission contract.

Documented scope exception: the full Spec Kit feature implementation sequence, Docker/submission packaging, and routed-versus-single-model comparison are deferred for this isolated experiment. Reason: the user explicitly requested a detailed experimental plan and per-prompt Luna-high research trials. Impact: results may inform a later feature, but cannot be claimed as a submission-ready agent. Owner: project maintainer; follow-up: capture any chosen production integration as a separate Spec Kit feature and validate its runtime/model/evidence/cost contract before claiming completion.
