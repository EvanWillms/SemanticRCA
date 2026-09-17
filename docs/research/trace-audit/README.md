# Reproduce the Track 1 trace audit

These are read-only diagnostic scripts supporting the [audit report](../track-1-trace-audit.md), not the experiment's ranker. Run from the repository root using Python 3.10 or newer. The source is the extracted organizer bundle; no gold files or network access are used. Each command scans the entire March 20 trace CSV; the semantic script retains only its first 100,000 records plus the selected trace. Outputs go to a temporary directory and can contain raw telemetry.

```bash
mkdir -p /private/tmp/symbolicrca-trace-audit-reproduction
python3 docs/research/trace-audit/audit_trace_span.py data/track-1/telemetry/2022_03_20/trace/trace_span.csv /private/tmp/symbolicrca-trace-audit-reproduction/schema.json
python3 docs/research/trace-audit/audit_trace.py data/track-1/telemetry/2022_03_20/trace/trace_span.csv 9451fd8fdf746a80687451dae4c4e984 /private/tmp/symbolicrca-trace-audit-reproduction/graph
python3 docs/research/trace-audit/audit_trace_semantics.py data/track-1/telemetry/2022_03_20/trace/trace_span.csv /private/tmp/symbolicrca-trace-audit-reproduction/semantics.json
```

Expected invariants: 9,132,857 source records, nine fields with zero wrong-width rows; selected trace has 37 unique spans, one blank-parent root, 36 resolved links, 19 same-emitter and 17 cross-emitter relations. The source SHA-256 is recorded in the report and schema JSON.

The parent review corrected the retained scripts to keep exact integer root/nonroot endpoints distinct. Under the microsecond hypothesis, root duration is 93,829 us and the latest nonroot endpoint is +93,228 us. A maximum that includes the root cannot independently establish its duration unit. Broader sampled enclosure/slack statistics use floating point and are descriptive, not fine-grained clock evidence.

Scope limits: full-day lexical validity does not establish full-day graph integrity; the selected trace's resolved graph does not prove full instrumentation or health; the first-record sample is structurally incomplete and cannot establish missing-parent rates or feature eligibility. No production parser, causal detector, benchmark score, or fault verdict is supplied by these scripts.
