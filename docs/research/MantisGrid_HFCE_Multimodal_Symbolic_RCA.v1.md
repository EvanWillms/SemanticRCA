---
title: "HFCE Export — Multimodal Symbolic Evidence for Efficient, Explainable Infrastructure RCA"
version: "v1"
date: "2026-09-17"
mode: "high-fidelity-context-export"
root_thesis: "A multimodal symbolic evidence layer for efficient, explainable infrastructure RCA."
primary_track: "MantisGrid AI Hackathon 2026 — Track 1 Infrastructure Root Cause Analysis"
status: "hackathon hypothesis + research-program seed"
evidence_boundary: "Conversation context, user-supplied research summaries, MantisGrid official hackathon repository, MantisGrid public materials discussed in-session, and cited research lineage through 2026-09-17."
---

# ROOT

- **ROOT THESIS — Hackathon claim:** Build a **multimodal symbolic evidence layer for efficient, explainable infrastructure RCA**.
  - **CLAIM:** Continuous metrics, logs, and distributed traces can be transformed into compact, interpretable symbolic behavior streams that help an RCA agent distinguish the **causal component and fault onset** from downstream symptoms.
    - **MECHANISM:** Preserve separate symbolic channels for resource behavior, log-event behavior, trace/dependency behavior, and topology/context; fuse their evidence rather than flattening all telemetry into one text prompt.
    - **MECHANISM:** Use temporal transitions and approximate motif matching to represent behaviors such as `NORMAL → RISE → SATURATED`, `RETRY_BURST`, or `parent→child latency-rise`, rather than sending millions of raw observations to an LLM.
    - **MECHANISM:** Use the symbolic layer as cheap triage and evidence compression; reserve stronger GLM models for ambiguous causal reasoning.
    - **MEASUREMENT:** First test whether the representation improves **gold root-cause component top-k recall** over the supplied metric-only heuristic before claiming end-to-end RCA gains.
  - **CLAIM:** The Track 1 dataset is unusually well suited to this experiment.
    - **EVIDENCE:** The official bundle is OpenRCA-derived production telemetry from a microservice online shop, with metrics, logs, and traces, 70 development cases, known answers, and evaluation on another deployment of the same system.
    - **EVIDENCE:** The dataset includes millions of rows per day across container, mesh, node, runtime, service, log, proxy-log, and trace-span files; it cannot fit into an LLM context window.
    - **EVIDENCE:** Network faults often barely appear in metrics and require parent/child trace latency, creating a direct test of whether multimodal fusion outperforms metric-only anomaly ranking.
    - **EVIDENCE:** The true fault time commonly falls between samples, making **behavioral onset detection** more appropriate than exact-point matching.
    - **EVIDENCE:** Judging values evidence/explainability, evaluation quality, cost efficiency, and accuracy; a compact evidence layer can potentially improve all four.
  - **CLAIM:** The hackathon project should test the representation, not prematurely claim the broader Reliability Ecologist thesis.
    - **BOUNDARY:** Track 1 faults are primarily injected CPU, memory, network, disk, process, and I/O failures. The supplied material does not establish that it contains autonomous controller-action populations, failover cascades, or control-loop oscillations.
    - **BOUNDARY:** Therefore the hackathon should establish **multisensor symbolic fusion → behavioral episode → causal localization**.
    - **EXTENSION:** The broader research program can later extend the same machinery from **fault activity** to **controller/population activity** such as failover stampedes, recolonization cycles, and coupled-controller oscillation.

# EXECUTIVE APEX

## Final working position

The project should be framed as a **representation and evidence-selection innovation**, not as another generic LLM RCA agent and not as “SAX for cloud telemetry.”

The starter baseline already exposes the exact failure mode to attack: it robust-z-scores KPI series, chooses the loudest anomalous component, ignores logs and traces, has no causal model, and often selects a symptom rather than the root cause. Its mean score is 0.073 and it fully solves only 2 of 70 development cases.

The project hypothesis is that a small, interpretable symbolic layer can perform three jobs before expensive LLM reasoning:

1. **Detect meaningful temporal transitions** in each modality.
2. **Rank candidate root-cause components** using cross-modal agreement and causal ordering.
3. **Compress supporting evidence** into a small, inspectable episode passed to the model.

The first Lean Startup test is not official benchmark accuracy. It is:

> **Does symbolic multimodal fusion put the true root-cause component in the top 3 candidates more often than the supplied metric-only heuristic?**

If that does not move, stop. If it does, test whether traces particularly improve network-fault recall, then measure token/cost savings and end-to-end OpenRCA scoring.

## Why this is differentiated from MantisGrid itself

MantisGrid already publicly positions its platform around multimodal telemetry, dependency-aware correlation, a real-time reliability graph, root-cause identification, Findings, prediction, and governed remediation. The project must not present those capabilities back to MantisGrid as novelty.

The differentiated layer is:

> **Represent continuous multimodal infrastructure evidence as reusable, topology-normalized behavior episodes that can be matched, fused, explained, and used to select what an RCA model should inspect next.**

For the hackathon, this is a narrower and more defensible claim than the full Reliability Ecologist concept.

For the longer research program, the differentiated object becomes **reliability activity**: a temporally extended system behavior rather than an individual fault.

# MECE TAKEAWAYS MAP

## D1 — Choose Track 1 as the experimental substrate

- **DECISION:** Apply the symbolic-fusion method to Track 1.
  - **RATIONALE:** Track 1 directly requires time, component, cause, and evidence from a large multimodal telemetry corpus.
  - **RATIONALE:** The organizer explicitly says the telemetry does not fit in context and must be queried.
  - **RATIONALE:** The baseline ignores roughly half of the available signal by never opening logs or traces.
  - **RATIONALE:** The evaluation deployment changes component identities while retaining the same software and failure types, creating a useful test of structural/generalized behavior representation.
  - **BOUNDARY:** Track 2 remains a better substrate for CFO-oriented population-efficiency analysis, but it is less reproducible due to its CC BY-NC-ND source data and does not test root-cause localization as directly.

## D2 — Treat symbolic representation as triage, not the final reasoner

- **DECISION:** The symbolic layer should produce ranked candidates and compact evidence; the LLM should resolve ambiguous causal cases.
  - **MECHANISM:** Numeric telemetry → symbolic state transitions.
  - **MECHANISM:** Logs → normalized event classes / frequency transitions.
  - **MECHANISM:** Traces → parent-child latency/status behavior and path-level transitions.
  - **MECHANISM:** Topology → structural context inferred from component names and span relationships.
  - **MECHANISM:** Fusion → evidence agreement/disagreement across channels.
  - **OUTCOME:** Small evidence packets for a strong reasoning model.
  - **OUTCOME:** Cheap or deterministic handling of easy cases; expensive reasoning only where needed.

## D3 — Validate candidate recall before end-to-end RCA

- **DECISION:** Use an early go/no-go metric that isolates the representation layer.
  - **PRIMARY METRIC:** Gold-component top-1 and top-3 recall.
  - **SECONDARY METRIC:** Reason-family recall.
  - **SECONDARY METRIC:** Fault-onset error.
  - **SECONDARY METRIC:** Evidence size / tokens passed downstream.
  - **SECONDARY METRIC:** Wall-clock and dollars per case.
  - **RATIONALE:** If the true cause never reaches the model’s candidate set, stronger LLM reasoning cannot recover it reliably.
  - **STOP CONDITION:** If symbolic fusion cannot beat the baseline candidate ranking on held-out development cases, do not spend the day polishing the LLM agent.

