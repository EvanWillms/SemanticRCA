# Track 1 trace audit: actual schema, recorded relationships, and experiment corrections

Date: 2026-09-17. Status: descriptive data audit completed; no RCA ranking or benchmark evaluation run.

## Result

The CSV is usable, but a row is an instrumentation span record, not a service-to-service call. The selected trace contains both local nesting and plausible caller/receiver pairs. Its mixed status representations, zero durations, unsorted storage, and timestamp/duration precision require explicit handling before meaningful trace symbols can be produced.

Three `gpt-5.6-terra` subagents at medium reasoning independently examined (1) full-day schema and lexical types, (2) one complete recorded trace graph, and (3) a bounded semantic sample and the experiment assumptions. The primary agent checked the outputs, corrected sampling/precision interpretations, and updated the experiment documents. No `dev/query_dev.csv` gold labels were read, and no fault was diagnosed.

## Scope and reproducibility

- Source: `data/track-1/telemetry/2022_03_20/trace/trace_span.csv`.
- File size: **1,357,227,973 bytes**.
- SHA-256: `42057b3325dc32bda37fc98feaf07a9edb48bcf394f5b511e18b38f23670f550`.
- Full lexical scan: **9,132,857 data records**, plus the header.
- Selected trace: `9451fd8fdf746a80687451dae4c4e984`, recovered by scanning the entire file.
- Supporting semantic sample: first **100,000 physical-order data records**, spanning local 00:00:00.361–02:39:58.110. This is neither a complete set of traces nor a random sample.
- Both day directories exist. The March 21 trace header/first rows were inspected initially; full-day findings below apply only to March 20.
- Label-free query inventory: **70 rows, 57 distinct windows**; 44 windows occur once and 13 occur twice. This does not establish 57 independent faults or complete gold coverage.

The selected trace begins at `1647705600361` epoch milliseconds: `2022-03-19T16:00:00.361Z`, or **March 20 00:00:00.361 UTC+8**. It is outside the declared query windows. This avoids selecting it using a fault answer, but does not prove it is healthy. Schema summaries over the full day are not a held-out RCA evaluation.

Reusable audit scripts are in [trace-audit](trace-audit/README.md). Full extracted telemetry and detailed working JSON remain in `/private/tmp/symbolicrca-trace-audit/`; they are not copied into the source documentation. Logical source record numbers below include the header as record 1; the graph extractor also stores physical line positions.

## 1. Observed schema and types

All records have exactly nine fields; no wrong-width rows were found. A CSV-aware reader is still required: row order and the logical record boundary must not be guessed from string operations.

| Column | Observed March 20 contents | Parsing contract |
|---|---|---|
| `timestamp` | Nonempty 13-digit integers; 1647705600361 through 1647791999992 | Signed 64-bit integer epoch milliseconds; preserve raw value |
| `cmdb_id` | Nonempty strings; 40 distinct recording components | Opaque identity string; maintain explicit aliases to metric component IDs |
| `span_id` | Nonempty, 16 lowercase hex characters | String, never numeric; preserve leading zeros |
| `trace_id` | Nonempty, 32 lowercase hex characters | String; combine with span ID for joins |
| `duration` | Nonempty nonnegative integer strings; 0 through 72,735,156 | Preserve integer raw units; record conversion and confidence separately |
| `type` | `rpc`, `telemetry`, `http`, `db`, or empty | String/category; empty is valid unspecified type |
| `status_code` | Eight distinct strings with mixed numeric/text representations | String; interpretation must be instrumentation-specific |
| `operation_name` | Nonempty strings; 29 raw values | Preserve original; normalize only with an explicit matching policy |
| `parent_span` | Empty or 16 lowercase hex characters | Empty is observed no-parent marker; otherwise composite-key reference |

Only `type` and `parent_span` contain empty fields: 554,823 and 418,518 respectively. No literal `0` parent sentinel or self-parent was found in this lexical scan. Nonempty missing parents, duplicate identities, and cycles were tested for the selected trace, not exhaustively across every trace in the day.

