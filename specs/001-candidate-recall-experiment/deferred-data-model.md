> **Deferred historical artifact.** This describes the previous candidate-recall integration study, not the active first experiment. Use [the revised assertion plan](plan.md). No CLI, loader, fusion pipeline, or full benchmark run described below is required for the first test.

# Experiment data model

| Entity | Required fields | Invariants / relationships |
|---|---|---|
| Query | row_id, task_index, window_start/end, failure_count, deployment | Original row provenance; timezone explicit; start < end |
| EvaluationUnit | unit_id, row_ids, window, failure_count, split_block_id | Exact duplicate windows collapse; conflicting metadata raises an error |
| SplitBlock | block_id, unit_ids, split, seed, grouping_reason | Related/overlapping incidents cannot cross split boundaries |
| GoldRecord | unit_id, event_id, component?, reason?, onset?, source_rows, completeness | Evaluator-only; absent is null, never guessed; ambiguous event pairing excluded from joint metrics |
| Component | canonical_id, level, raw_ids, parent_node?, service?, mapping_evidence | Preserve pod versus node identity; ambiguous aliases cannot produce an exact match |
| RawSpan | trace_id, span_id, parent_span_raw, timestamp_ms, duration_raw, duration_scale?, emitter_cmdb_id, type_raw, status_raw, operation_raw, source_record | Preserve opaque IDs/leading zeros and raw strings; empty parent is observed no-parent marker; blank type is valid; zero duration is retained with quality metadata |
| SpanRelation | parent_key, child_key, resolution, relation_kind, operation_match?, role_inference?, clock_quality | Composite-key join; classify same-component/cross-component; conflicting duplicates cannot be silently overwritten; missing parent in a prefix is not a missing span in the source |
| Interaction | parent_span_key, child_span_key, caller_emitter?, receiver_emitter?, operation_normalized?, role_confidence, provenance | A derived interpretation, not a raw column; preserve original span graph; never infer a database component from a DB operation name alone |
| ReferenceStats | channel, series_or_edge, count, median, MAD, excluded_windows, clock_policy, data_hash, eligibility_reason | No gold values; reference selection shared across matched arms; constant baseline is distinct from absent/normal data |
| Episode | id, channel, subject_or_edge, feature, state, start/end, onset_interval, strength, count, provenance, missing_reason? | State follows plan thresholds; concurrent edges remain separate |
| Candidate | unit_id, method, rank, component, metric_score, trace_score, fused_score, onset?, episode_ids | Unique component per ranking; deterministic ties; no gold input |
| Run | run_id, data/source/config/split hashes, runtime_versions, method_ids, status | Immutable after holdout unlock; preserve failed attempts |
| Result | unit_id, method, status, candidates, elapsed, peak_rss, rows/bytes_scanned, evidence_bytes | Every input unit yields result or explicit failure; failures count as misses |

Workflow: inventoried → grouped → split frozen → development → configuration frozen → rankings written → holdout scored → report frozen. Any change after holdout scoring creates a new run and marks reused holdout information as exposed.

Episode lifecycle: NORMAL → RISE/HIGH/DROP or isolated SPIKE → RECOVER; MISSING breaks persistence. Already-abnormal initial observations have left-censored onset. Unavailable channels and observed normal channels are distinct even when both contribute zero score.

Trace-quality rules from the [actual-data audit](../../docs/research/track-1-trace-audit.md): a 37-span example has a self-contained recorded tree but does not establish instrumentation completeness or health. Intervals use integer arithmetic and retain the 1 ms timestamp precision; apparent sub-millisecond overlap does not prove concurrency. Status semantics remain unknown unless resolved by instrumentation-specific evidence. Raw duration-to-time conversion is an explicit, provenance-bearing decision, not a consequence of timestamp units. No lookup of gold labels was performed in this audit.