## D4 — Preserve multimodal channels instead of flattening telemetry

- **DECISION:** Maintain distinct streams.
  - **METRIC CHANNEL:** `NORMAL`, `RISE`, `SPIKE`, `SUSTAINED_HIGH`, `DROP`, `OSCILLATE`, `RECOVER`, `MISSING`.
  - **TRACE CHANNEL:** parent→child relation, latency transition, span-status transition, causal path.
  - **LOG CHANNEL:** normalized event class and burst/transition features.
  - **TOPOLOGY CHANNEL:** node/pod/service roles and source/destination dependencies.
  - **FUSION:** late fusion of per-channel match/evidence scores.
  - **RATIONALE:** The activity-recognition lineage shows value in keeping sensors separate until recognition/fusion; combining everything into one alphabet destroys source-specific semantics.
  - **RATIONALE:** Missing-channel behavior becomes measurable and explainable.

## D5 — Use behavioral onset, not sample peaks, for time localization

- **DECISION:** Fault time should be inferred as the earliest credible transition in the causal component, not the maximum anomaly point.
  - **EVIDENCE:** Official data guidance says there is usually no data point exactly at the fault time.
  - **EVIDENCE:** The starter baseline currently uses the peak of one metric series, which the organizers identify as a weakness.
  - **MECHANISM:** Estimate onset from transition boundaries such as baseline→rise, latency-change point, error-burst onset, or first persistent deviation.
  - **MEASUREMENT:** Compare estimated time against the benchmark’s ±60 second tolerance.

## D6 — Exploit the unseen-deployment test as a generalization experiment

- **DECISION:** Avoid rules tied to literal component names wherever possible.
  - **NORMALIZATION:** `shippingservice-1` → service/pod role + structural neighbors.
  - **NORMALIZATION:** node-specific names → node/pod/service layers.
  - **NORMALIZATION:** fault signatures → resource/interaction behavior.
  - **RESEARCH QUESTION:** Does topology-normalized symbolic behavior transfer better to unseen component identities than literal anomaly heuristics?
  - **HACKATHON VALUE:** The organizer’s hidden evaluation deployment creates a natural stress test for overfitting.

# FOUNDATIONS

## F1 — Story hook: the disposable-server shift

- **EXPERIENCE:** In 2008, the user watched a founder friend notice an application behaving strangely, terminate the running AWS application instance, and bring up a clean replacement connected to the core application database.
  - **OBSERVED:** The act felt dangerous under a server-as-state mental model because the server was assumed to be where the application lived.
  - **UPDATED:** The founder was already operating under the new cloud abstraction: an application instance could be disposable if durable state and deployment artifacts lived elsewhere.
  - **HISTORICAL IDENTIFICATION:** The specific AWS product was almost certainly **Amazon EC2**.
  - **DATE CAVEAT:** EC2 launched in beta in 2006 and reached full production in October 2008.
  - **DATE CAVEAT:** AWS Management Console launched in January 2009; if the event was definitely in 2008, “console” is likely retrospective shorthand or the interaction may have been through API tooling / third-party UI such as Elasticfox or RightScale.
  - **DATE CAVEAT:** EBS launched in August 2008; EBS-backed boot instances arrived later, so the safest story is “terminated an EC2 application instance and launched a fresh instance from an AMI, reconnecting to persistent application state.”

- **CLAIM:** The cloud appeared effectively infinite to early-stage application teams because replacement compute could be requested without reasoning about the physical server pool.
  - **BOUNDARY:** The physical infrastructure was never literally infinite.
  - **UPDATED FRAME:** AI workloads make the physical substrate visible again: GPU availability, memory, power, networking, placement, topology, and shared accelerators now constrain application behavior directly.
  - **BRIDGE:** We moved from a replaceable machine to populations of replaceable machines managed by populations of automated controllers.

## F2 — Reliability Ecologist

- **DEFINITION:** The Reliability Ecologist treats reliability as an emergent property of interacting controllers, workloads, and shared resource pools.
  - **SEES PROBLEM AS:** Individually sensible controllers synchronize, displace risk, and create fleet-wide instability.
  - **OPTIMIZES FOR:** Diversity, damping, containment, and system-wide stability over time.
  - **REJECTS:** The assumption that fixing each component independently necessarily improves the whole.
  - **CHARACTERISTIC MECHANISMS:** Coupling analysis, controlled heterogeneity, delayed response, comparative experiments, hysteresis, recovery intervals, and action-rate limits.
  - **FULL COMMITMENT:** Withhold a locally beneficial action if it increases correlated-failure or control-oscillation risk.

### Original Reliability Ecologist concepts

- **E01 — Self-healing stampede breaker**
  - Multiple controllers evacuate workloads toward the same apparently healthy destination and overwhelm it.
  - Proposed intervention: staggered retry windows + destination occupancy feedback.

- **E02 — Shared-fate route portfolio**
  - Nominally different endpoints may share a region, accelerator fleet, or upstream dependency.
  - Proposed intervention: optimize against dependency exposure, not endpoint count.

- **E03 — Deliberately empty firebreak**
  - Full utilization can eliminate the headroom needed to absorb displaced work.
  - Proposed intervention: preserve intentionally idle reserve capacity.

- **E04 — The do-nothing control arm**
  - Recovery after an intervention is not proof that the intervention caused recovery.
  - Proposed test: matched nonintervention comparison.

- **E05 — Fallow-node rotation**
  - Returning full load to a freshly recovered node can recreate the failure.
  - Proposed intervention: recovery interval + gradual load restoration.

- **E06 — Sentinel workload migration**
  - Passive telemetry may not exercise underused paths.
  - Proposed intervention: bounded known-answer probes across underobserved resource combinations.

- **E07 — Controllers get an action budget**
  - Autoscaler/router/scheduler actions can repeatedly undo one another.
  - Proposed intervention: shared change-rate budget and explicit action dependencies.

- **E08 — Central-controller disappearance drill**
  - The reliability layer itself can become a dependency.
  - Proposed test: remove central coordination and measure what local obligations survive.

## F3 — Closed-loop control vs population dynamics

- **CLAIM:** Closed-loop control explains how an actor responds to feedback; population dynamics explains what happens when many actors share resources and change one another’s environment.
  - **CONTROL LOOP UNIT:** sensor → controller → actuator → plant.
  - **CONTROL QUESTION:** Is feedback driving the controlled process toward a target?
  - **POPULATION UNIT:** many workloads/controllers/resources interacting over time.
  - **POPULATION QUESTION:** What collective behavior emerges from migration, competition, resource depletion, recovery, and synchronization?
  - **KEY SYNTHESIS:** Modern infrastructure is a **population of closed-loop controllers**.
    - autoscalers
    - schedulers
    - routers
    - retry policies
    - circuit breakers
    - model routers
    - Kubernetes operators
  - **MECHANISM:** One controller’s actuator becomes another controller’s disturbance.
  - **IMPORTANT PROPERTY:** Each controller can be stable in isolation while their coupled population is unstable.