Numeric-looking hexadecimal IDs can accidentally satisfy decimal/scientific-notation parsers. This is a reason to declare ID columns as strings explicitly, not infer their type from a sample. The example includes leading-zero span ID `006ff86f3e6096d9`.

### Type and status distributions

| Raw type | Records | Raw status values and counts |
|---|---:|---|
| `rpc` | 6,291,109 | `0`: 6,065,575; `OK`: 225,150; `1`: 140; `4`: 218; `13`: 6; `14`: 20 |
| `telemetry` | 1,161,828 | `0`: 1,161,828 |
| `http` | 735,181 | `0`: 375,083; `200`: 359,965; `13`: 133 |
| `db` | 389,916 | `Ok`: 389,916 |
| empty | 554,823 | `0`: 554,823 |

The local official guide reports illustrative counts of 27 operations and four statuses; the actual March 20 file has **29 and eight**. Do not hard-code the guide's counts. A nonzero-string check would flag 975,548 records, including every `200`, `OK`, and `Ok`. A numeric-only parser cannot represent 615,066 text-status records. Even `type=http` does not imply HTTP status semantics: `0` and `13` also appear there. This audit has not established a definitive error mapping for each producer; error-fraction features remain disabled.

Operations include naming variants such as `hipstershop.PaymentService/Charge` and `grpc.hipstershop.PaymentService/Charge`; leading-slash variants; `HGET`, `HMSET`, `GET`, `SET`; and both `hipstershop.AdService/GetAds` and `hipstershop.adservice/getads`. Matching may account for known wrappers, but arbitrary lowercasing or service-name rewriting could merge distinct instrumentation. Preserve both raw and normalized forms.

Components include names such as `adservice-0` and `adservice2-0`. The extra `2` is not a replica suffix to discard automatically.

## 2. Storage order is not execution order

There are **3,059,987 adjacent timestamp decreases** in the March 20 file. The second data record is already earlier than the first. A filter must stream all records or query a validated index; stopping at an out-of-window timestamp loses data.

The example's 37 spans lie between source records **3 and 1,203,024**. Its root appears at record **300,575**, long after some children. A prefix parser would incorrectly report missing parents and an incomplete trace.

The first-100,000-record semantic sample has 19,180 resolved parent relations and 76,228 unresolved nonroot references. **That is a sample-truncation observation, not a dataset orphan rate.** The selected trace itself has no unresolved parent after full-file retrieval. File-prefix samples also cannot establish actual per-minute call volume or baseline eligibility.

A two-minute temporal buffer alone does not solve noncontiguous storage or missing ancestors. Time-filter the whole file, then resolve ancestry with an explicit retrieval budget and adjacent-date policy. A successfully resolved recorded graph does not prove that all execution activity was instrumented.

## 3. One trace, reconstructed

| Property | Observed value |
|---|---:|
| Span records / distinct composite identities | 37 / 37 |
| Recording components | 13 |
| Root-marked spans | 1, with blank parent |
| Resolved parent relations | 36 |
| Same-component / cross-component relations | 19 / 17 |
| Duplicate keys / ambiguous parents / orphans | 0 / 0 / 0 |
| Self-loops / detected cycles | 0 / 0 |
| Zero-duration records | 4 |
| Raw types | 27 rpc, 3 empty, 3 http, 2 telemetry, 2 db |
| Raw statuses | 33 `0`, 2 `200`, 2 `Ok` |

An abbreviated span-context tree (indents encode parent references, not inferred network hops):

```text
frontend-0: Frontend/Recv.                          root
├── frontend-0: CheckoutService/PlaceOrder          apparent caller span
│   └── checkoutservice-2: CheckoutService/PlaceOrder  apparent receiver span
│       ├── checkoutservice-2: CartService/GetCart
│       │   └── cartservice-1: /CartService/GetCart
│       │       └── cartservice-1: HGET
│       ├── checkoutservice-2: ProductCatalog/GetProduct (two calls)
│       ├── checkoutservice-2: Shipping/GetQuote and Shipping/ShipOrder
│       ├── checkoutservice-2: Payment/Charge
│       ├── checkoutservice-2: Cart/EmptyCart → cartservice-0 → HMSET
│       └── checkoutservice-2: Email/SendOrderConfirmation
├── frontend-0: Recommendation/ListRecommendations
│   └── recommendationservice-0 → productcatalogservice-2
├── frontend-0: ProductCatalog/GetProduct (five calls)
└── frontend-0: Currency/GetSupportedCurrencies
```

