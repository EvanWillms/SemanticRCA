# Resource relationships outside the recorded trace graph

Inspected 2026-09-17. These are observed schema and example relationships, not a complete topology extraction or a diagnosis of Redis.

The resulting decision is [ADR 0005](../adr/0005-evidence-backed-resource-relationships.md), with requirements in [feature 003](../../specs/003-contextual-telemetry-evidence/spec.md) and its [relationship contract](../../specs/003-contextual-telemetry-evidence/contracts/resource-relationships.md).

## What the trace export carries

The trace CSV has nine columns: `timestamp`, `cmdb_id`, `span_id`, `trace_id`, `duration`, `type`, `status_code`, `operation_name`, and `parent_span`. It supports explicit recorded ancestry through `(trace_id, parent_span)` → `(trace_id, span_id)`. A receiver span's recording component can identify the downstream replica. A client operation name alone may identify a logical operation without identifying its physical target.

The export has no dedicated peer-address, database-instance, resource-target, or span-link column. `cmdb_id` identifies the recording component; it must not automatically be interpreted as the called resource. A database span can therefore describe an external operation while leaving its target unresolved.

## Concrete example: cartservice and Redis

In the previously inspected checkout request, trace `328e653dddef2f29d419a46895d85d12` contains:

```text
cmdb_id:       cartservice-0
operation_name: HGET
type:           db
span_id:        82699ec29b9d8e4c
parent_span:    7a432b5aeaf47a4e
timestamp:     1647788971415
```

Source: [March 20 traces](../../data/track-1/telemetry/2022_03_20/trace/trace_span.csv), record 7,578,097. This is an operation recorded by cartservice-0 at 23:09:31.415 UTC+8; its row does not name a Redis instance.

Other channels supply related-resource evidence:

| Source | Actual identity or value | Supported relationship |
|---|---|---|
| Mesh metric, timestamp 1647788940 | `cartservice-0.source.cartservice.redis-cart` | cartservice-0 records the source side of cartservice→redis-cart traffic |
| Mesh metric, same timestamp | `redis-cart-0.destination.cartservice.redis-cart` | redis-cart-0 records the destination side of that service relationship |
| Container metric, same timestamp | `node-6.redis-cart-0` | Redis pod redis-cart-0 is associated with node-6 at this observed time |
| Redis proxy log, timestamp 1647757435 | Component `redis-cart-0`; endpoint `172.20.3.27:6379`; cluster text `outbound_.6379_._.redis-cart.ts.svc.cluster.local` | Endpoint/service evidence for a Redis connection at that log's time |
| Service log | `cmdb_id=redis-cart-0`, `log_name=log_redis-cart-service_application` | Application logs attributable to the Redis resource |

The mesh samples are at 23:09:00 UTC+8 and have KPI `istio_tcp_sent_bytes.-`. Physical CSV lines are 22,571 for cartservice-0 and 23,291 for redis-cart-0 in [mesh metrics](../../data/track-1/telemetry/2022_03_20/metric/metric_mesh.csv). The container identity is visible at line 20,771 in [container metrics](../../data/track-1/telemetry/2022_03_20/metric/metric_container.csv). The proxy example is logical record 774,658 in [proxy logs](../../data/track-1/telemetry/2022_03_20/log/log_proxy.csv), decoded with a CSV reader; it is an earlier example, not an endpoint mapping verified at the checkout request's time.

Together these records justify expanding the investigation from cartservice to the Redis service, Redis pod telemetry, and its host. They do not prove which Redis connection or backend invocation served this individual HGET. A service-level traffic measurement and a connection log are not per-operation trace joins.

## Joining policy

Keep relationship types separate:

1. **Recorded span ancestry:** exact IDs inside a trace.
2. **Observed service dependency:** source/destination names in mesh telemetry or endpoint evidence in proxy logs.
3. **Resource placement/identity:** pod/node names in container telemetry, plus independently supported aliases.
4. **Temporal association:** telemetry for related entities near an event, with clock units and aggregation resolution retained.

The metric schema has no trace ID, and the log schema has no dedicated trace/span ID columns. Payloads can contain request identifiers or endpoints, but their relationship to trace IDs must be verified before joining. Timestamp proximity alone does not create an exact request-level link. Persistent connections may carry multiple operations. Observed identity mappings must retain their time support; IP addresses and placement must not be assumed permanent.

Missing receiver spans can also reflect incomplete retrieval or instrumentation. Search the full available trace before declaring a resource outside it. Even a fully resolved recorded trace does not prove that all external calls were instrumented.

The supplied telemetry inventory and manifest do not provide a separate complete resource-topology table. The evidence must be assembled from these channels, retaining unresolved targets. In particular, `redis-cart` and `redis-cart2` must not be collapsed by stripping digits from names.

## Index implication

Time and trace-ID indexes accelerate raw retrieval. Supporting related-resource exploration additionally requires a derived relationship lookup that preserves:

```text
source entity → relationship type → target entity
observed time/window + evidence source/record + mapping rule + uncertainty
```

This is a proposed derived view, not an existing universal foreign-key relation in the CSVs. It should enable expansion to related resource telemetry while keeping exact trace edges distinct from service-level dependencies, placement, and temporal corroboration.