### Hierarchy of dynamics

1. **Component dynamics**
   - CPU, memory, disk, GPU, network.
2. **Closed-loop dynamics**
   - autoscaler, router, scheduler, retry/failover logic.
3. **Population dynamics**
   - many workloads + many controllers + shared resources.
4. **Emergent reliability**
   - cascades, stampedes, oscillations, concentration, recovery, collapse.

## F4 — Sensor fusion and continuous activity recognition lineage

- **ORIGIN:** Stiefmeier et al. (2007), *Fusion of String-Matched Templates for Continuous Activity Recognition*.
  - Continuous upper-body motion was encoded into symbolic motion strings.
  - String-matching-based segmentation identified industrial activities from continuous motion.
  - Multiple streams were processed and recognition evidence fused.
- **EXPANSION:** Stiefmeier et al. (2008), *Wearable Activity Tracking in Car Manufacturing*, IEEE Pervasive Computing.
  - Multimodal motion / muscle / location context.
  - Continuous real-world assembly-task recognition.
  - Cross-domain information could help segmentation and classification.

### Later user-supplied symbolic time-series lineage

- **Sousa Lima et al. (2018)** — symbolic representations for inertial-sensor HAR; compared SAX/SFA with raw IMU telemetry.
- **Mezari & Maglogiannis (2018)** — SAX-based gesture recognition from smartwatch accelerometers.
- **Pappa et al. (2020)** — multichannel SAX representation (“intelligent icons”) for synchronized accelerometer/gyroscope streams.
- **Jia et al. (2018)** — symbolic important-point representation + HMM for hydraulic-pump fault diagnosis.
- **Han et al. (2020)** — symbolic sequences + multiscale Lempel-Ziv complexity for rotating machinery faults.
- **Chicco (2021)** — SAX and symbolic representations in smart-energy time-series analysis.

### Transfer to infrastructure

- **RAW PHYSICAL SENSORS:** IMU, FSR, location.
- **RAW INFRA SENSORS:** metrics, logs, traces, topology, controller events.
- **SYMBOLIZATION:** continuous values/events → compact state alphabets.
- **CONTINUOUS SPOTTING:** detect activity onset/offset without pre-cut windows.
- **FUSION:** combine partial evidence from separate channels.
- **OUTPUT:** higher-level activity whose meaning is not present in any one sensor.

### Critical methodological transfer

- Do not reduce the idea to “telemetry as text.”
- The stronger transfer is:
  - multiple noisy streams;
  - discrete symbolic observations;
  - approximate temporal matching;
  - independent per-channel evidence;
  - fused recognition;
  - tolerance to missing channels;
  - continuous segmentation;
  - cross-domain segmentation / selective evidence acquisition.

## F5 — Infrastructure activity-recognition mapping

### Component/fault-level activity

Example:

```text
METRIC
READ_IO: NORMAL → RISE → HIGH

TRACE
shipping→downstream: NORMAL → SLOW

LOG
WARN → ERROR_BURST

TOPOLOGY
pod shippingservice-1 on node-5

FUSED INTERPRETATION
shippingservice-1 / container read I/O load
```

### Population-level activity

Example — failover stampede:

```text
CONTROLLER
EVACUATE  EVACUATE  EVACUATE  EVACUATE

WORKLOAD POPULATION
A→B       A→B       A→B       A→B

DESTINATION LOAD
NORMAL    RISING    HIGH      SATURATED

SERVICE HEALTH
HEALTHY   HEALTHY   SLOW      FAILING
```

Recognized activity:

```text
SYNCHRONIZED_MIGRATION
→ DESTINATION_CONCENTRATION
→ CAPACITY_EXHAUSTION
→ SECONDARY_FAILURE
```

### Premature recolonization

```text
DEGRADE
→ EVACUATE
→ APPARENT_RECOVERY
→ RAPID_RETURN
→ RESOURCE_PRESSURE
→ REDEGRADE
```

### Coupled-controller oscillation

```text
SCALE_UP
→ ROUTE_SHIFT
→ UTILIZATION_FALL
→ SCALE_DOWN
→ ROUTE_REVERSE
→ UTILIZATION_RISE
→ REPEAT
```

## F6 — Partial order matters

- **CLAIM:** Distributed traces are not ordinary strings.
  - Concurrent child spans create a partial order.
  - Pure timestamp sorting can invent causal sequence that did not exist.
- **DECISION:** Symbolize multiple root-to-leaf paths or preserve happens-before constraints.
- **EXAMPLE:**

```text
A
├── B
│   └── D
└── C
    └── E
```

Prefer:

```text
A-B-D
A-C-E
```

over an arbitrary total order:

```text
A-B-C-D-E
```

- **RESEARCH EXTENSION:** Define motifs as partial-order constraints across symbolic channels rather than as one flat sequence.

# TRACK 1 — OFFICIAL DATA AND EVALUATION CONTEXT

## T1.1 Dataset provenance

- **SOURCE:** OpenRCA (Xu et al., ICLR 2025), derived from the AIOps Challenge series.
- **LICENSE:** CC BY-NC 4.0.
- **MANTISGRID MODIFICATION:** Organizer-prepared bundles with evaluated-case answers removed.
- **HACKATHON DATASET:** `Market-cloudbed-1`.
- **DOMAIN:** production telemetry from a microservice online shop with injected, operator-labelled faults.

## T1.2 Development and hidden evaluation structure

- **DEVELOPMENT:** 70 cases with answers available in `dev/query_dev.csv`.
- **CASE WINDOW:** each instruction specifies a 30-minute window and number of failures.
- **HIDDEN JUDGING:** 20 cases from another deployment of the same shop.
- **TRANSFER CONDITION:** same software and kinds of failure; different components, many unseen during development.
- **EVALUATION IMPLICATION:** literal component-name memorization is fragile; structural behavior representation has a natural opportunity to generalize.

## T1.3 Telemetry files

Approximate rows/day and size/day:

| File | Columns | Rows/day | Size/day |
|---|---|---:|---:|
| `metric/metric_container.csv` | `timestamp,cmdb_id,kpi_name,value` | 3.7 M | 265 MB |
| `metric/metric_mesh.csv` | `timestamp,cmdb_id,kpi_name,value` | 2.5 M | 247 MB |
| `metric/metric_node.csv` | `timestamp,cmdb_id,kpi_name,value` | 488 K | 21 MB |
| `metric/metric_runtime.csv` | `timestamp,cmdb_id,kpi_name,value` | 959 K | 88 MB |
| `metric/metric_service.csv` | `service,timestamp,rr,sr,mrt,count` | 16 K | 1 MB |
| `log/log_service.csv` | `log_id,timestamp,cmdb_id,log_name,value` | 4.6 M | 672 MB |
| `log/log_proxy.csv` | `log_id,timestamp,cmdb_id,log_name,value` | 7.9 M | 2.9 GB |
| `trace/trace_span.csv` | `timestamp,cmdb_id,span_id,trace_id,duration,type,status_code,operation_name,parent_span` | 9.1 M | 1.3 GB |

Distinct values for one day reported by the official guide:

- `metric_container`: 42 `cmdb_id`, 64 `kpi_name`.
- `metric_mesh`: 176 `cmdb_id`, 125 `kpi_name`.
- `metric_node`: 6 `cmdb_id`, 59 `kpi_name`.
- `metric_runtime`: 2 `cmdb_id`, 333 `kpi_name`.
- `trace_span`: 40 `cmdb_id`, 27 `operation_name`, 5 `type`, 4 `status_code`.
- `log_service`: 25 `cmdb_id`, 9 `log_name`.

## T1.4 Data traps

- **Mixed time units:** metrics/logs are seconds; traces are milliseconds.
- **Timezone:** answers use UTC+8.
- **Sampling:** there may be no datapoint exactly at fault time.
- **Network faults:** often require trace parent/child latency; metrics alone miss them.
- **Multiple faults:** some 30-minute windows contain more than one independent failure.
- **Large files:** filtering the time window before broad loading is necessary.
- **Topology embedded in names:** e.g. `node-5.adservice-2`.
- **Mesh IDs can encode source and destination.**
- **Quoted KPI names can contain commas.**
- **Trace fields are heterogeneous.**

## T1.5 Failure reasons

Official reason labels:

1. `container CPU load`
2. `container memory load`
3. `container network latency`
4. `container network packet corruption`
5. `container network packet retransmission`
6. `container packet loss`
7. `container process termination`
8. `container read I/O load`
9. `container write I/O load`
10. `node CPU load`
11. `node CPU spike`
12. `node disk read I/O consumption`
13. `node disk space consumption`
14. `node disk write I/O consumption`
15. `node memory consumption`

## T1.6 Starter baseline

- Parses time window.
- Computes robust z-score for each `(component, KPI)` series against the rest of the day.
- Ranks components by strongest anomaly.
- Keyword-matches winning KPI to a reason.
- Does not inspect logs.
- Does not inspect traces.
- Has no causal model.
- Uses symptom peak as fault time.
- Reported on all 70 Market cases:
  - mean score: `0.073`
  - fully solved: `2 / 70`
  - easy: `0.083`
  - middle: `0.060`
  - hard: `0.075`

## T1.7 Official scoring orientation

Participant agreement:

- Overall judging:
  - Technical Execution: 40%
  - Innovation / Wow Factor: 30%
  - Potential Impact: 20%
  - Presentation / Demo: 10%
- Track 1 focus:
  - model accuracy
  - explainability
  - strength of evaluations
  - token usage

Starter/scoring docs emphasize:

- evidence and explainability;
- evaluation quality;
- cost efficiency;
- accuracy on unseen cases;
- honest uncertainty and calibration;
- routing that demonstrably saves cost/time without losing much accuracy.

Starter README states `evidence/` is read by humans and is worth 35% versus accuracy's 20% in the track scoring scheme it describes.

## T1.8 Accuracy state of the art

Official scoring guide reports benchmark results on 335 cases:

| Method | Model | Strict | Partial |
|---|---|---:|---:|
| RCA-Agent | Claude 3.5 Sonnet | 11.34% | 17.31% |
| RCA-Agent | GPT-4o | 8.96% | 17.91% |
| Prompting (Oracle) | Gemini 1.5 Pro | 7.16% | 23.58% |
| Prompting (Balanced) | Gemini 1.5 Pro | 6.27% | 24.18% |
| RCA-Agent | Gemini 1.5 Pro | 2.69% | 6.87% |

Organizer framing: state of the art solves roughly one case in nine; most answers will be wrong.

## T1.9 Output contract

Submission writes:

```text
predictions.csv
evidence/<row_id>.md
```

Prediction fields must appear in exact order:

```json
{
  "1": {
    "root cause occurrence datetime": "...",
    "root cause component": "...",
    "root cause reason": "..."
  }
}
```

Sharp edges:

- wrong number of failures → whole case zero;
- wrong key order → zero;
- exact-string component/reason matching;
- timestamp tolerance ±60 seconds;
- always emit a best guess in predictions;
- express abstention/uncertainty in evidence, not by leaving prediction blank.

# HACKATHON CLAIM — OPERATIONAL FORM

## HC1. Minimal claim

> **A multimodal symbolic evidence layer can compress metrics, logs, and traces into interpretable behavioral episodes that improve root-cause candidate ranking and provide cheaper, clearer evidence to an RCA agent.**

## HC2. Stronger claim only if supported

> **Compared with metric-only anomaly ranking, multimodal symbolic fusion improves top-k localization of the true root-cause component—especially on fault classes where causal evidence is split across metrics and traces—while reducing the amount of telemetry passed to expensive models.**

## HC3. Claims not yet earned

Do not claim before evidence:

- end-to-end state-of-the-art RCA;
- causal proof from edit-distance similarity;
- universal cross-cluster transfer;
- population-dynamics detection;
- controller oscillation detection;
- MantisGrid capability gap;
- production-safe remediation;
- superior SAX representation;
- general novelty of symbolic telemetry compression.

# LEAN STARTUP EXPERIMENT PLAN

## L1 — First uncertainty: candidate localization

- **HYPOTHESIS:** Symbolic fusion improves top-k true-component recall relative to the metric heuristic.
- **TEST SET:** Hold back a subset of the 70 development cases.
- **BASELINE:** Provided heuristic.
- **TREATMENT:** Symbolic metrics; then metrics + traces; then metrics + traces + logs.
- **METRICS:**
  - top-1 component recall;
  - top-3 component recall;
  - reason-family recall;
  - onset-time error.
- **GO:** clear repeatable lift on held-out cases.
- **NO-GO:** no lift or improvements depend on component-name memorization.

## L2 — Second uncertainty: whether traces add specific causal value

- **HYPOTHESIS:** Trace symbolic behavior materially improves network-fault localization.
- **TEST:** Compare metric-only vs metrics+traces on network fault reasons.
- **EXPECTED SIGNAL:** parent-child latency increase, status transitions, path-localized delay.
- **GO:** network-fault recall improves without major false-positive inflation.

## L3 — Third uncertainty: compression/cost

- **HYPOTHESIS:** Symbolic evidence reduces strong-model input volume without materially reducing accuracy.
- **MEASURE:**
  - bytes/rows read;
  - evidence tokens sent to model;
  - dollars per case;
  - wall-clock;
  - accuracy.
- **COMPARE:**
  - raw/filtered telemetry prompt;
  - symbolic evidence packet;
  - routed vs single strong model.

## L4 — Fourth uncertainty: hidden-deployment transfer

- **HYPOTHESIS:** Role/topology-normalized motifs transfer across unseen component identities.
- **PROXY TEST:** hold out services/components during development where feasible.
- **TRUE TEST:** organizer’s hidden deployment.
- **FAILURE MODE TO WATCH:** rules that silently learn literal naming conventions.

# PROPOSED SYMBOLIC REPRESENTATION

## S1 — Metric state alphabet

Initial simple alphabet:

- `N` — normal/baseline
- `R` — sustained rise
- `H` — sustained high
- `P` — spike
- `F` — sustained fall
- `O` — oscillatory
- `X` — missing / insufficient
- `REC` — recovery toward baseline

Keep KPI family attached:

