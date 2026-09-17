# Harness report

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