The root is span `952754a738a11675`, recorded by `frontend-0`, raw type `http`, raw status `0`, operation `hipstershop.Frontend/Recv.`.

The first three spans illustrate the distinction:

| Span ID | Recording component | Operation | Parent | Source record |
|---|---|---|---|---:|
| `952754a738a11675` | frontend-0 | Frontend/Recv. | empty | 300575 |
| `a652d4d10e9478fc` | frontend-0 | CheckoutService/PlaceOrder | `952754a738a11675` | 3 |
| `60fb4dba9b9d4a42` | checkoutservice-2 | CheckoutService/PlaceOrder | `a652d4d10e9478fc` | 902104 |

The first relation is local nesting on frontend; the second connects two recording components and plausibly represents two sides of one RPC. Both PlaceOrder records have `type=rpc`, so type alone cannot identify client/server role. The 36 parent relations are not 36 interservice calls.

Similarly, `HGET` recorded on `cartservice-1` describes a database operation, but no Redis component ID is present in that record. Projecting it to a particular Redis pod would invent a target.

## 4. Time and duration: facts versus inference

**Established from data and documented convention**: timestamp values are epoch milliseconds. The March 20 file bounds align with March 20 in UTC+8. The node metric begins at the matching epoch-second value `1647705600`. A 09:00 UTC+8 query starts at `1647738000` seconds; treating the same clock text as UTC shifts the window by eight hours. Preserve the native baseline separately from this correction.

**Strong inference, not explicit producer metadata**: duration raw units behave like microseconds. In the selected trace:

| Frontend child operation | Start offset, ms | Raw duration | Duration if microseconds, ms | Next child starts after, ms |
|---|---:|---:|---:|---:|
| PlaceOrder | 0 | 49,877 | 49.877 | 50 |
| ListRecommendations | 50 | 4,740 | 4.740 | 5 |
| GetProduct | 55 | 7,614 | 7.614 | 8 |
| GetProduct | 63 | 7,398 | 7.398 | 7 |
| GetProduct | 70 | 9,230 | 9.230 | 9 |
| GetProduct | 79 | 5,907 | 5.907 | 6 |
| GetProduct | 85 | 5,907 | 5.907 | 6 |
| GetSupportedCurrencies | 91 | 2,228 | 2.228 | — |

The root's raw duration is **93,829**; microsecond interpretation yields **93.829 ms**, consistent with this dispatch sequence and encompassing the last child's endpoint at +93.228 ms. The latest child start is +92 ms. Treating those durations as milliseconds instead creates tens of seconds of overlap and slack in a sequence whose starts are separated by milliseconds. This strongly favors microseconds but does not prove the exporter contract for every span type/day.

Merely choosing the scale with most parent-child enclosure is unsound: both millisecond and microsecond hypotheses enclose 35/36 example relations. The broader incomplete sample even gives more enclosure to millisecond scaling. Larger durations can mechanically increase enclosure. Use producer metadata where possible and multiple timing consistency checks; retain the scale decision in configuration.

For precision, use integer `timestamp_ms * 1000 + duration_raw` when assuming microseconds; avoid adding small float durations to large epoch floats. Preserve millisecond start-time precision and unknown inter-host clock synchronization.

### Zero durations and apparent overlap

The full-day scan found **673,248 zero-duration records: 387,141 database and 286,107 HTTP spans**. The selected trace has two HTTP and two database spans with raw duration zero. One zero-duration HTTP EmptyCart span starts at offset +43 ms; its zero-duration HMSET child starts at +44 ms. Literal interval enclosure therefore fails, but the parent reference resolves. This does not establish a broken trace or a failed database operation. Zero can reflect instrumentation or duration quantization; that interpretation remains unresolved.

