# One pre-labelled Track 1 failure: case 25

Extracted 2026-09-17. This is an inspected **development example**, not a held-out result. The recorded answer is taken directly from the organizer's development labels; the telemetry observations below are separate from that answer.

## Recorded case and answer

| Field | Value |
|---|---|
| Row / task | `25` / `task_7` (time, component, reason) |
| System | `cloudbed-1` |
| Supplied window | 2022-03-20 23:00–23:30, UTC+8 |
| Number of failures | One |
| Labelled fault onset | **2022-03-20 23:09:26, UTC+8** |
| Labelled root component | **`checkoutservice-2`** |
| Labelled root reason | **`container memory load`** |
| Time-scoring tolerance | ±60 seconds |

Source: [organizer development queries](../../../data/track-1/dev/query_dev.csv), selected by `row_id == 25` using a CSV reader. This was the first `task_7` row encountered; no fault class was selected for a favorable result.

The exact instruction:

> The cloud service system, cloudbed-1, experienced a failure within the time range of March 20, 2022, from 23:00 to 23:30. The exact time of the root cause occurrence, the affected component, and the underlying reason for this failure are currently unknown. Please identify the root cause occurrence datetime, the root cause component, and the root cause reason.

The source stores these scoring statements separated by literal backslash-n sequences; rendered here as separate lines:

```text
The only root cause occurrence time is within 1 minutes (i.e., <=1min) of 2022-03-20 23:09:26
The only predicted root cause component is checkoutservice-2
The only predicted root cause reason is container memory load
```

## Metric observations

The metric component is `node-5.checkoutservice-2`: pod `checkoutservice-2` on node-5. For KPI `container_memory_usage_MB`, the actual samples are:

| Time, UTC+8 | Value in the KPI's MB units | Source CSV record |
|---|---:|---:|
| 23:05:00 | 33.894531 | 1927800 |
| 23:06:00 | 33.894531 | 1927801 |
| 23:07:00 | 33.894531 | 1927802 |
| 23:08:00 | 33.894531 | 1927803 |
| 23:09:00 | 63.455078 | 1927804 |
| 23:10:00 | 99.640625 | 1927805 |
| 23:11:00 | 104.007812 | 1927806 |
| 23:12:00 | 103.888021 | 1927807 |
| 23:13:00 | 49.201172 | 1927808 |
| 23:14:00 | 56.050781 | 1927809 |

Source: [March 20 container metrics](../../../data/track-1/telemetry/2022_03_20/metric/metric_container.csv). Record numbers include the header as record 1. The source was scanned with a CSV reader and filtered by exact pod suffix, memory KPI and the interval five minutes before through five minutes after the labelled onset.

The before/after intervals are `[23:04:26, 23:09:26)` and `[23:09:26, 23:14:26)`, five observed minute samples in each. Median memory usage rises from **33.89453125 to 99.640625**, and median working set from **28.0625 to 87.77734375**. The observed `container_spec_memory_limit_MB` stays 128; `container_memory_failcnt` stays zero across these ten samples.

The 23:09:00 sample already shows increased usage, 26 seconds before the labelled onset. We therefore cannot describe 23:09:26 as an exact change point established by these samples. Metric aggregation timestamp semantics and label precision require separate treatment. The increase is consistent with the supplied memory-load label; these observations alone do not establish an out-of-memory event, process crash, or customer-visible outage.

## One associated request trace

Trace ID: **`328e653dddef2f29d419a46895d85d12`**.

Selection rule: after scanning the full day's trace file, select the earliest `checkoutservice-2` `PlaceOrder` span starting at or after the labelled fault onset within the supplied query window. The window contains 94,912 spans; 26 match that component/operation/post-onset selection. This selection explicitly uses gold and is only for illustration.

The selected span starts **23:09:31.332 UTC+8**, 5.332 seconds after the label. Its raw record is:

```json
{
  "timestamp": "1647788971332",
  "cmdb_id": "checkoutservice-2",
  "span_id": "6b68c1e69127a30d",
  "trace_id": "328e653dddef2f29d419a46895d85d12",
  "duration": "384198",
  "type": "rpc",
  "status_code": "0",
  "operation_name": "hipstershop.CheckoutService/PlaceOrder",
  "parent_span": "1f5b3af5678bf1ca"
}
```

Source: [March 20 trace spans](../../../data/track-1/telemetry/2022_03_20/trace/trace_span.csv), logical record **2,998,687**. Full-file extraction recovers **37 spans, 13 recording components and 36 resolved parent links**, with no duplicate composite IDs or orphan parents in this recorded trace.

```text
frontend-2: Frontend/Recv.                 23:09:31.331  raw duration 428249
└── frontend-2: CheckoutService/PlaceOrder 23:09:31.331  raw duration 386142
    └── checkoutservice-2: PlaceOrder     23:09:31.332  raw duration 384198
        └── downstream calls, including cart, product, shipping, payment and email
```