```text
READ_IO: N N R H H
CPU:     N N N N N
MEM:     N N N N N
```

## S2 — Trace behavior alphabet

Per causal edge/path:

- `LAT_N`
- `LAT_RISE`
- `LAT_HIGH`
- `ERR_RISE`
- `TIMEOUT`
- `SPAN_MISSING`
- `CHILD_DELAY`
- `PARENT_DELAY`

Preserve:

- source component;
- destination component;
- parent span;
- child span;
- causal path;
- relative onset.

## S3 — Log behavior alphabet

Normalize raw messages/events into:

- `INFO_BASE`
- `WARN_RISE`
- `ERROR_BURST`
- `RETRY_BURST`
- `TIMEOUT_BURST`
- `PROCESS_EXIT`
- `IO_WARNING`
- `NETWORK_WARNING`
- `UNKNOWN_EVENT`

Initial implementation can use log_name/category counts before semantic parsing.

## S4 — Topology abstraction

Represent:

- node;
- pod;
- service;
- source→destination edge;
- sibling pods;
- node-to-pod placement.

Potential normalized roles:

- `CANDIDATE_SOURCE`
- `DOWNSTREAM_SYMPTOM`
- `UPSTREAM_CALLER`
- `SIBLING_HEALTHY`
- `NODE_PARENT`
- `SERVICE_PEER`

## S5 — Fused evidence packet

Example:

```markdown
## Candidate: shippingservice-1
Reason candidate: container read I/O load

### Metric evidence
09:06:10 READ_IO transitions N→R
09:06:18 READ_IO reaches H
CPU and memory remain N

### Trace evidence
09:06:20 shipping→downstream child latency transitions N→R
09:06:28 downstream caller latency rises

### Log evidence
No process-exit burst
No corresponding node-level error burst

### Causal ordering
shipping read-I/O transition precedes downstream latency by ~10s

### Alternatives
emailservice-0 also shows latency rise, but begins later and lacks local resource transition

### Confidence
Medium
```

# MODEL-ROUTING DESIGN

## R1 — Deterministic / cheap stage

Responsibilities:

- parse case window;
- load/filter relevant data;
- compute baseline/transition features;
- construct symbolic streams;
- rank candidate components;
- generate candidate evidence packet.

## R2 — Cheap model stage

Possible responsibilities:

- classify ambiguous log templates;
- summarize candidate evidence;
- check output formatting;
- produce concise evidence prose.

## R3 — Strong model stage

Only for:

- causal comparison among top candidates;
- difficult multimodal conflicts;
- final selection of component/reason/time when deterministic evidence is insufficient.

## R4 — Stopping rule

Stop escalating when:

- one candidate has strong cross-modal agreement;
- alternatives lack independent evidence;
- reason family is unambiguous;
- onset estimate falls within a narrow interval.

Escalate when:

- top candidates are close;
- channels disagree;
- evidence is missing;
- network fault requires trace interpretation.

# EXPLAINABILITY MODEL

## E1 — Evidence should show temporal precedence

Not:

> “shippingservice-1 had the largest anomaly.”

Prefer:

> “shippingservice-1 read-I/O departed baseline first; downstream latency rose afterward; node CPU/memory stayed normal; competing services became anomalous only after the shipping-service transition.”

## E2 — Evidence should preserve alternatives

Include:

- strongest alternative;
- why it was rejected;
- missing evidence;
- uncertainty;
- whether timing differences may be sampling noise.

## E3 — Missing-signal honesty

Borrow from original A05 concept:

- mask or remove modalities during evaluation;
- measure whether confidence changes;
- surface when the decisive sensor is absent.

Potential result:

> “Without traces, the system confuses network latency with downstream service symptoms; adding parent-child latency restores top-3 localization.”

# RELIABILITY ACTIVITY RECOGNITION — LONGER RESEARCH PROGRAM

## P1 — The publishable object

The stronger research problem is not “SAX for infrastructure.”

It is:

> **Continuous recognition of emergent reliability behaviors in distributed systems from fused symbolic telemetry streams.**

Academic working titles:

- **From Telemetry to Behavior: Continuous Recognition of Emergent Reliability Dynamics in Distributed Systems**
- **Continuous Reliability Activity Recognition with Multimodal Symbolic Telemetry**

## P2 — Research task definition

Input:

- continuous multimodal observability streams;
- topology / dependency structure;
- optionally controller actions.

Output:

- activity class;
- onset;
- offset;
- confidence;
- aligned evidence.

Potential activity classes:

- failover stampede;
- premature recolonization;
- coupled-controller oscillation;
- retry amplification;
- cascading resource migration;
- shared-fate collapse.

## P3 — Why this differs from ordinary RCA

Ordinary RCA:

```text
What component failed?
What caused it?
```

Reliability activity recognition:

```text
What temporally extended behavior is the system entering?
How are workloads/controllers/resources interacting?
Is the recovery behavior itself amplifying risk?
```

## P4 — Population observables

Candidate measurable signals:

- workload concentration;
- migration flow;
- controller synchrony;
- remaining headroom;
- shared-fate exposure;
- action frequency;
- recovery hysteresis;
- destination occupancy;
- recurrence rate.

## P5 — Cross-system transfer

Normalize literal identities into structural roles.

Example:

```text
node-172 → SOURCE_RESOURCE
node-214 → DESTINATION_RESOURCE
payments-api → WORKLOAD
```

Motif:

```text
SOURCE_DEGRADES
→ POPULATION_MIGRATES
→ DESTINATION_CONCENTRATION
→ HEADROOM_COLLAPSES
```

Research question:

> Can the same symbolic motif be recognized across topologically different clusters?

# DIFFERENTIATION FROM MANTISGRID

## M1 — What MantisGrid publicly already claims

Publicly described capabilities discussed in this context include:

- ingestion of logs, telemetry, configuration;
- real-time reliability graph;
- dependency-aware signal correlation;
- anomaly/risk detection;
- root-cause identification;
- Findings;
- predictive fault models;
- governed / closed-loop remediation;
- synthetic reliability scenarios through the Rockfish partnership.

Therefore none of the following are sufficient novelty claims:

- sensor fusion for infrastructure;
- multimodal telemetry correlation;
- dependency-aware RCA;
- real-time reliability graphs;
- predictive reliability;
- autonomous remediation.

## M2 — Differentiated research layer

Potentially differentiated public whitespace identified in discussion:

1. **Activities rather than faults**
   - recognize temporally extended behaviors.
2. **Population dynamics rather than individual components**
   - detect collective behavior before any one resource necessarily fails.
3. **Controller actions as observations**
   - treat remediation/control actions as telemetry to diagnose control-population instability.
4. **Continuous episode segmentation**
   - identify onset/offset rather than relying on incident-ticket boundaries.
5. **Topology-independent behavioral motifs**
   - transfer learned patterns across deployments.

## M3 — Panel formulation

> “Your platform already does the hard part I initially thought I was exploring: multimodal correlation, dependency-aware RCA and predictive reliability. The direction that became interesting is one level above that. Can we treat the infrastructure itself as a continuously behaving system and recognize recurring system activities—not just faults—such as coordinated failover, controller oscillation, workload recolonization or resource-pool cascades?”

