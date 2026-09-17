# Integration source notes

## Official documentation alignment — 2026-09-17

Reviewed all four files in the user-designated local `hackathon-2026-official/track-1/docs`
checkout, revision `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`. Hashes identify the
actual working files read, independently of that revision. This is a local source
review, not live provider-price verification. No telemetry or answer files were
opened; data.md itself includes an illustrative labelled case, which was not used
to choose a discovery rule or fixture answer.

| Official source | Governing facts | SHA-256 |
|---|---|---|
| [data.md](../../../mantisgrid-hackathon/hackathon-2026-official/track-1/docs/data.md) | Seven projections; 30-minute scopes; timestamp seconds versus milliseconds; UTC+8; schema families; different judged deployment; exact reason vocabulary | `c3813bb8447c28af56940027da3521c54d8b1b9fed6882f3235c01c998c24bda` |
| [submission.md](../../../mantisgrid-hackathon/hackathon-2026-official/track-1/docs/submission.md) | Three-flag Docker CLI; read/write and endpoint restrictions; row_id; ordered answer fields and chronological incidents; four evidence sections; final repository/release requirements | `087efc658ab24b47b4afb4292e17c3b23bd786c60a526c1588aeafcd392521f6` |
| [scoring.md](../../../mantisgrid-hackathon/hackathon-2026-official/track-1/docs/scoring.md) | Exact count/string/field order, 60-second time tolerance; permutation-tolerant evaluator; best guesses; strict/partial and per-task evaluation; repeat/configuration comparisons | `3fbbe6f435139d243453dcf5cceed55f19add04c987a4b5fda740a65dadbc6af` |
| [models.md](../../../mantisgrid-hackathon/hackathon-2026-official/track-1/docs/models.md) | GLM-only routing; environment-selected endpoint/key; HTTP-200 capacity errors and fallback; $3/600s per case and $25/1200s per 20 cases | `8dd746f48aa5bd4c1db1c7ecfebd90ba72903a47560b016d8f6f1770e133d77e` |

The official docs require a working diagnostic submission. Blank predictions and
no-call discovery are project-only intermediate milestones. Feature 007 owns best
guesses with legal answers and evidence; feature 002 owns final packaging,
routing evaluation and release checks. Emit chronological incidents per submission.md
even though scoring.md permits permutations. Local numeric exit codes, source
journals, stricter label isolation, reproducibility checks and the initial detector
policy are project choices, not additional rules attributed to the organizers.

The data guide does not define trace duration units, a portable frontend-entry
algorithm, anomaly thresholds, a five-minute reference, 20-sample support, or
packet sampling. [The initial project policy](contracts/discovery-policy.md)
explicitly supplies these design choices where applicable, retains provisional
duration units and requires fixture validation. Source-name topology is contextual
binding evidence; a parent/child time gap does not by itself prove network transit
or causal fault. No official example component, row count or date is a runtime
allowlist. Runtime never requires this neighboring checkout.

## OpenRCA adoption amendment — 2026-09-17

The [adoption map](../../docs/openrca-adoption.md) pins the inspected OpenRCA and official Track 1 sources. OpenRCA's Market prompt is an adapter reference, not an authoritative component inventory or diagnostic policy. Official `docs/scoring.md` and `docs/submission.md` govern final best-guess output, row identity, exact strings and field ordering; this feature remains the intermediate no-call discovery stage. Added FR-015/016 and O1/O2 specify validated inventories and auditable bounded operations. No runtime acceptance was executed.

Read on 2026-09-17 from the supplied workspace; no external research or benchmark labels were needed.

- Official neighboring repository: `track-1/docs/data.md`, `track-1/docs/submission.md`; the provided content defines the seven task types, 30-minute scope, UTC+8, mixed timestamp units, exact resource labels, CLI and runtime limits. The local public `data/track-1/query.csv` has row_id/task_index/instruction columns and 70 rows. Inspected representative wording for every task type and multiple failures; no gold answers were read for scope generation.
- [Feature 002](../002-final-demo-runner/spec.md), its implemented runtime and strict placeholder validator: working empty-output scaffold; the new discovery output requires a distinct validation path and an explicit retained stub regression mode.
- [Feature 003](../003-contextual-telemetry-evidence/spec.md) plus ADRs 0003–0005: authoritative qualified retrieval, comparison and resource-linkage requirements; current research code is not proof of compliance.
- `experiments/frontend_blind_v1/run_case.py` uses a development scope.csv and local artifacts, fixed index defaults and a multi-arm top-prefix experiment. It is a reuse candidate, not directly portable production integration.
- `experiments/short_window_baselining_v1/analysis.py:_query_inventory` first joins development scopes by ID and has a fallback parser limited to March 20/21, 2022. That is insufficient for interpreting arbitrary supplied Track 1 rows from another deployment/date. `replay.py` assumes 57 development windows; that count cannot become a runtime requirement.
- The locally inspected ignored `data/experiments/short-window-baselining-v1/selection.json` freezes five-minute pooled C1 (recorded direct-child operation/type set), median and signed absolute excess, no fallback, and an independent structural channel. Qualifications include exposed telemetry, unverified health/workload/replica equivalence, provisional raw-duration microseconds and no incident-sensitivity/calibrated-threshold claim. Selection is for descriptive replay, not a proven root-cause detector.
- The local final research report records a roughly 322-second index build and about 13.44 GB on disk, with much larger experimental exports than the demo needs. These are reported research measurements, not freshly verified integration results. Cold preparation, storage and memory must be assessed within judging limits; do not transplant the full matrix/replay pipeline or assume warm state.

Only source/policy facts needed to frame the integration are captured here. Do not package ignored research results, private source paths or per-case answers into the runtime. Planning must choose and freeze concrete portable discovery policies and demonstrate controlled correctness plus Track 1 runtime fit before claiming integration complete.
