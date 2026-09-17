# Random-eight execution amendment

The user reduced the run on 2026-09-17: “pick 8 at random and then review the outputs. do not wait to execute all 69.” This amendment replaces the 69-case execution and evaluation population before any answer-key values were opened. It does not change the frozen detectors, trace attribution, retrieval limits, investigator model, or prediction schema.

## Selection

At 19:52:38 UTC the coordinator executed `sorted(random.Random(42).sample([i for i in range(70) if i != 25], 8))`. The selected rows are **3, 6, 14, 17, 29, 32, 36, 48**. The complete population, seed, command description, and timestamp are preserved in `data/experiments/frontend-blind-v1/orchestration/random8_selection.json`. Selection was not stratified or conditioned on scores, hypotheses, completion status, or incident difficulty.

Rows 0, 1, and 2 had completed as pilots and are excluded from the primary eight-case analysis. Row 3 was already active and continues with its original investigator. Rows 4 and 5 were interrupted because they fall outside the sample; partial artifacts are preserved as user-cancelled runs, not scored diagnostic failures. No remaining unselected investigation will be dispatched.

## Execution and review

Each selected case retains a fresh Luna-high investigator, executed case code, a trace-only seal before metrics/logs, and a final seal. Three investigators can run concurrently. The original 15-minute per-case investigation budget remains. The coordinator records real dispatch-to-seal time rather than trusting agent-written elapsed-time fields.

Before opening labels, verify both seals and completed/failed status for exactly these eight cases. The original all-69 gate is superseded by this explicit user-authorized population change. A separate review wrapper parameterizes the existing evaluator to this subset in memory; the source files covered by investigator seals remain unchanged. It uses a nine-row scope file containing the eight trials and the already excluded control, to retain the existing scope contract. Only the selected cases contribute to primary scores and discovery denominators.

Report per-case trace-only and final scores, requested-field accuracy, evidence quality, execution errors, abstentions, and the raw-duration/MAD/Isolation-Forest discovery comparison. Review the actual evidence and executed code, not only the score. Preserve original predictions after unblinding. Describe failures without repairing predictions, changing thresholds, or substituting another sample.

The sample contains task_2 (2 prompts), task_3 (1), task_5 (2), and task_6 (3), including four two-incident prompts. It does not request a full time/component/reason tuple for any one prompt. Requested-field scores therefore cannot establish full-tuple diagnostic accuracy. Eight prompts are an exploratory sample, not evidence that anomaly detection or root-cause analysis is generally solved. The original restrictions on false-positive and causal claims still apply.