Four sibling pairs appear to overlap by **398, 230, 453, and 106 microseconds** under the microsecond hypothesis. All are below the 1 ms start-time granularity. They do **not** establish concurrency. Retain the structural partial order and uncertainty instead of forcing either a sequential or concurrent execution story.

The incomplete 100k sample has 22 matched child starts earlier than parent starts (minimum gap −1 ms). Preserve these observations with quality flags; they do not justify declaring causality backwards or silently clamping gaps to zero.

## 5. What the original plan assumed, and what changes

| Assumption or proposal | Audit finding | Required treatment |
|---|---|---|
| Telemetry not yet extracted | Data now exist locally | Remove stale archive blocker; validate remaining files separately |
| Seventy cases may be independent | Seventy rows occupy 57 windows | Group before split; establish incident equivalence before unioning gold |
| A CSV prefix approximates a complete trace/time slice | Example spans scatter across 1.2M records | Whole-file filter/index, composite-key closure, explicit retrieval scope |
| Timestamp and duration may share units | Millisecond timestamps; strong microsecond duration evidence | Separate raw fields and conversion provenance |
| Every parent link describes a service dependency | 19/36 links stay on the same component | Retain span graph; derive and deduplicate interaction graph explicitly |
| Type identifies client/server or complete protocol semantics | Caller and receiver both rpc; http has mixed status encodings | Infer roles cautiously from several fields; preserve unknowns |
| Nonzero status means error | Eight mixed status strings | Disable error ratios until producer-specific mapping is established |
| Blank type / zero duration is invalid data | Both occur in the selected trace and broader sample | Preserve with quality metadata; do not coerce to missing/failure |
| Start gap measures network latency | Gaps include local work, scheduling and clock effects | Name feature observed start gap; avoid network-cause claims |
| Apparent overlapping intervals prove concurrency | All four example overlaps are sub-millisecond | Respect measurement resolution; retain uncertain ordering |
| Five calls/min and 20 reference bins guarantee usable p95 features | Prefix coverage is structurally biased and incomplete | Audit full-window support by operation/type/role before freezing eligibility |
| Positive MAD is a harmless filter | Constant baselines cannot pass it; database sample p95 is zero | Record constant baseline separately; define any fallback before holdout, identically in S2/N2 |
| A complete-looking trace identifies a fault | This trace is outside declared incident windows and has no gold diagnosis | Use as shape/semantics evidence only |

The experiment [plan](../../specs/001-candidate-recall-experiment/plan.md), [data model](../../specs/001-candidate-recall-experiment/data-model.md), research decisions, specification assumptions, CLI contract and validation guide have been amended accordingly. The equal-weight fusion/ranking experiment has not been executed or validated by this audit.

## 6. What is still unknown

- Producer-authoritative duration units and status mappings across every instrumentation type and day.
- Whether zero duration means rounding, truncation, absent measurement, or actual sub-resolution work in each producer.
- Full-day composite-key uniqueness, orphan rates, cycle rates and instrumentation completeness beyond the selected trace.
- Actual cross-component clock offsets; whether start/end values can support finer causal ordering.
- Whole-window feature support and constant-baseline policies; the proposed p95 thresholds are not validated yet.
- Root-cause accuracy: no labels, service obligation violations, failure cause, or candidate recall were tested here.

The data support reconstructing and describing observed work. They do not, by themselves, establish that an observed span or component failed to meet a service obligation.

## Verification performed

The primary agent reran all three retained diagnostic scripts on the extracted 37-span fixture under Python 3.14.3, checked strict JSON outputs, and asserted 36 resolved relations, 19 same-emitter/17 cross-emitter relations, four zero durations, and exact last-nonroot endpoint +93,228 microseconds. Full-day type/status totals reconcile to 9,132,857 and the zero-duration cross-tab reconciles to 673,248. The full-day scans were performed by the subagents; this fixture rerun checks the retained scripts after review corrections without implying another independent whole-day graph audit.

Explicit review corrections: a subagent's prose timezone conversion was contradicted by executable `datetime.fromtimestamp` and was not adopted; a root-inclusive maximum endpoint was not used as independent duration evidence. All source facts and limitations above reflect the checked versions.