Short distinction:

> **Instead of asking only ‘what failed?’, ask ‘what is the system doing?’**

# AGENT-TRACE REVIEW ANALOGY

## A1 — Shared abstraction: causal compression

Infrastructure RCA:

```text
telemetry + logs + config + topology
→ correlation
→ failure pattern
→ root-cause candidate
→ prioritized finding
```

Agent trace review:

```text
prompts + tool calls + state transitions + outputs
→ correlation
→ behavioral failure pattern
→ critical failure step / likely cause
→ prioritized issue
```

Shared problem:

> Transform high-volume low-level observations into a small set of evidence-backed causal hypotheses.

## A2 — Commercial agent-trace analogs discussed

- Arize Signal
- Braintrust Topics / Patterns / Debugger
- Datadog Agent Observability Patterns

These systems illustrate population-level issue/pattern discovery over agent traces.

## A3 — Research lineage discussed

- AgentRx
- AgenTracer
- AgentDiagnose
- AgentPex
- AGENTSCOPE
- STRACE
- process mining / conformance checking
- distributed-trace RCA

## A4 — Future cross-layer extension

Potential long-term system:

```text
AGENT BEHAVIOR
tool calls
retries
parallel agents
workflow branching

+

INFRASTRUCTURE BEHAVIOR
GPU load
scheduling
routing
migration
resource pressure

↓

CROSS-LAYER RELIABILITY ACTIVITY
```

Example feedback loop:

```text
agent retries
→ inference demand spike
→ scheduler redistribution
→ GPU concentration
→ latency rise
→ agent timeout
→ more retries
```

This cross-layer loop sits between conventional agent observability and conventional infrastructure RCA.

# PRIOR-ART BOUNDARY

## PA1 — Symbolic telemetry itself is not novel

Neighboring work discussed includes:

- KPIRoot / KPIRoot+ — SAX / symbolic compression in cloud KPI RCA;
- sequence alignment for system-level traces;
- Workflow Motifs — recurring subgraphs in distributed traces;
- multimodal metrics/logs/traces RCA;
- symbolic/log evidence compression before LLM diagnosis;
- time-series shapelet methods.

Therefore:

> The research novelty cannot be “turn telemetry into symbols.”

## PA2 — Stronger novelty candidate

> Define and recognize **reliability activities**: temporally extended, multi-component behaviors detected continuously from fused symbolic streams, with cross-system transfer and missing-modality robustness.

## PA3 — Publishable evaluation dimensions

1. Continuous activity precision/recall/F1.
2. Temporal IoU / onset delay.
3. Cross-system transfer.
4. Missing-modality robustness.
5. Analysis cost.
6. Downstream RCA improvement.
7. Human/operator actionability.

# HACKATHON PRESENTATION STORY

## Story arc

1. **2008 — disposable compute**
   - server-as-object intuition breaks.
2. **Cloud abstraction**
   - for startups, compute feels effectively limitless.
3. **2026 — physical substrate returns**
   - AI exposes GPU/memory/power/network/placement constraints.
4. **Existing MantisGrid strength**
   - multimodal infrastructure RCA already exists.
5. **Research transfer**
   - physical sensing/HAR methods recognize activity from many continuous signals.
6. **Hackathon experiment**
   - can symbolic multimodal evidence help separate cause from symptom in OpenRCA?
7. **Longer thesis**
   - can infrastructure itself have recognizable activities?

## 90-second orientation skeleton

- “In 2008 I watched a founder friend terminate the EC2 instance running his app because it was behaving strangely.”
- “I was horrified because my mental model was still that the server was where the application lived.”
- “He had internalized the new abstraction: the instance was disposable; bring up another image, reconnect it to durable state, keep going.”
- “For teams like ours, the cloud could be treated as effectively infinite.”
- “AI infrastructure is making the physical system underneath that abstraction visible again.”
- “I’m borrowing an idea from continuous human-activity recognition: multiple noisy sensor streams can be discretized, matched, and fused to recognize an activity no individual sensor names.”
- “Today I’m testing the narrow version: whether the same idea can help an RCA agent distinguish cause from downstream symptoms across metrics, logs, and traces.”
- “The larger question is not only ‘what failed?’ but ‘what is the system doing?’”

# OFFICIAL RULES / IP / LICENSING

## RUL1 — Fresh work

- All judged work must be created during the hackathon.
- Ideas, plans, and pre-existing projects may exist beforehand.
- Pre-existing code written by the participant may not be reused as judged work.
- Open-source libraries/frameworks/starter kits are allowed under their licenses.
- Thin wrappers/reskins can score poorly or be disqualified from awards.
- Judges consider functionality created during the event.

## RUL2 — AI disclosure

Repository README must list:

- AI models used;
- coding assistants;
- agent frameworks;
- what was AI-generated vs team-built.

Judges may ask any member to explain the architecture/code.

## RUL3 — Submission

- Public source repository.
- Dockerfile.
- Secrets removed.
- AI-disclosure README.
- Around four-minute presentation.
- Submission deadline: 3:00 PM PDT, September 17, 2026.

## RUL4 — IP

- Participant project remains participant intellectual property.
- Submission grants MantisGrid a non-exclusive worldwide royalty-free license to use/display/reference the submission for judging and promotion for three years.
- Participant warrants rights to submitted materials.

## RUL5 — Track 1 data license

- OpenRCA-derived Track 1 telemetry: **CC BY-NC 4.0**.
- This is materially friendlier for a later reproducible noncommercial research artifact than Track 2’s source license.

## RUL6 — Track 2 license contrast

- MIT SuperCloud TX-GAIA: **CC BY-NC-ND 4.0**.
- NoDerivatives restriction is why the official repository does not redistribute Track 2 data.
- Working tables generated from it may not be redistributed.

# ACTION PLAN

## A0 — Immediate setup

1. Run official starter baseline.
2. Confirm scorer/output contract.
3. Select a held-out development subset before tuning.
4. Build a fast time-window telemetry loader.
5. Normalize seconds vs milliseconds and UTC+8 immediately.

## A1 — Implement metric symbolizer

- reuse robust baselines where possible;
- produce per `(component, KPI)` transitions;
- retain onset timestamps and strength;
- aggregate to candidate component scores.

## A2 — Implement trace symbolizer

- filter traces to case window;
- reconstruct parent/child edges;
- derive latency transitions;
- derive component-pair anomalies;
- rank components where abnormal edge behavior begins rather than where latency is largest.

## A3 — Run first ablation

Compare:

- baseline metric heuristic;
- symbolic metrics;
- symbolic metrics + traces.

Report:

- top-1/top-3 component recall;
- network-fault subset recall;
- onset error;
- runtime.

## A4 — Add logs only if justified

- first use `log_name` frequency/burst features;
- avoid spending early time on semantic LLM parsing unless evidence shows logs add discriminative power.

## A5 — Add LLM reasoning

Input only:

- top candidates;
- compact evidence packet;
- valid reason label list;
- exact output schema.

Compare:

- single strong GLM;
- routed GLM;
- potentially deterministic/cheap handling of high-confidence cases.

## A6 — Produce evidence files

Every evidence artifact should include:

