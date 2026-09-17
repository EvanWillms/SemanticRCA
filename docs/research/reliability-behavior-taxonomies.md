# Reliability behaviors: taxonomies, recognition formalisms, and semantic compression

Date: 2026-09-17. Status: bounded primary-source review and research-design synthesis; no empirical result or novelty claim. Incorporates the user's distinction between faults and temporally extended behaviors and the supplied literature leads, checked against available primary texts.

## Answer to the research question

Relevant classifications exist, but they classify different objects: dynamical forms, propagation relations, sustaining mechanisms, verification properties, and temporal event patterns. They should not become one flat list of mutually exclusive labels. This review did not establish a comprehensive accepted operational taxonomy for continuous reliability-behavior recognition across cloud telemetry.

The closest conceptual precedent is emergent software misbehavior. The closest recognition architecture is chronicle/composite-event recognition. Metastability and controller-verification research supply narrower definitions that can make behavior hypotheses testable. None of those findings establishes a contribution from adding an LLM; that requires a separate experiment.

The immediate thesis remains **a multimodal symbolic evidence layer for efficient, explainable infrastructure RCA**. The longer target remains **continuous recognition of emergent reliability behaviors from fused telemetry**. The research object is a temporally structured evidence episode, not a renamed abnormal measurement.

## What is classified, and how mature is it?

