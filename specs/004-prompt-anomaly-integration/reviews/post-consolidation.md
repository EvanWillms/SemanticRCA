# Post-consolidation acceptance review — 2026-09-17

Review baseline: `ea46d49`, published on `main`. This continues the original
feature 004 objective; the demo checkpoint is not full feature acceptance.

## Later user decisions

The user requested consolidation and publication on `main`, a minimal working
input-to-finding demo, and an explicit “I don't know” result when a diagnosis
cannot be obtained. These decisions supersede the plan's intermediate default
promotion sequence and its downstream prohibition on abstention. They do not
establish feature 004 acceptance or benchmark accuracy. The default router uses
a documented 30-minute metric reference; explicit `agents.discovery` still uses
the original five-minute multimodal discovery policy.

The one approved live provider case was consumed. It returned no usable model
answer. Later transport checks use controlled offline responses; they are not
live inference or accuracy evidence.

## Verified current evidence

| Requirement area | Evidence inspected | Result and limit |
| --- | --- | --- |
| P1, public scope interpretation | Fresh comparison of `data/track-1/query.csv` against independently authored `public-scope-expectations.json` | All 70 rows match deployment, window, count and projection; all seven projections covered. No answers or labels used. |
| Existing runner/discovery behavior | `python3.12 -m unittest discover -s tests -q` at the review baseline | 77 tests pass. This suite does not cover every acceptance scenario. |
| Source-backed output on real data | `eval/assessment-smoke.md` and `/private/tmp/semanticrca-assessment-final` | Two cases finish in 6.334/6.622 seconds with 24 findings each; independent assessment owner checked 48 findings and medians against 1,460 source records. Metric-only coverage, zero model calls. |
| Default failure result | `tests/integration/test_submission_agent.py`, `test_assessment_cli.py`, actual prediction CSV | Missing/unavailable/malformed diagnosis produces requested unknown fields with low confidence; observations remain in evidence. |
| Runtime model eligibility | `rca/model_policy.py`, official `models.md`, `test_model_policy.py` | Exactly the seven official models are permitted at submission and Featherless study request boundaries. |
| Container execution | Image `36883e4ba251678477dd32200e74f027d74bab922298367260df57a6fa061c40`; network-disabled CLI with 2 CPUs/8 GB | Authored fixture emits prediction/evidence/usage and passes structural validation. Not a cold 20-case real-data certification. |
| Provider transport mechanics | Installed SDK against dummy loopback server in network-disabled container; `test_model_client.py` | Raw response handling, usage, large response delivery and bounded worker termination verified without a paid call. |

## Outstanding original acceptance

- Trace continuation now reaches query traces beyond the first 30 historical
  records and preserves completed page comparisons. The cold-data runtime and
  memory limits of repeated enumeration/comparison still require measurement.
- The original multimodal pipeline discarded completed observations after a
  later operation failed. The follow-up retention regression reproduced this
  before the fix; the reviewed fix now retains completed observations and
  source identities with explicit partial status. Validation is recorded below.
- Detailed operation receipts, recorded batch-boundary replay, bounded SQLite
  interruption and complete relationship expansion remain unverified or incomplete.
- Full discovery's cold 20-case CPU/memory/time gate has not been demonstrated.
- Downstream diagnosis accuracy, scorer parity and held-out routed versus
  single-model comparison remain open. Unknown output is useful progress but
  cannot prove these requirements.

The task checklist remains an implementation plan, not a completion claim. The
active goal must stay open until requirement-specific evidence closes the gaps.

## Parent adjudication of the independent review

The additional Luna acceptance review confirmed that unknown root names are
filtered from generic trace evidence by `frontend_only=True`. Retaining those
roots separately, without assigning a frontend role or starving the frontend
page, remains a concrete acceptance gap.

Two other suggestions were not accepted as immediate defects: metric ordering
must keep incompatible contexts separate, so globally sorting raw magnitudes
would violate the same policy; conflicting trace rows already remain in the
raw recovered trace artifact and comparisons are marked unresolved. A fuller
ambiguity/provenance review is still warranted, but these observations do not
justify replacing the current ordering or declaring raw source loss.

## Retention fix verification

The focused test initially failed because the failure result lacked source IDs
and recovered traces. The fix updates retained case state after each completed
retrieval/comparison. Later log failure or deadline exhaustion retains trace
excess +200 and metric difference +25, with the failed operation's status and
source identity. A failure before metric comparison retains retrieved metric
samples without inventing comparison results. Successful comparisons discard
the extra raw-series copy to avoid inflating completed artifacts.

Parent review retained the existing explicit recoverable-exception boundary,
corrected the qualification to refer to completed observations, and kept actual
per-family metric coverage. No arbitrary exception swallowing or new framework
was added. The scope of this correction is completed operation retention;
records local to an interrupted operation may still be unavailable.

Final checks: 79 repository unittest tests pass; `make validate` passes 18 core
tests. The explicit discovery CLI and its artifact validator passed in image
`18cf566e86b57dc4231b9f4fbd54f1f537e430bc29888d7246b64d56e73a1057`,
with network disabled, 2 CPUs and 8 GB. Authored fixture output is at
`/private/tmp/semanticrca-show-live-20260917/discovery-retention-output`.

## Trace pagination follow-up

The CLI regression initially exited partial with no query trace after forty
reference roots. The executor now consumes stable offset pages under its case
budget. Every page records its selection arguments, returned count, next offset,
withheld count, source identity and elapsed time. Comparisons are updated after
each complete page; a forced deadline on the next page retains earlier findings.
Offsets are valid only for identical immutable source and selection arguments.

The Luna API slice verifies 35 authored roots with equal timestamps, unsorted
physical order and cross-partition spans. CSV and prepared-view pages match,
never overlap, and together recover the expected trace IDs. Parent integration
checks forty references followed by the query trace (two pages: 30 and 11), and
a forced later-page deadline after ten query comparisons have completed.
Parent review also removed a redundant raw-series deletion and copied trace
comparison lists before adding metric findings, preserving separate channels.

Validation: all 83 repository unittest checks and 20 `make validate` checks pass.
The multi-page authored fixture passed the discovery CLI and validator in Docker
image `e7518a55d3c6f9addbadf27b05f3c5aeb2a564f08568005cd9e975300836d85a`,
with network disabled, 2 CPUs and 8 GB. Output:
`/private/tmp/semanticrca-pagination-bt1_rile/out`. The query has a raw duration
excess of 200 against forty eligible references; no causal diagnosis is claimed.

This closes first-page starvation on the demonstrated source shape. It does
not certify full-scale runtime: each page currently enumerates matching roots
again and re-compares accumulated records. Bounded SQLite query interruption,
unknown-root generic evidence, replay at recorded parse boundaries and cold
20-case full discovery acceptance remain open.