- what was inspected;
- primary evidence;
- temporal ordering;
- strongest alternative;
- confidence;
- missing/ambiguous signal;
- reason for final choice.

## A7 — Final eval

Run:

- official scorer;
- routed vs single-model comparison;
- per-difficulty breakdown;
- per-fault-family breakdown;
- cost/case;
- seconds/case;
- token usage;
- confidence calibration where possible.

# OPEN QUESTIONS

## Q1 — Does symbolic fusion actually improve component recall?

Highest-priority unknown.

## Q2 — Which modality provides the largest marginal lift?

Possible answers:

- metrics dominate common resource faults;
- traces rescue network faults;
- logs add little;
- logs add decisive process/error evidence.

Do not assume.

## Q3 — How should transitions be encoded?

Candidates:

- fixed thresholds;
- robust z-score states;
- change-point detection;
- SAX/SFA;
- ordinal patterns;
- learned quantization.

Hackathon rule: start simple.

## Q4 — What is the right fusion rule?

Candidates:

- weighted evidence scoring;
- rank aggregation;
- motif edit distance;
- probabilistic fusion;
- LLM arbitration over compact per-channel evidence.

## Q5 — Can onset be inferred consistently enough for ±60s scoring?

May depend strongly on sampling cadence and fault type.

## Q6 — Does topology normalization help on unseen deployment?

Cannot be fully known before hidden judging.

## Q7 — How much does compression reduce model cost?

Measure; do not infer.

## Q8 — Can missing-signal robustness become a meaningful result?

Possible evaluation:

- remove traces;
- remove logs;
- remove metrics;
- mask intervals;
- measure candidate recall/confidence changes.

## Q9 — Does the broader Reliability Ecologist phenomenon appear in OpenRCA?

No evidence yet that the Track 1 dataset contains enough controller-action or workload-migration data to support this claim.

## Q10 — Does MantisGrid already model higher-order behavioral episodes internally?

Public materials do not establish this. Ask with concrete examples rather than abstract terminology.

# EVIDENCE / SOURCE INVENTORY

## Official MantisGrid hackathon repository

### Participant agreement

`https://github.com/MantisGridAI/hackathon-2026-official/blob/main/PARTICIPANT_AGREEMENT.md`

Carries:

- fresh-work rule;
- AI disclosure;
- public repo requirement;
- judging;
- IP;
- event rules.

### Attribution

`https://github.com/MantisGridAI/hackathon-2026-official/blob/main/ATTRIBUTION.md`

Carries:

- Track 1 OpenRCA provenance;
- CC BY-NC 4.0;
- Track 2 MIT SuperCloud TX-GAIA provenance;
- CC BY-NC-ND 4.0;
- synthetic shared-volume scenario note.

### Track 1 README

`https://github.com/MantisGridAI/hackathon-2026-official/blob/main/track-1/README.md`

Carries:

- RCA challenge;
- GLM routing requirement;
- unseen-data evaluation;
- evidence/eval/cost focus.

### Track 1 starter README

`https://github.com/MantisGridAI/hackathon-2026-official/blob/main/track-1/starter/README.md`

Carries:

- starter structure;
- output files;
- baseline behavior and score;
- routed-agent example;
- evidence weighting note;
- exact output constraints.

### Track 1 data guide

`https://github.com/MantisGridAI/hackathon-2026-official/blob/main/track-1/docs/data.md`

Carries:

- file schemas and sizes;
- 70 cases;
- unseen deployment;
- data traps;
- 15 reason labels;
- topology naming;
- network-fault trace dependence.

### Track 1 scoring

`https://github.com/MantisGridAI/hackathon-2026-official/blob/main/track-1/docs/scoring.md`

Carries:

- benchmark baselines;
- hidden test behavior;
- strict/partial scoring;
- output sharp edges;
- cost/time evaluation;
- calibration;
- required routed-vs-single-model comparison.

## MantisGrid public product research discussed

- `https://www.mantisgrid.ai/`
- `https://mantisgrid.ai/blog/k8s-reliability-for-ai`
- `https://www.mantisgrid.ai/blog/DesignpartnershipRockfishdata`
- `https://www.mantisgrid.ai/blog/accuknox`

Used for:

- multimodal telemetry;
- reliability graph;
- Findings;
- dependency-aware RCA;
- predictive fault modeling;
- synthetic failure scenarios;
- governed remediation.

## Sensor / activity-recognition lineage

### Stiefmeier

- Stiefmeier et al. (2007), **Fusion of String-Matched Templates for Continuous Activity Recognition**.
- Stiefmeier et al. (2008), **Wearable Activity Tracking in Car Manufacturing**, IEEE Pervasive Computing.

### User-supplied later references

- Sousa Lima, W., De Souza Bragança, H. L., Montero Quispe, K. G., & Pereira Souto, E. J. (2018). *Human activity recognition based on symbolic representation algorithms for inertial sensors*. Sensors 18(11), 4045. `https://doi.org/10.3390/s18114045`
- Mezari, A., & Maglogiannis, I. (2018). *An easily customized gesture recognizer for assisted living using commodity mobile devices*. Journal of Healthcare Engineering. `https://doi.org/10.1155/2018/3180652`
- Pappa, L., Karvelis, P., Georgoulas, G., & Stylios, C. (2020). *Multichannel Symbolic Aggregate Approximation intelligent icons: Application for activity recognition*. IEEE SSCI. `https://doi.org/10.1109/ssci47803.2020.9308497`
- Jia, Y., Xu, M., & Wang, R. (2018). *Symbolic important point perceptually and Hidden Markov Model based hydraulic pump fault diagnosis method*. Sensors 18(12), 4460. `https://doi.org/10.3390/s18124460`
- Han, B., Wang, S., Zhu, Q., Yang, X., & Li, Y. (2020). *Intelligent fault diagnosis of rotating machinery using hierarchical Lempel-Ziv complexity*. Applied Sciences 10(12), 4221. `https://doi.org/10.3390/app10124221`
- Chicco, G. (2021). *Data consistency for data-driven smart energy assessment*. Frontiers in Big Data 4. `https://doi.org/10.3389/fdata.2021.683682`

## Agent-trace diagnosis lineage preserved from the companion UFCE

- AgentRx
- AgenTracer
- AgentDiagnose
- AgentPex
- AGENTSCOPE
- STRACE
- van der Aalst process mining
- Arize Signal
- Braintrust Topics / Patterns / Debugger
- Datadog Agent Observability Patterns

Companion context source:
`agent_trace_review_mantisgrid_ufce.v1.md`

# EPISTEMIC STATUS

## Established by official hackathon sources

- Track 1 dataset provenance and license.
- File schemas/approximate sizes.
- 70 development cases.
- hidden evaluation on another deployment.
- scoring requirements.
- baseline implementation and reported score.
- reason labels.
- telemetry traps.
- fresh-work/IP rules.

## Established by MantisGrid public material discussed in-session

- MantisGrid claims multimodal telemetry ingestion, dependency-aware correlation, reliability graph, Findings, RCA, prediction, and governed remediation.

## User-supplied research summary

- Details and interpretation of several 2018–2021 symbolic time-series / HAR / machinery references.
- These should be bibliography-verified before formal publication even where DOI metadata was supplied.