Using the trace audit's provisional microsecond duration interpretation, the checkout receiver span lasts **384.198 ms**, its frontend caller span **386.142 ms**, and the frontend root **428.249 ms**. At initial extraction these were individual observations without a before/after comparison. The follow-up comparison below adds context, but the small sample does not establish a statistically significant slowdown or a breached service obligation. Their raw status is `0`; the trace also contains `200` and `Ok`. There is no explicit memory-failure verdict embedded in this request trace.

The full extract and machine-readable selection/metric evidence are under `/private/tmp/symbolicrca-labeled-example/`. To re-extract the trace from the repository root:

```bash
python3 docs/research/trace-audit/audit_trace.py data/track-1/telemetry/2022_03_20/trace/trace_span.csv 328e653dddef2f29d419a46895d85d12 /private/tmp/symbolicrca-case-25-trace
```

## Interpretation boundary

The benchmark explicitly labels this incident as **container memory load on checkoutservice-2**. We observe elevated memory measurements and a request passing through that component shortly afterward. Establishing the correct diagnosis without knowing the label would require comparing alternative components, behavior before/after the event, and other telemetry. This example does not perform that blind test.

The inspected window and any overlapping/duplicate incident variants must remain on the development side of future splits. Other labels exposed during example selection (rows 0–2) are recorded in the experiment's development-exposure manifest as well.

## Follow-up: what service problem is actually visible?

The label itself does not name a failed business operation, affected endpoint/SLO, or required outcome that was violated. Memory load is the labelled resource disturbance. To look for an effect, we compared the same five-minute intervals used above and the same `PlaceOrder` receiver operation on `checkoutservice-2`, then joined those trace IDs to their recorded frontend root spans.

| Observation | Five minutes before labelled onset | Five minutes after labelled onset |
|---|---:|---:|
| Matching checkout receiver spans | 6 | 7 |
| Checkout receiver median duration, ms* | 46.858 | 48.846 |
| Checkout receiver maximum duration, ms* | 65.195 | 384.198 |
| Associated frontend root median duration, ms* | 91.288 | 94.789 |
| Associated frontend root maximum duration, ms* | 110.190 | 428.249 |
| Checkout and frontend `sr` field, all observed service samples | 100 | 100 |
| Container `container_memory_failcnt`, all observed samples | 0 | 0 |

*Duration conversion retains the provisional microsecond interpretation. Six/seven traces are a small sample and the intervals were chosen using the label. The roots all resolved in the source window. All matched checkout/root raw statuses were `0`; this is reported without imposing a global status interpretation.

The seven post-onset checkout durations are 384.198, 94.035, 48.846, 48.177, 46.685, 65.039 and 42.690 ms in chronological order. The trace originally selected as an example is the largest duration in that post-onset group. It supports a brief latency-spike observation, not a claim that all requests were persistently slow. The other checkout replicas' median receiver durations are 47.603→54.242 ms (`checkoutservice-0`), 64.401→48.367 ms (`checkoutservice-1`), and 46.017→45.993 ms (`checkoutservice2-0`). These are descriptive comparisons, not a causal control experiment.

For each of `checkoutservice-grpc` and `frontend-http`, the service metric file has five samples per comparison period; `rr` and `sr` remain 100 throughout. The median of the per-minute `mrt` values changes 56.429→59.667 for checkout and 50.049→51.836 for frontend, with a checkout maximum of 144.167 after onset. These are source-field values; do not infer an SLA breach from them. The local guide does not define their aggregation window or units, so trace-derived durations above are the clearer timing comparison. No application error logs or SLO contract were audited in this follow-up.

Evidence location: `/private/tmp/symbolicrca-case25-impact/inspect.py`, `service.json`, and `traces.json`. The trace scan covers the entire source file before filtering to the supplied incident window, so this is not a file-prefix sample.

### Benchmark construction explains the distinction

The original OpenRCA paper, Appendix A.5, describes label validation primarily through anomalies in the named root component's resource-related KPIs. It says business metrics/logs/traces are used when those KPIs do not show clear anomalies, and that telemetry for non-root components is not verified during calibration. This procedure establishes recoverability of the labelled root-cause elements; it does not state a mandatory customer-impact or SLO-breach criterion for every retained record. [OpenRCA paper, Appendix A.5](https://netman.aiops.org/wp-content/uploads/2025/05/13411_OpenRCA_Can_Large_Langua.pdf#page=17)

For this case, the supported description is **a labelled memory-load fault with elevated memory use and a brief observed checkout latency spike**. Checkout unavailability, failed orders, an out-of-memory kill, an SLO violation, and the mechanism causing the slow request remain unestablished. The RCA benchmark scores recovery of the recorded time/component/reason; it does not score whether those additional impact claims have been proved.

## Follow-up: request-level causal link

The [trace causality analysis](track-1-case-25-trace-causality.md) follows exact span ancestry from the frontend into checkoutservice-2 and compares all 13 matching requests around the onset. In the selected slow request, 337.005 ms of the 337.220 ms frontend increase is inside its checkout call. The analysis locates three long outgoing RPC intervals and an 82.572 ms same-component gap, while distinguishing observed latency propagation from the unproved memory-related mechanism.
