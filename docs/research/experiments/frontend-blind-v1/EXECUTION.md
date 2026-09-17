# Execution record: frontend blind v1

Execution was explicitly requested on 2026-09-17 after the [plan](PLAN.md) was written. The scheduled population is 69 development prompts and 56 unique windows. Model selection is `gpt-5.6-luna` with `high` reasoning for infrastructure agents and independent case investigators. Fresh case contexts use no conversation fork.

The source implementation is in [experiments/frontend_blind_v1](../../../../experiments/frontend_blind_v1). Private generated indexes, case evidence, predictions, and the orchestration ledger are under `data/experiments/frontend-blind-v1/`, which is ignored by Git.

## Provenance and exposure

The orchestrator recorded SHA-256 hashes for all 16 allowed telemetry CSV files before the trial wave. Their combined size is 11,936,919,880 bytes. Answer-key files are excluded from this inventory and from the investigator inputs.

The public starter's node/container reason vocabulary is provided equally to investigators. Its source is `track-1/starter/agents/heuristic.py` (`NODE_REASONS` and `POD_REASONS`), not dev scoring points. Names are permitted vocabulary, not a metric-to-cause inference rule.

Case 25 remains an exposed engineering control. The scope register flags case 24 as previously used reference traffic and case 26 as having a reference overlapping the exposed control. Fresh agents receive no previous case diagnoses. Blinding is procedural because agents share filesystem access.

## Pretrial integration checks

Infrastructure code is reviewed and corrected before any trial investigator starts. Reviews include timestamp/duration unit conversions, immutable stage snapshots, persistent retrieval budgets, source row provenance, reference/query isolation, and scorer input/tuple compatibility. These corrections are implementation fixes, not detector tuning based on new-case results.

The final source/configuration freeze and all investigator dispatches are recorded in the private orchestration directory. The answer key may be opened only after the complete-case seal gate passes. Original predictions are not repaired after scoring.

The completed SQLite index contains 18,160,322 trace spans, 15,455,234 metric rows, and 25,772,490 log rows. The exposed-control regression and 18 synthetic integration tests passed before the source freeze at 2026-09-17 19:39:47 UTC. All 70 deterministic inputs were prepared (69 trials plus the control). The first investigators started after their own inputs were ready, while preparation of later rows continued; no investigator input was subsequently overwritten.

Execution issues are preserved in `orchestration/dispatch.jsonl`. Case 2's agent-written runtime fields disagree with machine timestamps, so reporting uses dispatch-to-final-seal time. Case 1 attempted the global seal gate and learned only that case 0 had not finished; it reported no access to another case's evidence or labels. Later dispatch instructions explicitly reserve the global gate for the coordinator. These issues do not justify changing predictions.

## Results

The user reduced execution to eight random prompts before any labels were opened. See [RANDOM8-AMENDMENT.md](RANDOM8-AMENDMENT.md) for the fixed sample, interrupted runs, and revised evaluation gate. All eight completed and passed both stage seals. The [results and output review](RANDOM8-RESULTS.md) report 2/8 fully correct requested answers and a 25% mean official score, plus the identity-granularity limitation that makes the exact trace-discovery comparison uninformative here. The report also compares the user-supplied short-window baselining study, which was read after the eight outputs were sealed. The 69-case run is no longer scheduled.