## Working hypothesis / inference

- symbolic fusion may improve top-k candidate recall;
- topology-normalized motifs may transfer better;
- compact evidence may reduce LLM cost;
- reliability activity recognition may be a publishable abstraction;
- controller/population dynamics may form recurring infrastructure activities.

These are not treated as established results.

# CONTEXT CAPSULE

The work began as divergent hackathon exploration and produced a “Reliability Ecologist” persona: a systems view in which individually sensible controllers can synchronize, displace risk, and create fleet-wide instability. That led to a comparison between population dynamics and closed-loop control systems, then to a mapping from multimodal continuous human-activity recognition into infrastructure observability.

The key conceptual bridge was Stiefmeier’s activity-recognition approach: continuous noisy sensor streams can be discretized into symbolic sequences, matched approximately, and fused to recognize higher-level actions that no single sensor explicitly names. The corresponding infrastructure idea is to preserve distinct symbolic channels for metrics, logs, traces, topology, and eventually controller actions, then recognize higher-level reliability behavior.

A broader publishable direction emerged: **Continuous Reliability Activity Recognition**, in which temporally extended infrastructure behaviors such as failover stampedes, coupled-controller oscillations, premature recolonization, or resource-migration cascades become first-class recognition objects. This was differentiated from MantisGrid’s public product story, which already includes multimodal signal correlation, reliability graphs, root-cause identification, Findings, prediction, and remediation.

The official hackathon brief then materially narrowed the practical opportunity. Track 1 supplies a 12 GB OpenRCA-derived multimodal dataset, 70 development cases, an unseen evaluation deployment, a weak metric-only baseline, GLM model routing, and scoring that strongly values evidence, evaluation quality, cost, and explanation. Track 1 therefore became the best near-term substrate for validating the **underlying representation method**, even if it cannot validate the whole population-dynamics thesis.

The current hackathon thesis is:

> **A multimodal symbolic evidence layer for efficient, explainable infrastructure RCA.**

The first test is whether symbolic fusion improves gold root-cause component top-k recall over the provided metric-only anomaly baseline. The second is whether trace-symbol fusion particularly improves network-fault localization. The third is whether compact evidence reduces model context, cost, and wall-clock while preserving or improving official benchmark performance.

If those tests succeed, the hackathon becomes experiment zero for the longer research program. If they fail, the negative result should be reported honestly rather than forcing the Reliability Ecologist narrative onto data that does not support it.

# RESUME PROMPT

Continue from this root thesis:

> **Build and evaluate a multimodal symbolic evidence layer for efficient, explainable infrastructure RCA on the MantisGrid Track 1 OpenRCA dataset.**

Preserve these constraints:

1. Do not claim sensor fusion, multimodal RCA, reliability graphs, or prediction are novel to MantisGrid.
2. Do not force population/controller-dynamics claims onto Track 1 unless the data actually contains the required signals.
3. Validate candidate localization before spending heavily on LLM reasoning.
4. Preserve separate metric/log/trace/topology channels.
5. Treat time localization as onset detection, not peak selection.
6. Optimize for evidence quality, hidden-deployment transfer, routing/cost, and honest uncertainty.
7. Keep the larger research path alive: fault activity recognition → continuous reliability activity recognition → population/control dynamics.
8. All judged implementation code must be created during the hackathon under the official fresh-work rule.
9. Track 1 data is OpenRCA-derived CC BY-NC 4.0; comply with attribution/noncommercial terms.
10. A negative result that cleanly falsifies a mechanism is preferable to an unsupported positive claim.

Immediate next experiment:

- run baseline;
- hold out a dev subset;
- build metric symbolic transitions;
- add trace-path symbolic transitions;
- compare top-1/top-3 component recall;
- quantify network-fault lift;
- only then add logs and LLM routing.

# EXHAUSTIVENESS CHECK

Covered:

- root hackathon thesis;
- 2008 EC2 story hook and historical caveats;
- Reliability Ecologist origin;
- population dynamics vs closed-loop control;
- sensor fusion / continuous activity recognition transfer;
- symbolic stream design;
- partial-order trace caveat;
- MantisGrid public capability boundary;
- differentiated longer-term research space;
- agent-trace causal-compression analogy;
- Track 1 official dataset structure;
- hidden deployment/generalization opportunity;
- baseline weakness;
- official scoring/evaluation constraints;
- reason labels and telemetry traps;
- Lean Startup wedge;
- candidate-recall-first experiment;
- model routing;
- explainability;
- missing-signal testing;
- publishable extension;
- hackathon rules;
- IP;
- licensing;
- action plan;
- open questions;
- source inventory;
- epistemic status;
- context capsule;
- resume prompt.

Known exclusions / unresolved areas:

- no claim that the hackathon dataset contains controller-action population dynamics;
- no completed empirical results yet;
- no selected symbolic algorithm beyond an initial simple state alphabet;
- no verified optimal fusion method;
- no completed novelty review sufficient for a publication claim;
- no legal interpretation beyond reporting official license/rule text;
- no assumption that MantisGrid lacks internal capabilities not described publicly.

# COMPRESSION FAILURE AUDIT

Potentially lossy distinctions explicitly preserved:

1. **Symbolic telemetry ≠ novelty.**
   - Prior cloud RCA and time-series work already uses symbolic representations.
2. **Sensor fusion ≠ MantisGrid gap.**
   - MantisGrid already claims multimodal correlation.
3. **Fault recognition ≠ population behavior recognition.**
   - Track 1 validates the former; the latter is a later research extension.
4. **Correlation ≠ causality.**
   - Motif similarity must not be presented as causal proof.
5. **Peak anomaly time ≠ fault onset.**
   - Track 1 should explicitly model transition/onset.
6. **Downstream symptom ≠ root cause.**
   - This is the central baseline failure the project attacks.
7. **More data ≠ better reasoning.**
   - The project tests whether compact structured evidence beats raw-volume prompting.
8. **Candidate recall ≠ end-to-end RCA.**
   - It is the first representation-layer gate, not the final score.
9. **Hidden-deployment transfer ≠ guaranteed generalization.**
   - It is one meaningful externalization test.
10. **A strong hackathon result ≠ publication novelty.**
    - Publication requires a broader prior-art review, reproducible benchmark design, and deeper experiments.
11. **A negative result ≠ failure.**
    - The event explicitly rewards defensible evaluation and honest uncertainty.
12. **Pre-event thinking ≠ pre-event code.**
    - Planning is allowed; judged code must be built during the hackathon.

# END STATE

The single organizing thesis for the current work is:

> **A multimodal symbolic evidence layer for efficient, explainable infrastructure RCA.**

Everything else is subordinate:

- **Human activity recognition** provides the methodological inspiration.
- **OpenRCA Track 1** provides the immediate falsifiable experiment.
- **MantisGrid** provides the infrastructure-RCA setting and public capability boundary.
- **Lean Startup** determines what must be learned first.
- **Reliability Ecologist** provides the larger systems interpretation.
- **Population dynamics** supplies the future class of emergent activities.
- **Agent-trace diagnosis** supplies a parallel causal-compression lineage.
- **Continuous Reliability Activity Recognition** is the longer publishable research direction if the representation proves useful.
