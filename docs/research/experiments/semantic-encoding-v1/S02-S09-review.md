# S02–S09 final review

Date: 2026-09-17. Scope: `experiments/semantic_encoding_v1/run_s02_s09.py`,
`test_s02_s09.py`, and saved run `data/experiments/semantic-encoding-v1/20260917-s02-s09-002/`.
This review is limited to the changed experiment; it does not rereview the repository.

Focused tests pass (`python3 -m unittest experiments.semantic_encoding_v1.test_s02_s09 -v`).
The saved S02–S08 table reports every slice supported, but the following issues keep
that result from being a reliable screen.

| Severity | Location | Finding and required fix |
|---|---|---|
| P1 | `run_s02_s09.py:430-456`, `:398-411`; `test_s02_s09.py:13-22` | The S02 gate does not use independent frozen expectations and does not compare all required facts. `freeze` and `expected_rows` are built from the same `load_r0()` rows immediately before encoding; the test also compares decoded rows to those same rows. `run_slice()` marks a run passed from raw-row/provenance checks while `edge_count` is informational, and no exact edge set or entity set is compared. A packet with a corrupted edge set but the same count still passes (confirmed by a bounded probe). The “reviewed once” boolean is only a self-authored marker. Add a committed/hash-checked S02/R3 expectation input authored before implementation, assert the exact requested trace IDs and inventory, and make the pass gate compare exact parent links, entities, counts, all nine fields, and one-to-one source pointers. |
| P1 | `run_s02_s09.py:461-470`; `test_s02_s09.py:24-30` | S03 does not test entity relations. It checks only operation-count equality, edge count, and that some node has `catalog#new`; it neither compares the exact edge set nor independently derives the expected same/different-entity span pairs. The encoder has no relation fact in the decoded contract. Compare T0 and the rebind on exact unordered relation sets, retain raw identities/provenance, and add a negative control that would fail if only the new entity label were retained. |
| P1 | `run_s02_s09.py:160-170`, especially line 169; saved `S04-missing-parent` | A synthetic incomplete retrieval with no `instrumentation_completeness` field is labelled `structure_completeness: qualified`; a bounded check reproduces this. Missing-parent evidence therefore carries an unjustified completeness claim. Treat missing/unknown instrumentation and any retrieval other than complete as `unknown`, and assert that in the S04 expected facts. Also require the conflicting group to contain both conflicting node IDs and both evidence pointers. |
| P1 | `run_s02_s09.py:275-283`; `authored_s06_cases()` | Status mapping is not context-scoped: `interpret_status()` applies any `entries` dictionary to every row without checking producer/context scope or mapping evidence. A mapping authored for one producer can silently turn the same raw value from another producer into `reported_error`. Require an explicit matching scope key, otherwise return `unknown`, and retain/assert mapping version and evidence ID. |
| P2 | `run_s02_s09.py:490-498`; `test_s02_s09.py:32-38` | S05 emits clock qualifications, but the pass rule never asserts them. A cross-emitter implementation could report a numeric offset while omitting `cross_emitter_clock_alignment_unknown` and still pass. Assert same-emitter and different-emitter qualification/uncertainty exactly, alongside the +3/+13/+10 and unknown-endpoint checks. |
| P2 | `run_s02_s09.py:288-307`; `test_s02_s09.py:32-38` | The name grammar accepts malformed mesh names such as `x.destination.y.` because the destination regex permits trailing/consecutive dots; only one malformed container case is tested. Use a label-by-label grammar with no empty labels or trailing dot, freeze the expected name cases separately, and add malformed mesh negatives. |
| P2 | `run_s02_s09.py:520-532` | S08 reports cold symbolic bytes and a dictionary byte subtotal, but never reports an explicitly amortized dictionary/schema cost or a reuse/crossover calculation. Add per-instance payload bytes and an explicit amortized formula under a declared reuse count, then base the narrow size decision on cold and amortized measurements with exact-fidelity checks. |

The saved run evidence is useful for inspection: S02 has 37 rows/13 entities/36
resolved links and provenance audits pass; S04, S05, S06, S07 and S08 outputs are
present. The evidence does not cure the independence and pass-gate defects above.
S09 in this run is a six-slot not-run record; a separate live-client attempt is
required before evaluating the S09 access/claim status.

## S09 live attempt review

The new runner and `data/experiments/semantic-encoding-v1/S09/` attempts were
reviewed separately. Each frozen request contains only the authored synthetic
`status.case` row (`trace_id: synthetic`, `span_id: s`, `cmdb_id: service`) and
synthetic mapping/verifier evidence. No R0/R3 IDs or real trace rows were sent in
the six request bodies. The schedule is six calls, one per case/representation,
with normalized/symbolic order counterbalanced. Requests are persisted and hashed
before transport; responses, usage, validation, adjudication, and credential audit
files are retained. The current-code attempt `20260917-s09-live-004` made six DNS
failed requests and is correctly `inconclusive`; it has no model outputs or actual
token measurements. Attempt `-002` is an older-code artifact whose transport-failure
result is misleadingly `falsified` and whose aggregate transport fields are null;
it must not be used as the S09 result.

| Severity | Location | Finding and required fix |
|---|---|---|
| P1 | `run_s09_live.py:87-120` | Model-facing payloads leak the expected case through `packet_id: s09-unmapped_14`, `s09-mapped_error`, `s09-mapped_error_verified_success`, and raw evidence IDs such as `S06-mapped_error:record:1`. This violates the no-answer-leakage requirement and would make any future entailment pass uninformative. Use opaque packet/evidence IDs in requests and keep the case-to-ID mapping evaluator-only. |
| P1 | `run_s09_live.py:24`, `:87-135`, `:295-297` | S09 expected facts are generated at runtime from `authored_s06_cases()` imported from the S02–S08 runner; no separately authored/hash-checked S09 fixture precedes this implementation. A change to that helper can change both payload and oracle. Freeze a separate synthetic S09 input and expected-facts file before the live runner, hash it in the manifest, and compare outputs only to that frozen file. |
| P1 | `run_s09_live.py:230-242`; bounded validator probe | Unsupported-claim adjudication is an incomplete regex heuristic. For example, a response limitation `Business outcome unknown; backend target appears to be database.` passes `validate_response()` with `entailment: true`, even though it asserts an unsupported backend target. Replace the regex-only check with a bounded claim vocabulary/structured limitations (or independent claim adjudication), and add negative controls for unsupported target, cause, retry, and success/failure claims. |
| P1 | `run_s09_live.py:355-365`; saved `S09/20260917-s09-live-004/result.json` | Missing provider usage is summed as numeric zero (`input_tokens: 0`, `output_tokens: 0`) while `missing_usage` is nonzero. This is not an actual token measurement and can mislead the required representation comparison. Emit `null`/`unavailable` aggregates whenever any selected call lacks numeric usage, and suppress token/cost conclusions. |
| P2 | `run_s09_live.py:323-327`, `:349-365` | The run records prompt/completion usage and latency, but has no per-call or aggregate cost field even when usage is returned; only rates and `observed_charge: null` are stored. Add an explicitly labelled estimated-cost calculation from actual usage and frozen rates, or mark cost unavailable in the result schema. |

The live S09 screen therefore supports no labeling or representation claim: the
current attempt is transport-inconclusive, and the model-facing leakage and
validator gaps must be repaired before another authorized run.
