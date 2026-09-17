# S02–S09 demo result

The deterministic happy path is ready in this workspace. Core validation:
`python3 -m unittest experiments.semantic_encoding_v1.test_s02_s09 -v` — **7/7 passed**.
One Luna extra-high implementation worker and one Luna extra-high final reviewer
were used; root verified the targeted repairs. Review was limited to changed
experiment code and its evidence.

| Slice | Decision | Saved observation |
|---|---|---|
| S02 — Real trace | supported_on_fixture | 37 records, all nine raw fields, 13 entities and 36 parent links retained; exact structures and provenance checked. |
| S03 — Identity | supported_on_fixture | One binding changed; counts and edges stayed equal; frozen same/different entity relations recovered. |
| S04 — Evidence quality | supported_on_fixture | Missing ancestry, both conflicting rows/pointers, and observed root-only children remain distinct; completeness unknown. |
| S05 — Timing | supported_on_fixture | +3/+13 ms offsets and +10 ms change; clock qualifications retained; unknown duration gives no endpoint. |
| S06 — Status | supported_on_fixture | Unmapped, mapped error, mapped error with enclosing success, and mapped non-error remain distinct; mismatched mapping context stays unknown. |
| S07 — Context | supported_on_fixture | Equivalent seconds/milliseconds and UTC+8 round-trip; authored names parse and malformed inputs remain unresolved. |
| S08 — Size | supported_on_fixture | Exact recovery. Cold symbolic/normalized bytes at 1, 10, 100 instances: 644/698, 3,984/6,135, 37,735/60,586. Dictionary/schema overhead included; savings at every tested size. |
| S09 — LLM | inconclusive; provider blocked | After explicit paid-call approval, all six corrected requests reached the endpoint but returned HTTP 403 / Cloudflare 1010 (`browser_signature_banned`). No model outputs or token/cost measurements. |

[Corrected deterministic run](../../../../data/experiments/semantic-encoding-v1/20260917-s02-s09-009/result.md)
contains packets, decoded facts, provenance, frozen expectations, exact checks,
source/code hashes, and cold/amortized size accounting.
[Prepared S09 run](../../../../data/experiments/semantic-encoding-v1/S09/20260917-s09-live-005/result.json)
contains six opaque model-facing requests and a separate frozen oracle. Unknown
usage and cost are null. It made zero transport attempts.

To demonstrate a fresh deterministic run from the repository root, use a new ID:

```sh
python3 -m experiments.semantic_encoding_v1.run_s02_s09 --run-id demo-s02-s08-001
```

Run IDs cannot be reused. This is a local demo: R0 currently depends on the prior
complete trace audit at `/private/tmp/symbolicrca-trace-audit/graph/trace_9451fd8fdf746a80687451dae4c4e984.json`;
R3 uses the saved indexed trace extract. Packaging those inputs for a clean clone
and fresh index retrieval remain outside this minimal happy path.

The initial automatic pass labels were rejected by the [bounded review](S02-S09-review.md).
Corrected expectations and gates were frozen for later attempts; this is not a
claim that the entire original implementation was prospectively validated.
Results remain provisional against authored/source-derived expectations, without
independent human annotation. S04–S08 are isolated checks, and passing them does
not validate a production pipeline. Byte savings do not imply token savings.

The S09 record contains two six-attempt DNS-failed runs (`002` and `004`), with no
provider responses; the previously reported six attempts referred to the latest
run, not the cumulative total. Older labels and zero-valued usage aggregates are
superseded, not overwritten. The current revised six-request screen has not run.
The reviewer confirmed its payloads are synthetic and contain no R0/R3 telemetry.

Automatic approval review rejected escalated Featherless transport as a
credential-authenticated transfer of internal trace-derived data to an untrusted
external endpoint; [the saved denial](../../../../experiments/semantic_encoding_v1/fixtures/s09-auto-review-denial.json)
records the reason. A live synthetic-only run requires resolving that approval
block. No repeated-run reliability claim or remaining twelve calls are included.

Next handoff: demonstrate S02–S08 now; resolve the external-transport approval
separately before running the six prepared S09 requests.

## Approved live attempt

The user explicitly approved paid Featherless requests using the `.env` key.
Run [20260917-s09-approved-001](../../../../data/experiments/semantic-encoding-v1/S09/20260917-s09-approved-001/result.md)
sent the six corrected synthetic requests. All six returned HTTP 403 with
Cloudflare error 1010, `browser_signature_banned`. The response declares
`retryable: false` and `owner_action_required: true`; no identity-changing retry
was attempted. The previous local approval barrier is resolved. The current
blocker is the provider's access rule, not DNS, model semantics, or demonstrated
credential validity. The key did not appear in saved artifacts. Actual billing
and token usage are unavailable, not asserted to be zero.

Core demo tests were rerun: 7/7 passed. Full live capability has **not** been
demonstrated. Featherless must permit this client before another model run;
provide support the saved response's Ray ID `a3cb2cfb79671be5` and timestamp
`2026-09-17T21:24:05Z`. Do not launch additional calls while the block stands.
