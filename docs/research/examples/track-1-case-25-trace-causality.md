# Case 25: tracing frontend latency back to checkoutservice-2

This development analysis finds a recorded request dependency and a latency propagation path from the frontend of `cloudbed-1` into `checkoutservice-2`. It localizes the slow request to the checkout invocation and identifies suspicious gaps around checkout's outgoing work. The trace does not identify the memory-related mechanism that produced those gaps.

`cloudbed-1` is the system named in the incident query. The request boundary examined here is its recorded `Frontend/Recv.` span; there is no additional system-wide `cloudbed-1` span in this request.

## The explicit dependency

At **2022-03-20 23:09:31.331 UTC+8**, trace **`328e653dddef2f29d419a46895d85d12`** records:

```text
frontend-2 / Frontend/Recv.                           428.249 ms
  span d520fc2d7fae1ee0
  └─ frontend-2 / CheckoutService/PlaceOrder          386.142 ms
       span 1f5b3af5678bf1ca, parent d520fc2d7fae1ee0
       └─ checkoutservice-2 / CheckoutService/PlaceOrder 384.198 ms
            span 6b68c1e69127a30d, parent 1f5b3af5678bf1ca
```

These links are exact `parent_span`→`span_id` matches inside one `trace_id`, not temporal correlations between unrelated requests. The source logical CSV records are **4,524,855**, **6,049,664**, and **2,998,687**, respectively (header counted as record 1). The checkout receiver begins at 23:09:31.332, 5.332 seconds after the labelled fault onset.

The checkout call occupies **90.17%** of the frontend request's recorded duration. Subsequent frontend calls start at about +386 ms, as checkout finishes, consistent with the frontend waiting on checkout before continuing the request.

All times below convert raw durations to milliseconds using the audit's provisional microsecond interpretation. The exact ID links and duration ratios do not depend on that unit assumption. Start timestamps have millisecond precision.

## Nearly all additional frontend time is inside checkout

We extracted all six matching checkout requests in the five minutes before the labelled onset and all seven in the five minutes after it. All 13 complete recorded traces have 37 spans each, unique span IDs within each trace, one root, resolved parents, and no parent cycles.

The closest earlier request on **the same checkout pod**, at 23:09:22.528, is trace **`958208cb1d31eae52efe9ce0770b19f6`**. Its frontend is `frontend-0`; the incident request's frontend is `frontend-2`. This is a descriptive comparison of equivalent operation sequences, not a controlled replay with identical inputs.

| Recorded interval | Closest earlier request | Selected incident request | Difference |
|---|---:|---:|---:|
| Frontend root | 91.029 ms | 428.249 ms | +337.220 ms |
| Frontend's checkout client call | 49.137 ms | 386.142 ms | +337.005 ms |
| Checkout receiver | 46.502 ms | 384.198 ms | +337.696 ms |
| Frontend root minus its checkout call | 41.892 ms | 42.107 ms | +0.215 ms |

**99.94% of the observed frontend duration increase is accounted for by the longer checkout client interval.** This is elapsed-time accounting for these two traces, not an estimate of a fault's causal effect across the population. The frontend-to-checkout duration difference is small in both requests: 2.635 ms before and 1.944 ms in the slow request.

The comparison is not dependent on one unusually fast baseline: across all six earlier requests, checkout receiver duration ranges from 43.830 to 65.195 ms and frontend duration from 86.034 to 110.190 ms. The incident checkout receiver lasts 384.198 ms. The other six post-onset checkout receiver durations are 94.035, 48.846, 48.177, 46.685, 65.039, and 42.690 ms. This is a spike, not uniformly persistent slow service.

## Where the extra time appears inside checkout

Each outgoing client span below is recorded by **checkoutservice-2**. The downstream receiver is joined using the explicit parent link.

| Checkout outgoing operation | Earlier client duration | Incident client duration | Incident downstream receiver | Recorded gap from client start to receiver start |
|---|---:|---:|---|---:|
| Cart/GetCart | 4.354 ms | **84.786 ms** | cartservice-0: raw duration 0 | **83 ms** |
| Payment/Charge | 3.108 ms | **93.441 ms** | paymentservice-2: 0.164 ms | **92 ms** |
| Email/SendOrderConfirmation | 4.026 ms | **92.591 ms** | emailservice-2: 0.257 ms | **91 ms** |

The earlier client-to-receiver start gaps are 3, 2, and 3 ms respectively. Across all six earlier requests, these client durations range from 4.069–4.927 ms for Cart, 3.041–3.702 ms for Payment, and 3.912–21.959 ms for Email. Thus there is some pre-existing variability, especially for Email, but the incident's delays are substantially larger.

There is also a large **same-component gap** between checkout's second Product/GetProduct client span and its Shipping/GetQuote client span:

- Product call starts at frontend-relative +97 ms and lasts 6.428 ms, ending at +103.428 ms.
- Shipping call starts at +186 ms.
- The interval between them is **82.572 ms**, versus **3.141 ms** in the closest earlier request.

Both timestamps come from spans recorded by checkoutservice-2, so this particular gap does not require comparing clocks on different components. It is time inside checkout's receiver span with no recorded direct child covering it; it could include scheduling, runtime pauses, application work, or uninstrumented work. It is not a measurement of CPU execution.

Overall, checkout time uncovered by the union of its recorded direct-child intervals increases from **11.402 to 89.111 ms**. Child intervals are clipped to the checkout receiver and unioned rather than blindly summed, because millisecond start timestamps can create small apparent overlaps. The increase in covered time is 259.987 ms and the increase in uncovered time is 77.709 ms, summing to the receiver increase of 337.696 ms.

These observations support a delay around checkout's execution and outgoing RPC handling. The measured downstream handlers do not account for the long client intervals. Cross-component start gaps remain subject to clock offsets, transport, scheduling, and instrumentation boundaries; a zero-duration Cart span is not proof that Cart performed no work. The trace cannot isolate caller delay from all those alternatives.

### Exact source references for the suspicious intervals

All records are in [the March 20 trace CSV](../../../data/track-1/telemetry/2022_03_20/trace/trace_span.csv), in the selected incident trace:

| Span | Span ID | Parent span ID | Source record |
|---|---|---|---:|
| Checkout Cart client | d918e82b2db86440 | 6b68c1e69127a30d | 6,049,658 |
| Cart receiver | 7a432b5aeaf47a4e | d918e82b2db86440 | 9,102,887 |
| Checkout second Product client | 3a5e0ab5a1717734 | 6b68c1e69127a30d | 4,524,839 |
| Checkout Shipping/GetQuote client | e59fea6ecc4f3286 | 6b68c1e69127a30d | 7,578,007 |
| Checkout Payment client | 399990cc15604e26 | 6b68c1e69127a30d | 6,049,661 |
| Payment receiver | 1bd6c0ca16cb51a7 | 399990cc15604e26 | 2,998,672 |
| Checkout Email client | c12e4f7cb03c65b4 | 6b68c1e69127a30d | 2,998,688 |
| Email receiver | 7703e5ae1b7d0d9d | c12e4f7cb03c65b4 | 9,102,844 |

## What causal claim is supported?

The supported request-level chain is:

```text
Delay within the checkout invocation
  → checkout's response is later
  → the dependent frontend request finishes later
```

The benchmark's proposed initiating chain is:

```text
Container memory load on checkoutservice-2 [organizer label; elevated memory observed]
  → runtime/scheduling/application delay [mechanism not identified by these spans]
  → slow checkout invocation [observed]
  → slow frontend request [observed and linked by span ancestry]
```

The linked [case report](track-1-case-25-memory-load.md) records the elevated memory measurements. They corroborate the labelled disturbance, but these traces do not distinguish garbage collection, page faults, reclaim, CPU contention caused by a memory stressor, or other runtime/scheduling causes. No memory-specific event is encoded in the spans analyzed here. We also have not established a failed order, outage, or breach of a declared latency requirement.

The trace evidence therefore supports **frontend latency propagation through checkoutservice-2**, with multiple gaps around that component's work. The separate claim that **container memory load caused those gaps** requires the organizer label and additional mechanism evidence; it is not independently proved by this trace.

## Reproduction and scope

Run from the repository root:

```bash
python3 docs/research/trace-audit/analyze_case25_causality.py \
  data/track-1/telemetry/2022_03_20/trace/trace_span.csv \
  /private/tmp/symbolicrca-case25-causal-reproduction
```

The script first scans the complete source to select checkoutservice-2 PlaceOrder receiver spans starting in `[23:04:26, 23:14:26)` UTC+8, then scans the complete source again to recover every row with those trace IDs. The source is not chronologically sorted, so the script never stops at a timestamp cutoff. It writes `extracted_traces.json` and `analysis.json`, retaining source-record references. The source SHA-256 is `42057b3325dc32bda37fc98feaf07a9edb48bcf394f5b511e18b38f23670f550`, recorded in the earlier audit.

This analysis uses the known case-25 onset and component to select and explain evidence. It is a development investigation, not a blind recovery of the root cause or a held-out benchmark score. Parent completeness means completeness of the recorded links, not completeness of instrumentation.

## Follow-up: discovering the request from the prompt window

A [frontend-first discovery scan](track-1-case-25-anomaly-discovery.md) subsequently ranked all 2,729 frontend requests in the prompt window against preceding requests with matching operation-count signatures. The selected trace ranked first without using the fault component or onset in the score. This is a retrospective development demonstration, with explicit reference-contamination and severity limitations, rather than held-out detector validation.
