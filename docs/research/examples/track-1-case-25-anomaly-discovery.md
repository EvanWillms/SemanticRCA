# Case 25: finding the slow request before selecting checkoutservice-2

## Result

A frontend-first latency scan ranks trace **328e653dddef2f29d419a46895d85d12** first among **2,729 frontend root spans** in the prompt's March 20, 2022, 23:00–23:30 UTC+8 window. Its duration is **428.249 ms**, versus a **93.9525 ms median** for 102 preceding requests with the same recorded downstream-operation counts. Following this request's parent links then identifies the 386.142 ms checkout call and its receiver on checkoutservice-2.

The fault component, fault reason, and labelled onset are not used in the ranking calculation. This remains a retrospective development demonstration: the analyst already knows the example, and the detector has not been validated on held-out incidents.

## Procedure actually run

1. Scan the entire unsorted March 20 trace CSV. Retain frontend spans whose starts fall in 22:29–23:31, providing a one-minute margin around the comparison and query windows. Select blank-parent frontend roots in 22:30–23:30. All 2,729 query-window roots have operation `hipstershop.Frontend/Recv.`.
2. Join each root to its recorded direct children by `(trace_id, parent_span)` matching `(trace_id, span_id)`. Group requests by the multiset of their direct-child operation names, including counts, across frontend replicas. This is a proxy for request type, not a verified HTTP route or identical workload.
3. Use roots starting in 22:30–23:00 as the reference. There are 2,568 reference roots and nine distinct operation-count signatures across reference and query. A group is eligible only with at least 20 reference observations, positive median, and positive median absolute deviation (MAD). All query roots are eligible here.
4. Rank each query root by `(duration − reference median) / (1.4826 × reference MAD)`. This robust standardized departure is a prioritization score, not a failure probability or calibrated statistical significance. No alarm threshold was fitted or used to select the top request.
5. Only after ranking, look up the previously inspected trace ID and inspect the top request's child spans.

## What made the selected request stand out

| Quantity | Observation |
|---|---:|
| Query root timestamp | 23:09:31.331 UTC+8 |
| Query root duration | 428.249 ms |
| Matching reference requests | 102 |
| Reference median duration | 93.9525 ms |
| Reference MAD | 6.6125 ms |
| Duration / reference median | 4.558× |
| Excess over reference median | 334.2965 ms |
| Robust departure score | 34.099 |
| Rank among query roots by that score | 1 / 2,729 |
| Rank by absolute root duration | 1 / 2,729 |
| Rank by excess over cohort median | 1 / 2,729 |

The matching signature is one CheckoutService/PlaceOrder, one CurrencyService/GetSupportedCurrencies, five ProductCatalogService/GetProduct, and one RecommendationService/ListRecommendations. Checkout was not a selection filter: signatures for all frontend requests were considered.

The top request's checkout client span occupies 386.142 ms, about 90.17% of the frontend duration. Its span ID is `1f5b3af5678bf1ca`, with parent `d520fc2d7fae1ee0`. The receiver span `6b68c1e69127a30d` identifies the serving component as `checkoutservice-2`. The [trace causality analysis](track-1-case-25-trace-causality.md) then explains the duration increase and gaps inside that invocation.

This gives a concrete investigation sequence: **unusually slow frontend request → expensive checkout dependency → checkoutservice-2 → inspect its local behavior and correlated resource signals to test the cause.** The frontend request timestamp identifies a symptom occurrence, not automatically the fault's initiating time.

## Limits exposed by this scan

- The preceding interval is not certified healthy and is itself an incident window in the supplied prompts. Its matching cohort includes a **6,746.740 ms maximum**. Thus the selected request is unusual relative to typical reference behavior, but not unprecedented in that reference. Median/MAD reduces sensitivity to a few large values; it does not establish a valid healthy reference or calibrated false-positive rate.
- The second-ranked request lasts only **0.929 ms**, versus its cohort median of 0.181 ms. A high relative-departure score can describe a tiny absolute delay. A deployment policy would need to consider absolute excess, recurrence, impact and corroboration; no universal severity threshold is established here.
- Grouping by observed child operations can mix workloads and can separate a failed request from its normal cohort if the fault changes which calls occur. A durable detector should use route/workload metadata where available and handle changed or incomplete call patterns explicitly. Empty child signatures are retained here, not assumed fully instrumented.
- The one-minute extraction margin is a bounded collection rule. It does not guarantee complete children for arbitrarily long traces; selected candidates need full-trace retrieval. The selected trace has already been recovered from the full file and audited separately.
- Latency is one discovery channel. Other incidents may chiefly exhibit resource, error, throughput, missing-request or log changes. A frontend-latency search alone does not cover the full benchmark.
- Duration conversion retains the provisional microsecond interpretation from the trace audit. Ratios and standardized rankings are invariant to a consistent duration-unit conversion.

## Reproduce

From the repository root:

```bash
python3 docs/research/trace-audit/discover_case25_latency.py \
  data/track-1/telemetry/2022_03_20/trace/trace_span.csv \
  /private/tmp/symbolicrca-case25-discovery-reproduction
```

The script writes `analysis.json` with all ranked query roots, their child spans, reference statistics, and source records. Initial run output is `/private/tmp/symbolicrca-case25-discovery/analysis.json`. Source records for the selected frontend root and checkout client span are 4,524,855 and 6,049,664 respectively, counting the header as record 1.
