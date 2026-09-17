---
status: accepted
date: 2026-09-17
---

# Diagnose associated incident tuples from qualified evidence

OpenRCA separates anomaly discovery from localization, but its baseline prompt also promotes percentile excursions, the most downstream faulty component, and the first anomalous sample into diagnostic rules. Those heuristics are not causal guarantees. SymbolicRCA's discovery stage deliberately returns candidates rather than answers.

## Decision and trade-offs

- Keep observations, qualified comparison findings, diagnostic hypotheses and final incident selections distinct. Candidate count is not the requested failure count; only final answer assembly must satisfy the supplied count.
- Form hypotheses that retain associated onset, component and reason, with source-linked supporting and contradicting observations, relationship qualifications, alternative explanations and unresolved questions.
- Use targeted follow-up operations to distinguish hypotheses within declared budgets. Shared timing, a large deviation, a downstream position or a single anomalous KPI is insufficient by itself to establish cause.
- Preserve observed behavior onset separately from estimated fault onset. Sampling gaps, delayed effects and unit uncertainty qualify onset estimates; the evaluator's time tolerance must not be used to manufacture evidence precision.
- Discover component identities in the current deployment and map them to legal output names with explicit identity evidence. Select reason strings from the governing Track 1 vocabulary; distinguish the selected fault reason from the observed behavior description.
- Emit exactly the requested incident count and projection when scope is supported and legal answer choices are available, following the official scoring document and feature 002's best-guess requirement. Low confidence, an empty candidate set or provider exhaustion never authorizes abstention on a valid judged case. Mark weak selections as best guesses in the internal result and evidence. Never fabricate observations, exclusions, confidence probabilities or independent incidents to justify that count.
- If scope is unsupported or no legal answer can be assembled, return an explicit failed case with a blank prediction and honest evidence, continue recoverable work, and return nonzero overall. Such output is an operational failure artifact, not a valid completed diagnosis, and fails final acceptance. It does not create an exception to the official always-guess requirement for valid judged inputs.
- Budget/provider exhaustion may yield a legal best guess with explicit limitations. A completed output artifact does not establish evidential adequacy or benchmark correctness.

This preserves unattended output when evidence is weak without converting a format requirement into a claim of certainty. Diagnostic uncertainty remains visible even when the benchmark requires a decisive answer string.

## Alternatives not selected

Forcing discovery to produce exactly N anomalies would discard or invent candidates. Copying OpenRCA's instruction to avoid uncertainty would violate evidence-first reporting. Replacing every uncertain answer with abstention would conflict with the final runner's best-guess requirement. Treating every sampled onset as the injected fault onset would conflate observation with inference.

## Consequences and verification

[Feature 007](../../specs/007-evidence-backed-diagnosis/spec.md) owns hypothesis comparison and answer assembly. Feature 004 remains a no-call, blank-prediction discovery milestone. Controlled cases must cover competing explanations, masked service effects, repeated correlated observations, separate incidents sharing a component, and insufficient evidence. Diagnosis quality requires a separate held-out evaluation; no heuristic is accepted as effective by this ADR. See the [source and adoption notes](../openrca-adoption.md).