| Lineage | Classification object and reusable vocabulary | Status and limit |
|---|---|---|
| Mogul, EuroSys 2006 | Emergent misbehavior: thrashing, unwanted synchronization, unwanted oscillation/periodicity, deadlock, livelock, phase change, chaotic behavior; causes classified separately | Explicit provisional taxonomy and research agenda, not an operational standard. [Paper §5](https://shiftleft.com/mirrors/www.hpl.hp.com/techreports/2006/HPL-2006-2.pdf) |
| Parunak and VanderBok, ISA-Tech 1997 | Dynamical forms versus mechanisms such as limits, feedback, and delay; recovered-resource competition and repeated shutdown/restart examples | Direct distributed-control predecessor; original text accessed through a reproduction. [Primary text reproduction](https://studylib.net/doc/8298729/managing-emergent-behavior-in-distributed-control-systems) |
| Bronson et al., HotOS 2021; Huang et al., OSDI 2022 | Stable/vulnerable/metastable regimes; trigger versus sustaining effect; trigger classes and amplification classes | A defined framework with subsequent incident studies and reproductions, covering one family of behaviors. [2021](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf), [2022](https://www.usenix.org/system/files/osdi22-huang-lexiang.pdf) |
| Kivi, ATC 2024 | Unexpected topology, object numbers, object lifecycles, oscillation | Implemented model checking and a property taxonomy; not a runtime episode catalogue. [Paper §3](https://www.usenix.org/system/files/atc24-liu-bingzhe.pdf) |
| Rinaldi, Peerenboom, Kelly, 2001 | Cascading, escalating, common-cause disruptions; interdependency dimensions | Explicit critical-infrastructure taxonomy; cloud adaptation must define boundaries and dependency semantics. [Author-uploaded paper](https://www.researchgate.net/profile/James-Peerenboom/publication/3206740_Identifying_understanding_and_analyzing_critical_infrastructure_interdependencies/links/5628c9fa08aef25a243d2137/Identifying-understanding-and-analyzing-critical-infrastructure-interdependencies.pdf) |
| Pertet and Narasimhan, HotDep 2005 | Recovery escalation, chained reconfiguration, progressive error propagation, unhandled exceptions, malicious propagation | Explicit initial cascade taxonomy; mixes mechanisms and initiators. Distinguishes normal, failure-driven, and recovery-driven dependencies. [Table 1](https://research.ece.cmu.edu/mead/dsn-hotdep-2005.pdf) |
| Avižienis et al., TDSC 2004 | Fault/error/service failure, behavior, propagation, boundaries, recovery | Foundational dependability taxonomy; already extends beyond individual faults, but does not supply a retry-storm classifier. [Paper](https://www.landwehr.org/2004-aviz-laprie-randell.pdf) |
| Networking and operations | Congestion-collapse subtypes, inadvertent synchronization, retry storms, thundering herd, correlated failures | Mixture of formal models and operational terms, not one taxonomy. [RFC 2914](https://www.ietf.org/rfc/rfc2914), [Floyd/Jacobson](https://www.icir.org/floyd/papers/sync_94.pdf), [AWS retry guidance](https://docs.aws.amazon.com/wellarchitected/2024-06-27/framework/rel_mitigate_interaction_failure_limit_retries.html) |

The distinctions cut across each other. An episode can exhibit synchronization, amplify work through retries, propagate overload, and enter a metastable regime. These are different descriptions of its temporal form, mechanism, spread, and recovery behavior.

## How far did the agenda progress?

This is a set of relevant developments, not a demonstrated single genealogy of influence or an exhaustive citation-network analysis.

**Temporal recognition became implementable well before modern LLMs.** Dousson and colleagues' situation-recognition work appears in IJCAI 1993. Later chronicle work learns numerical temporal constraints from alarm logs and implements hierarchical recognition with attention to informative events. It explicitly separates raw-data processing from symbolic scenario recognition and represents scenarios through temporal constraints. [1993 proceedings entry](https://www.ijcai.org/proceedings/1993-1), [Dousson and Vu Duong, 1999](https://www.ijcai.org/Proceedings/99-1/Papers/089.pdf), [Dousson and Le Maigat, 2007](https://www.ijcai.org/Proceedings/07/Papers/050.pdf)

**There are reusable temporal formalisms, not only named behaviors.** Frequent-episode mining defines serial, parallel, and partially ordered event collections within time windows. It originated in part from telecom alarm analysis. An episode is not necessarily an entire incident; recurrence is not a causal proof. [Mannila, Toivonen, Verkamo, 1997](https://www.cs.helsinki.fi/u/htoivone/pubs/dmkd97episodes.pdf)

**Composite-event recognition developed streaming and uncertainty machinery.** RTEC supports higher-level event recognition, delayed/revised observations, and efficient windowing. Probabilistic Event Calculus addresses uncertainty in logical recognition. These are architectural precedents; neither supplies an infrastructure-behavior ontology or demonstrates LLM utility. [Artikis et al., 2015](https://users.iit.demokritos.gr/~a.artikis/publication/tkde15/), [Skarlatidis et al.](https://arxiv.org/abs/1207.3270)

**Controller interaction moved into executable verification.** Kivi turns cluster configurations, controller models, and operator properties into checks and counterexamples. Its controller cycles ground the concern technically. A finite recorded cycle, however, is evidence of recurrence, not proof of unending nonconvergence. [Kivi](https://www.usenix.org/system/files/atc24-liu-bingzhe.pdf)

**Metastability moved toward mathematical characterization.** HotOS 2025's *Analyzing Metastable Failures* introduces semantic models of request/queue/retry behavior across analytical and experimental backends. Follow-on formal work uses continuous-time Markov chains and escape probabilities. This is progress beyond naming a bad regime, but depends on modeling assumptions and calibration. [HotOS 2025](https://sigops.org/s/conferences/hotos/2025/papers/hotos25-106.pdf), [formal-analysis preprint](https://arxiv.org/abs/2510.03551)

**Recent work directly addresses harmful composition.** A 2026 preprint distinguishes structural metastable faults from executions exhibiting metastable failure and studies destabilizing interaction cycles among individually stabilizing components. It is a preprint, not an established consensus classification. [Farahbakhsh et al.](https://arxiv.org/abs/2606.00942)

**Recovery itself is an object of analysis.** A first-party SREcon presentation describes recovery cascades whose costs amplify and feed back into systems already recovered. Its event URL and displayed year disagree, so no precise year is asserted here. [Porter and Charapko, *When the Cure Is Worse than the Disease*](https://www.usenix.org/conference/srecon26americas/presentation/porter)

This evidence supports a narrower positioning: investigate a faithful, compact, uncertainty-aware interface between established behavior-recognition ideas and LLM reasoning. Whether that interface adds value beyond deterministic recognition, numerical summaries, or conventional temporal reasoning remains open. Earlier repository language calling the behavior layer itself novel is not substantiated by this review.

## Mapping the candidate labels without assuming their correctness

The mappings below are our interpretation of the cited literature, not claims that each candidate phrase is a canonical taxonomy entry. See the linked supporting notes for source-specific detail.

| Proposed phrase | Better-established anchor | Evidence needed before using it |
|---|---|---|
| Failover stampede | Unwanted synchronization plus failover/load redistribution | Multiple actors, common timing, destinations, and resulting load concentration; concurrence alone is insufficient |
| Cascading workload migration | Chained reconfiguration or load-redistribution cascade | Successive placement changes and dependency/overload effects |
| Retry amplification | Workload amplification; retry storm in operational usage | Attempts distinguished from original logical demand; retry lineage or equivalent accounting |
| Thundering herd | Established concurrent-contention pattern | Many participants contend for the same resource/event; not every traffic surge |
| Coupled-controller oscillation | Unwanted oscillation, controller interaction, nonconvergence | Controller actions, shared actuators, delays, and recurrence; periodic workload is a confounder |
| Scale-up / scale-down hunting | Autoscaling flapping or thrashing in Kubernetes documentation | Replica reversals related to demand and scaling decisions, not merely a periodic replica trace |
| Repeated recovery and re-failure | Recurrent degradation; possibly recovery escalation or an oscillatory loop | Actual recovery criteria and whether each relapse has a fresh trigger |
| Premature workload return after recovery | Recovery-driven overload / reintroduction of load | Routing or admission resumes before sufficient capacity, then renewed degradation; exact phrase remains descriptive |
| Resource-pool depletion and recovery | Resource exhaustion/replenishment trajectory; possibly a relaxation cycle | Acquisition, release, replenishment, and demand accounting; no universal fault label follows |
| Shared-fate collapse | Common-cause or correlated failure | A shared dependency/cause must be established; correlation alone does not identify it |
| Correlated failover | Synchronization or responses to a common cause | Distinguish coordinated action, shared external forcing, and genuine coupled dynamics |
| Overload propagation | Load-redistribution cascade / cascading overload | Receiver load changes following sender/capacity changes across identified relations |
| Cascading degradation | Cascading failure; escalation only for an independently existing disruption | Direction of induced disruption versus aggravation of another disruption |
| Synchronized remediation | Unwanted synchronization applied to recovery actions | Action identities and cross-actor timing; planned coordination can be beneficial |
| Pathological feedback between reasonable controllers | Harmful controller interaction / destabilizing interaction cycle | Closed interaction loop and sustained effect; individual intent or local correctness is insufficient |

Sources for this interpretive crosswalk: [control research note](reliability-control-terminology.md), [distributed-behavior research note](reliability-distributed-behaviors.md), [dependability/cascade research note](reliability-dependability-cascades.md). In particular, the [Kubernetes HPA documentation](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) supplies autoscaling terminology, [AWS caching](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/) supplies the cache thundering-herd example, and [Google SRE](https://sre.google/sre-book/addressing-cascading-failures/) discusses load movement, overload, and recovery failure.

The fault/behavior distinction is useful but should not flatten the fault vocabulary either: saturation and exhaustion may be states or consequences; a configuration error can be a cause; a process crash can be a service failure at one boundary and a fault for a consumer. Preserve the role of each claim and its system boundary. [Avižienis et al.](https://www.landwehr.org/2004-aviz-laprie-randell.pdf)

## What a semantically meaningful symbol must preserve

Proposed synthesis: an episode should separate five dimensions rather than assert a single diagnosis.

1. **Observed form**: burst, repetition, phase alignment, spread, recovery, or persistent impairment.
2. **Relations**: which entities interact, dependency/action edges, temporal order and overlap, and uncertainty bounds.
3. **Mechanism hypothesis**: feedback, workload amplification, resource redistribution, shared cause, or controller conflict.
4. **Operating consequence**: useful work, latency, errors, capacity, and recovery behavior relative to an explicit reference.
5. **Evidence status**: directly observed, derived, hypothesized, contradicted, or unavailable; source references remain accessible.

Illustrative packet, not a dataset observation:

```text
interval: [t0, t3]
entities: caller-group A, service B
observed:
  original_request_rate: baseline again after t1
  attempts_per_logical_request: elevated through t3
  successful_completion_rate: depressed through t3
  queue_occupancy: elevated through t3
relations:
  timeout_events precede repeated_attempts within measured lag
  repeated_attempts target B
unknown:
  whether B's original capacity loss has ended
  whether retries are sufficient to sustain the degradation
provenance: references to metric intervals and matched request records
```

The LLM can operate on actors, ordering, persistence, work amplification, and missing evidence. It should not confidently conclude metastability in this example because the removal of the initial capacity disturbance is unknown. A single `RETRY_STORM` token would discard that distinction and may simply hand the model an answer.

Higher-level behavior labels are still permitted as hypotheses with explicit criteria and supporting evidence. The problem is treating them as established observations or evaluating their repetition as independent reasoning. A typed temporal graph or a small relational packet may serve this thesis better than a flat alphabet; that is a design hypothesis to test.

## A smaller test that addresses the actual thesis

Research question: **Can semantic compression preserve the distinctions an LLM needs to reason about one extended behavior, at substantially lower input size, without supplying the desired conclusion?**

Start with one contrast: a temporary overload followed by recovery versus persistent degradation maintained by retry feedback. Add a crucial lookalike: persistent degradation because the external capacity loss never ended. Similar peaks should not make these equivalent. Use controlled generation or instrumented reproduction with known causal conditions, not gold incident labels as behavioral annotations. Do not assume Track 1 contains these scenarios.

Separate the research assertions:

| Assertion | Isolated test | Failure evidence |
|---|---|---|
| Semantic adequacy | Independently author minimal factual packets from known episodes; test whether the distinguishing evidence is expressible, including the external-disturbance confounder | Different mechanisms become indistinguishable, or the packet requires a guessed behavior label |
| Compression fidelity | Derive packets from noisy multimodal observations; compare each relation/interval/unknown with the generator or independently annotated reference | Required relations disappear, false relations appear, or noise/missing data becomes unwarranted certainty |
| LLM usability | With fixed model and task, compare raw bounded telemetry, numerical summaries, and symbolic factual packets | The LLM cannot reconstruct the sequence, distinguish plausible mechanisms, or cite evidence from the symbols |
| Efficiency at retained meaning | Vary input budget and compare quality-versus-token curves, including packet definitions and metadata | Savings result only from losing required distinctions, or a simpler numerical summary dominates |

For the initial feasibility probe, test LLM usability with manually verified packets, explicitly as an upper bound on representation usefulness; it does not show that automatic encoding succeeds. Automatic compression fidelity is a separate gate. This avoids building an encoder and ranker before establishing that the intended semantic object is useful.

Use answer-free entity IDs and packet metadata. Include a relation-order shuffle, removal of the decisive retry/capacity evidence, and renamed entities as controls. The model should change or withhold its explanation when distinguishing evidence is removed. Supplying final class names defeats the recognition test. A non-LLM rule recognizer is a relevant comparator; successful deterministic recognition need not imply LLM value.

Score independently: event/actor identification, temporal relations, mechanism distinctions, uncertainty under missing evidence, supported versus invented claims, and actual input tokens. Keep reference answers separate from packet construction logic; fix variants before inspecting model outcomes. Model API dollars and runtime are measured only when calls are run. No such experiment was executed in this review.

## Hackathon boundary and unresolved questions

The benchmark supplies fault-event labels, not ground truth for every emergent behavior listed here. The [local trace audit](track-1-trace-audit.md) also reports unresolved status semantics, nonuniform instrumentation, and precision constraints. A raw span relation cannot simply become a trusted behavior symbol. Controller and retry observability must be demonstrated, not assumed.

For Track 1, the same representation principle can preserve observed latency propagation, recurrence, changes in workload, and cross-modal disagreement without asserting a controller pathology. Root-component recall remains a later application metric. For the longer research direction, obtain a corpus with controller actions, request lineage, workload movement, and recovery interventions when the selected behavior requires them.

Open questions: operational definition and observability of the chosen behavior; whether temporal relations survive useful compression; whether the LLM improves on direct recognition; whether evidence packets generalize across entity names and workloads; and whether sufficient novelty remains after comparison with chronicle recognition, CER, model-based diagnosis, and current AIOps/LLM telemetry-compression work. This review answers the taxonomy question, not those empirical questions.
