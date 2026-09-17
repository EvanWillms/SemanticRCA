# Submission checkpoint report

## Final integration status

The default runner now selects a GLM-backed submission adapter over the deterministic
discovery path. It formats the requested incident fields and retains a qualified
best guess on provider failure. The earlier harness record below describes the
original milestone; the explicit `agents.submission` mode preserves it.

The combined authored demo passed in a network-disabled Docker container with
2 CPUs and 8 GB RAM. It produces trace and metric departures, baseline descriptors,
semantic trace descriptions and a scripted investigation receipt. Those results
demonstrate plumbing and source retention, not causal accuracy.

**Missing evaluation:** we have not completed a routed-versus-single-model RCA
benchmark comparison, held-out diagnosis accuracy, or a cold 20-case resource
rehearsal. No scores are invented. Separate semantic-model experiments are
documented under `docs/research/experiments/semantic-encoding-v1/`; they do not
substitute for end-to-end RCA evaluation. The S09 transport repair reached HTTP
200 for six requests, while its unchanged semantic scorer remained 0/6.

Known failure modes include truncated trace windows, insufficient historical
support, ambiguous correlated metric departures, unknown semantic operations,
unavailable models and an uncalibrated best-guess fallback. Full submission
compliance and performance are not certified by the synthetic checks.

## Status

This revision covers the empty-output harness milestone only. The runner validates inputs and writes the required artifact shape for every valid query. Prediction values are intentionally blank, evidence identifies diagnosis as unimplemented, and usage records contain no model calls or tokens.

The harness uses no API key, telemetry reader, model client, network connection, or paid call. Its zero usage is a property of the stub, not a measurement of a future diagnoser.

## What is and is not measured

The scaffold can demonstrate CLI execution, CSV/path preflight, original-ID preservation, evidence-file structure, zero-call usage records, and output checkpointing. This report makes no claim about diagnosis correctness, routing quality, evidence quality, accuracy, latency under benchmark load, cost, or model reliability. Those measures are not implemented or not measured in this milestone.

The harness validator recognizes expected placeholders and reports harness-shape validation. That result must not be presented as official benchmark validation, and blank predictions must not be sent to the official answer validator as a successful diagnosis.

## Remaining final-runner gates

The final runner still needs a telemetry-grounded diagnoser, exact incident projections, evidence review against raw files, bounded model access and fallback, routed versus single-model evaluation, repeated runs with cost/time accounting, held-out split controls, constrained 20-case rehearsal, secret/image/fresh-clone audits, and release/submission verification. None of those gates has a result in this report. The release checklist remains pending until those requirements are actually exercised.


## Harness verification

The parent-reviewed scaffold passed 26 tests and a two-query Docker smoke run with networking disabled, 2 CPUs, 8 GB RAM, read-only inputs and root filesystem, and only the output mount writable. [Validation details and review records](specs/002-final-demo-runner/checklists/harness-validation.md) document this limited result. It does not establish final-agent performance.
