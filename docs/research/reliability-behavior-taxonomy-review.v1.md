# Existing taxonomies for reliability behaviors

## Targeted literature and standards review

**Research date:** September 17, 2026  
**Basis:** The supplied research handoff on Reliability Activity Recognition.  
**Version:** 1.  
**Finding:** Strong conceptual and methodological precedents; a narrower operational-integration gap remains a hypothesis.

The report contains the five requested deliverables. Source findings, proposed operationalization, and limitations are distinguished in the text. Bibliographic keys resolve to the source register. Recent preprints are not treated as standards, and incomplete source access is disclosed.

# Executive finding

**The broad framing is already occupied. Several explicit classifications cover important proposed behaviors, including a remarkably close emergent-misbehavior taxonomy sketch. No single validated, detector-ready taxonomy spanning all the requested behaviors was established by this review.**

Mogul's 2006 work explicitly proposes classifying emergent software misbehavior separately from its causes and using that classification for detection and diagnosis. It is the closest conceptual predecessor, but remains a research agenda and provisional classification rather than a completed operational standard. [MOG06]

More developed partial classifications supply useful structure. Metastable-failure research distinguishes triggers from self-sustaining mechanisms; Kivi classifies cluster-management property violations, including oscillation; and infrastructure-interdependency research distinguishes cascading, escalating, and common-cause failures. These go beyond naming broken components. [BRO21; HUA22; KIV24; RIN01]

The recognition architecture also has strong predecessors. Chronicle recognition represents temporally constrained symbolic scenarios, supports hierarchy, and has been applied to telecommunications supervision. Consequently, converting telemetry into symbolic events and recognizing composite situations cannot itself establish novelty. [DOU93; DOU07]

Most provisional behavior names should therefore become aliases for established concepts, not new taxonomy leaves. The defensible synthesis is a small, multi-label vocabulary that separates **observed temporal form, propagation or feedback mechanism, participating entities, and strength of causal evidence**. A common cause is a causal relationship, for example, whereas synchronization is a temporal relationship; treating them as sibling activities would obscure that distinction. [IEC; RIN01]

A narrower contribution remains plausible: interoperable, evidence-bound recognition definitions for established behaviors, evaluated continuously across heterogeneous telemetry and multiple systems. Such a contribution would require operational definitions, negative cases, onset/offset rules, and comparative evaluation. The sources reviewed do not establish that this exact combination is absent everywhere, nor that implementing it would require a new taxonomy.

For the brief's example, the most defensible description is **load-redistribution-induced cascading overload**. Synchronization, recurrent recovery, or metastability should be added only when separate evidence supports those qualifiers. [SRE16; MOT02; BRO21]

**Recommendation:** retain Reliability Activity Recognition as a working implementation name, while positioning the research as operationalizing established emergent-misbehavior, dependability, and temporal-recognition concepts. Do not claim discovery of a previously unclassified family of system phenomena.

---

# Taxonomy landscape

## Scope and evidence policy

This targeted review follows the supplied research handoff and covers publicly accessible material identified through September 17, 2026. Searches combined the brief's exact and related terminology with citation-following from close primary sources. All eleven requested literatures were screened. This is not a preregistered systematic review, and no claim of exhaustive database coverage is made.

The word **taxonomy** is reserved for author-presented classifications. A named operational catalog, formal state model, verification-property taxonomy, and recognition method have different reuse implications. Recent preprints and vendor catalogs are identified explicitly. A promising HAL controller-model report could not be inspected in full. [HAL25]

The dossiers distinguish source findings from proposed recognition requirements. **All passages headed Recognition implications are this review's operational interpretation**, unless a source expressly implements the indicated representation. A paper discussing a behavior does not automatically provide a detector for it.

## Comparison matrix

Temporal and interaction columns describe what the source represents, not a claim that every class has that property. Production evidence distinguishes incident-derived work from illustrative experience and theoretical examples. No relevance scores are assigned.

| Taxonomy / source | Domain | Primary unit | Fault vs behavior | Temporal structure | Multi-component | Controller interaction | Population / resources | Production-derived | Relevance |
|---|---|---|---|---|---|---|---|---|---|
| Mogul 2006 [MOG06] | Software systems | System behavior | Explicit behavior-taxonomy sketch | Regimes and cycles | Yes | Discussed | Contention and coordination | Illustrative experience | Closest framing precedent |
| Parunak and VanderBok 1997 [PAR97] | Distributed industrial control | Coupled control system | Behavior forms and causes | Fixed points, cycles, chaos | Yes | Yes | Shared capacity | Industrial examples and analysis | Direct dynamic predecessor |
| Bronson et al. 2021 [BRO21] | Distributed systems | Runtime regime | State/mechanism framework | Persistent bad state | Yes | Not a dedicated axis | Load and capacity | Operational examples | Metastability definition |
| Huang et al. 2022 [HUA22] | Distributed systems | Failure episode | Trigger/mechanism classification | Trigger and sustaining process | Yes | Not a dedicated axis | Amplification and capacity | Incident-derived | Strong empirical partial classification |
| Kivi 2024 [KIV24] | Cluster management | Property / execution | Property taxonomy | Safety and liveness | Yes | Explicit | Placement and replica state | Real issues plus model verification | Oscillation and controller conflicts |
| Chen et al. 2026 [CHE26] | Microservice management | Management approach | Research-system taxonomy | Dynamics modeled by approaches | Yes | Control locus is an axis | Explicit | Literature synthesis | Adjacent, not activity classes |
| Avizienis et al. 2004 [AVI04] | Dependability | System/component boundary | Fault, error, failure taxonomy | Propagation and recovery | Yes | Not central | Not central | Canonical synthesis | Semantic foundation |
| Rinaldi et al. 2001 [RIN01] | Critical infrastructure | Interdependent infrastructures | Failure/interdependency classification | Cascade, escalation, restoration | Yes | Not a loop taxonomy | Cross-network dependencies | Case-informed | Propagation and shared-cause vocabulary |
| RFC 2914 [RFC2914] | Networking | Congested traffic/system | Mechanism distinctions | Throughput collapse | Yes | Protocol feedback | Shared network capacity | Standards synthesis | Congestion-collapse specificity |
| RFC 2309 [RFC2309] | Networking | Flows sharing queues | Operational pattern vocabulary | Synchronization | Yes | TCP feedback | Shared queues | Standards synthesis | Historical synchronization precedent |
| Feedback Systems [AST08] | Control theory | Dynamical system | Formal vocabulary, not incident taxonomy | Transients and stability | Possible | Formal treatment | Application-dependent | Theory and examples | Precise control terminology |
| Computational ecosystems [KEP89] | Distributed resource allocation | Agent population | Formal dynamical regimes | Equilibria and instability | Yes | Decentralized adaptation | Central | Models and simulation | Technical ecology predecessor |
| Smith 2020 [SMI20] | Performance / cyber-physical systems | Antipattern instance | Named catalog, not taxonomy | Cascades and contention | Yes | Pattern-dependent | Central | Practitioner experience | Reusable performance patterns |
| Oppenheimer et al. 2003 [OPP03] | Internet services | Failure/incident | Cause-oriented classification | Incident and recovery records | Service scope | Not a dedicated axis | Limited | Three production services | Contrast with behavior classification |
| RFC 3877 [RFC3877] | Network management | Alarm/resource | Alarm model and attributes | Active/clear lifecycle | Correlation requires more | No dedicated axis | Resource identifiers | Standard | Low-level normalization |
| Lineage-driven fault injection [LDF15] | Distributed testing | Execution and fault combination | Testing method | Execution histories | Yes | Not a behavior taxonomy | Application-dependent | Experimental evaluation | Constructing discriminating tests |
| Chaos review [CHA25] | Resilience testing | Platform/approach | Tool taxonomy | Experiments | Platform-dependent | Not behavior classes | Platform-dependent | Literature review | Prevent taxonomy-unit confusion |
| Chronicle recognition [DOU93; DOU07] | AI / telecommunications | Temporal scenario | Recognition formalism | Constraints and hierarchy | Via bound events | Representable, not predefined | Representable, not predefined | Telecom applications | Strong architecture precedent |
| Frequent episodes [MAN97] | Event mining | Event pattern | Pattern formalism | Partial orders and windows | Via event attributes | Not predefined | Not predefined | Telecom alarm application | Discovery without causal guarantees |
| Eadro [EAD23] | AIOps | Service/dependency graph | Troubleshooting method | Telemetry analysis | Yes | Not a dedicated axis | Performance data | Benchmark experiments | Multimodal-fusion precedent |
| HAR review [AGG11] | Activity analysis | Activity / recognition approach | Activity vocabulary and method taxonomy | Hierarchical activity | Human interactions/groups | Not applicable | Not applicable | Research synthesis | Structural analogy only |
| StackGen 2026 [STA26] | Operational SRE | Failure mode | Vendor taxonomy/catalog | Some recovery sequences | Yes | Some named patterns | Explicit | Vendor claims incident basis | Competing operational vocabulary |

## 1. Distributed systems and cloud reliability

### Emergent software misbehavior

**Mogul, 2006.** The proposed behavior classes are thrashing, unwanted synchronization, unwanted oscillation or periodicity, deadlock, livelock, phase change, and chaotic behavior. Causes are classified separately. The unit is system behavior; the formalism is a provisional prose classification supported by examples, not an annotated corpus. [MOG06]

**Recognition implications.** Reuse the separation between behavior and cause. Treat class membership as multi-label and evidence-dependent. A recurrent service-health pattern alone does not determine which interaction produced it. The paper supplies conceptual coverage, not reusable onset thresholds or detector contracts.

### Metastable failures

**Bronson et al., 2021; Huang et al., 2022.** The earlier framework distinguishes stable, vulnerable, and metastable regimes. In the classic formulation, a trigger can disappear while a sustaining mechanism keeps the system in a bad state. The later study examines 22 failures across 11 organizations and cross-classifies load-spike/capacity-reduction triggers against workload-amplification/capacity-degradation sustaining mechanisms. The selected incidents are not a prevalence sample. [BRO21; HUA22]

**Recognition implications.** This is a directly reusable mechanism framework, with episodes and runtime states as its units. A recognizer would need useful throughput, incoming and internally generated work, effective capacity, trigger timing, and evidence about persistence. A long outage is not sufficient; the sustaining mechanism matters. Use its dimensions instead of making every named retry or cache incident a separate top-level species.

### Incident causes and production pattern catalogs

**Oppenheimer et al., 2003** classifies failures in three production Internet services by causes and affected elements, including operator, software, hardware, and network factors. It distinguishes component failures from failures visible at service level. This supports the observation that some incident classifications are cause-centered, not the stronger claim that dependability literature stops there. [OPP03]

**Google SRE's cascading-failure chapter** is a practitioner account of operational mechanisms, including redistribution onto already stressed replicas and recovery attempts that encounter overload again. Its unit is the service and its interacting dependencies; its form is explanatory scenarios, not an author-declared taxonomy. [SRE16]

**Recognition implications.** Keep an incident's initiating cause, affected scope, observed behavior, and outcome in separate fields. Use SRE scenarios as test cases; do not promote an explanatory chapter into a validated ontology.

## 2. Kubernetes, autonomic management, and interacting controllers

### Kivi's property taxonomy

**Liu et al., 2024.** Kivi presents four property categories: unexpected topology, unexpected object numbers, unexpected object lifecycles, and oscillation. The first three concern safety; oscillation concerns liveness. Categories can overlap. It models cluster-management state and actions, including a descheduler/deployment-controller/scheduler interaction that repeatedly undoes its own effects. Its empirical basis combines real issues with model-based verification. [KIV24]

**Recognition implications.** Reuse the distinction between a bad configuration/state and a nonconverging execution. Runtime evidence would include reconciliation actions, object versions, placements, desired states, and repeated transitions. A bounded observed cycle can justify an oscillation alert; it does not prove infinite nonconvergence. The taxonomy classifies properties, not every operational incident phenotype.

### Separating single-loop instability from composition problems

**Ford, 2012** gives an explicitly simplified, hypothetical interaction between load balancing and power optimization. Loops whose independent operation is reasonable can destabilize their composition. This is explanatory evidence for the mechanism, not a measured production incident or a comprehensive taxonomy. [FOR12]

The **Kubernetes HPA documentation** uses flapping for repeated scaling near a target and describes stabilization. That is a single-controller example, so it should not be relabeled controller interference without evidence of another interacting loop. [HPA]

**Recognition implications.** Record which control actions respond to which measurements. Distinguish a controller reacting to external workload oscillation from controllers inducing the oscillation themselves. Neither simultaneous actions nor matching periods, alone, establishes interference.

### Recent adjacent classifications

**Chen et al., 2026** is an explicit taxonomy of microservice-management approaches, organized around control locus, modeled dynamics, adaptation strategy, and evaluation evidence. Its unit is the research/management approach, not a detected reliability activity. Reuse its characterization dimensions, not its approach categories as incident labels. It is a preprint. [CHE26]

**Farahbakhsh et al., 2026** develops a formal account of destabilizing cycles involving individually stabilizing components, with examples beyond the earlier overload-centered metastability framing. It is an important recent conceptual falsifier but remains a preprint, not a mature operational taxonomy. [FAR26]

**An and Potop-Butucaru, 2025** is a high-priority unresolved lead on multi-controller cloud management. Only accessible metadata and abstract were examined; the source's detailed failure classes cannot responsibly be reconstructed here. [HAL25]

## 3. Control theory and distributed industrial control

### Dynamical forms versus their causes

**Parunak and VanderBok, 1997** separates fixed-point, oscillatory, and chaotic forms from contributing capacity limits, feedback loops, and temporal delays. Industrial examples include synchronized controllers competing for a recovered resource and repeated shutdown/restart behavior. This is a technical predecessor to both the ecology framing and recurring-recovery examples, not merely an analogy. The work uses industrial observations, models, and dynamical analysis. [PAR97]

**Recognition implications.** Transfer the distinction between the observed regime and its explanation. An equilibrium can be operationally unacceptable; repeated changes need not represent progress. Do not infer mathematical chaos from noisy or unpredictable telemetry.

### Formal control vocabulary

**Astrom and Murray, 2008** supplies formal dynamical-system terminology rather than an incident catalog. Oscillation, transient overshoot, instability, saturation, and integral windup concern different properties and mechanisms; they are not interchangeable labels. [AST08]

**Recognition implications.** For a control-specific claim, the relevant evidence may include reference values, sampled measurements, commanded and actual actuation, delays, saturation limits, and controller memory. Calling replica-count fluctuation a limit cycle or windup episode requires more than visual resemblance. Use descriptive oscillation first; assign the stronger mechanism only when an appropriate model or instrumentation supports it.

## 4. Queueing, congestion, and networking

**RFC 2914** distinguishes congestion-collapse mechanisms, including unnecessary retransmission and traffic that consumes network resources without reaching its destination. The relevant unit is useful delivery across interacting senders and network resources, not an isolated full queue. **RFC 2309** describes global synchronization in congestion control. It is a historical vocabulary source, not current queue-management guidance, having been obsoleted in 2015. [RFC2914; RFC2309]

**Recognition implications.** Compare offered work with useful completed work, and distinguish synchronization from average load. To map retries onto network-collapse reasoning, preserve the difference between original requests, attempts, completions, and discarded work. A high-utilization destination may be healthy; low goodput despite increasing offered work is materially different.

**Brooker's retry/backoff account** documents operational workload amplification and the importance of desynchronizing retries. It is a concrete pattern/mechanism source, not a taxonomy. [AWS]

## 5. Dependable and fault-tolerant computing

### Fault, error, failure, propagation, and recovery

**Avizienis et al., 2004** is a canonical taxonomy whose scope is broader than component faults. Fault/error/failure distinctions depend on system boundaries, and the paper explicitly addresses propagation between components and recovery. Its formalism includes taxonomic dimensions and causal/propagation diagrams; its basis is foundational synthesis. It does not provide a ready-made catalog of all the proposed cloud activity classes. [AVI04]

**Recognition implications.** Reuse the terms as semantic types and boundary annotations. A failed dependency may act as a fault for the consuming service. The same observation can have different roles at different boundaries, so a universal one-label-per-signal hierarchy is inappropriate. Record the boundary at which service delivery is judged.

### Shared causes, shared modes, and alarms

The **IEC dependability vocabulary** distinguishes common-cause failures from common-mode failures. The former concerns a shared cause; the latter concerns a shared failure mode, which need not imply an identical cause. Mere correlation proves neither. These are relationship classifications, not necessarily temporal trajectories. [IEC]

**RFC 3877** provides a standardized alarm model with resource identity, state/severity information, and lifecycle changes. It supports event normalization, not an ontology of multi-stage reliability behavior. [RFC3877]

**Recognition implications.** Preserve common-cause hypotheses separately from observed co-failure. An alarm's activation and clearing can become low-level evidence, but alarms should not automatically define the start and end of an incident or prove recovery.

## 6. Complex systems, interdependencies, and resilience

### Failure relations across infrastructures

**Rinaldi et al., 2001** distinguishes cascading failure, escalating failure, and common-cause failure. A cascade produces disruption in another infrastructure; escalation worsens a separate existing disruption; a common cause affects multiple infrastructures. The framework additionally describes interdependencies and operating conditions, including restoration. Its dimensions are not a strict hierarchy. It is case-informed and cross-infrastructure, not a cloud telemetry benchmark. [RIN01]

**Recognition implications.** Adapt these distinctions to services only after defining the dependency and failure boundary. A downstream failure, an already impaired service becoming worse, and parallel co-failure deserve different relation labels. Restoration is a system condition, not proof of successful recovery.

### Overload from redistribution

**Motter and Lai, 2002** models load redistribution after a node is lost and the resulting overload cascade. The evidence is a mathematical network model and simulation. It supports the mechanism vocabulary for displaced work overwhelming destinations; it does not establish that its particular graph-load assumptions fit a cloud deployment. [MOT02]

**Recognition implications.** Reuse the causal hypothesis, then test it against measured placement and traffic changes. A topology edge is not automatically a workload-transfer edge; dependency, scheduling, routing, and shared-resource relations should remain distinct.

## 7. Population dynamics and ecology-inspired computing

**Kephart, Hogg, and Huberman, 1989** develops computational ecosystems as a formal model of distributed resource allocation. Agent populations choose resources using imperfect or delayed information, producing dynamical regimes analyzed through models and simulation. This is a substantive predecessor to ecology-inspired reliability reasoning. It is not a catalog of production incident activities. [KEP89]

**Recognition implications.** Use a population model only where its state variables can be identified: workload populations, resource choices, occupancy, delays, and response rules. A shared-resource model may explain coordinated migration, but migration alone does not justify predator-prey, carrying-capacity, or ecological-collapse terminology. The test is model fit and predictive discrimination, not the attractiveness of the analogy.

## 8. Performance engineering and antipatterns

**Smith, 2020** presents named cyber-physical performance antipatterns, including Falling Dominoes and Museum Checkroom. The former links one failure to subsequent performance failures; the latter concerns problematic resource-pool use. Crucially, the paper states that it introduces antipatterns without classifying them. Calling this a taxonomy would misrepresent its claim. Its basis is performance-engineering experience and modeling, not a labeled activity-recognition dataset. [SMI20]

**Recognition implications.** Reuse a pattern only with its specific mechanism and participating resources. For contention-related candidates, instrument acquisition/release, waiting, ownership, and useful progress where possible. A resource-pool exhaustion symptom does not by itself distinguish leakage, excessive demand, deadlock, or displaced-load overload.

## 9. Chaos engineering and resilience testing

**Lineage-driven fault injection, 2015** uses successful-execution provenance to find combinations of faults that defeat desired outcomes. It represents interacting failure scenarios rather than merely listing individual injected faults, but it does not supply a general vocabulary of resulting behavior. Its formalism is lineage/constraint reasoning over executions. [LDF15]

The **2025 chaos-engineering review** presents a taxonomy of platforms and capabilities. The classified unit is the testing approach, not the system's temporal response. This distinction matters when assessing apparent matches for failure-scenario taxonomies. [CHA25]

**Recognition implications.** Use fault injection to generate and distinguish candidate behaviors, not to define them by the injected trigger. The same intervention should be allowed to yield different episodes; different interventions may yield the same pattern. Test design must preserve this many-to-many relation.

## 10. AIOps, observability, and temporal event analysis

### Multisource troubleshooting

**Eadro, 2023** combines logs, performance indicators, and distributed traces with service dependencies for anomaly detection and localization. It demonstrates that multi-source troubleshooting is already an established research direction. It does not present a reusable named taxonomy of temporal reliability activities. Its reported evaluation uses microservice-system experiments. [EAD23]

**Recognition implications.** Compare an explicit pattern layer against direct multisource troubleshooting. Explanation benefits cannot be assumed from symbolic intermediate labels; they must be measured. A localization score should not be relabeled causal certainty.

### Chronicle recognition and episode mining

**Dousson and colleagues, 1993 and 2007** represent situations as symbolic events constrained in time, with hierarchical recognition and telecommunications applications. This directly precedes the proposed observation-to-composite-activity architecture. A chronicle is a recognition specification, not an infrastructure behavior category supplied in advance. [DOU93; DOU07]

**Mannila, Toivonen, and Verkamo, 1997** mines frequent episodes: partially ordered event collections occurring within temporal windows, including telecommunications alarm applications. Its episode is a pattern occurrence, not necessarily a complete bounded incident. Frequency and ordering do not establish causality. [MAN97]

**Recognition implications.** Reuse partial ordering, entity binding, event-time constraints, and hierarchical composition. Preserve alternative explanations when the same sequence matches several mechanisms. Add missing-data and late-arrival behavior explicitly rather than treating absent observations as absent events.

## 11. Human activity recognition and symbolic time-series methods

**Aggarwal and Ryoo, 2011** distinguishes activity concepts such as gestures, actions, interactions, and group activities, while also classifying recognition approaches. The distinction between domain vocabulary and method taxonomy must be preserved. It does not establish the brief's exact six-level infrastructure hierarchy. [AGG11]

**Stiefmeier, Roggen, and Troster, 2007** is a methodological precedent for fusing symbolically represented sensor information in continuous activity recognition. It is not a source of reliability classes. [STI07]

**Recognition implications.** Transfer continuous segmentation, composite-pattern recognition, and multimodal evidence handling as candidate methods. Do not import a human activity ontology or assume every incident has a single nonoverlapping label and clean boundaries.

## A contemporary competing operational catalog

**StackGen, June 2026** explicitly offers an SRE failure-mode taxonomy spanning several families, with named entries including autoscaling pathology and phased data recovery. It is relevant because it is an existing operational classification rather than simply a component-fault list. However, it mixes mechanisms, symptoms, and process concerns. Its claimed empirical coverage and automation benefits were not independently verified here. [STA26]

This should be screened as competing prior art and a vocabulary source, not treated as a scientific standard. The vendor's detailed methodology and any reusable machine-readable definitions require further inspection. Its existence weakens an unqualified claim that operational recovery patterns have no prior catalogs.

---

# Crosswalk from provisional concepts to existing terminology

The preferred terms below name the narrowest behavior or relationship supported by the evidence. They are not assertions that every provisional phrase is an exact synonym. Recognition evidence and label recommendations are this review's synthesis.

| Provisional concept | Existing term(s) | Discipline | Canonical source | Same concept? | Important distinction and label decision |
|---|---|---|---|---|---|
| A. Synchronized migration / failover | Unwanted synchronization; synchronized failover as a descriptive qualifier; load-redistribution cascade when secondary failures occur | Distributed systems; industrial control; reliability | [MOG06; PAR97; SRE16] | Partial | Timing alignment, workload movement, and secondary overload are separate claims. Keep synchronized failover as an alias when justified; do not make failover stampede a new top-level class. |
| B. Retry amplification | Workload amplification; retry storm; positive-feedback overload | Distributed systems; networking | [HUA22; AWS; RFC2914] | Close for amplification | Increased attempts per original request establishes amplification; a storm adds intensity or synchronization. Metastability additionally requires a sustaining regime in the chosen formalism. Replace a new class with the established mechanism plus qualifiers. |
| C. Repeated recovery and immediate relapse | Flapping; recurrent failure; oscillatory recovery | Cloud control; distributed control | [HPA; PAR97; SRE16] | Partial | Alternating reported health can differ from true service recovery. Hysteresis failure and limit cycle assert mechanisms or mathematical properties that need additional evidence. Use recovery/re-failure cycle descriptively. |
| D. Coupled-controller oscillation | Oscillation; interacting-control-loop instability; nonconverging reconciliation | Cluster management; control | [KIV24; FOR12; AST08] | Close if control actions sustain it | Single-controller tuning, externally oscillating demand, and mutually opposing controllers are different explanations. Keep coupled-controller oscillation only after identifying the loops and their interaction. |
| E. Shared-fate collapse | Common-cause failure; shared-dependency failure; correlated co-failure when causality is unknown | Dependability; infrastructure interdependency | [IEC; AVI04; RIN01] | Partial | Common mode is not the same as common cause. Shared fate is an informal umbrella, not a demonstrated mechanism. Replace collapse with the actual impact and relation. |
| F. Resource-pool exhaustion after displacement | Load-redistribution-induced cascading overload; overload cascade | Network resilience; SRE | [MOT02; SRE16] | Close if displaced work causes secondary failure | Resource depletion alone does not show propagation. Congestion collapse additionally concerns useful throughput. Prefer cascading overload over a new ecological label. |
| G. Cascading degradation across dependencies | Failure propagation; cascading failure; escalating failure in the narrower pre-existing-disruption case | Dependability; critical infrastructure | [AVI04; RIN01] | Close with boundary qualifications | Propagated latency need not yet violate service requirements. Escalation concerns worsening a disruption already present elsewhere. Preserve the failure/degradation distinction. |

## Applying the crosswalk without overclaiming

**A and F should not be merged.** Simultaneous failover can be absorbed successfully; an overload cascade can arise from sequential, unsynchronized redistribution. The first is a temporal-coordination property; the second names a propagation mechanism. The same incident can exhibit both.

**B and D should not be merged.** A monotonically growing retry feedback loop is not necessarily oscillatory. Conversely, two controllers can oscillate without any request retries. The shared abstraction is feedback, not an identical activity.

**C needs a recovery criterion.** A health check becoming green, a process restarting, a queue draining, and successful end-user service are different observations. The episode should state which criterion was met and for how long before relapse.

**E needs a causal-evidence boundary.** Simultaneous failures support a co-failure description. A confirmed shared dependency or intervention supplies stronger evidence for a common cause. Until then, store the common-cause explanation as a hypothesis rather than converting correlation into a fact.

These distinctions follow the source separation among temporal form, interaction, and causal mechanism; the proposed annotation policy is this review's synthesis. [PAR97; RIN01; IEC]

## Vocabulary to retain, restrict, or retire

Retain **cascading failure, failure propagation, workload amplification, oscillation, synchronization, flapping, and common-cause failure**, with explicit operational meanings appropriate to the deployment.

Restrict **metastability, limit cycle, chaos, integral windup, congestion collapse, and controller interference** to cases where their defining conditions are evidenced. They are explanatory commitments, not vivid substitutes for prolonged failure or noisy telemetry. [BRO21; AST08; RFC2914]

Retire **failover stampede, concentration cascade, shared-fate collapse, and hysteresis failure** as proposed scientific categories unless later review uncovers a precise established definition. They may remain user-facing aliases, but should resolve to clearer underlying annotations. Reliability Ecologist is a persona or framing; it is not a demonstrated new field. [KEP89; PAR97]

---

# Candidate synthesis

## Design decision

**Use a small faceted vocabulary rather than a new six-level taxonomy.** The minimum useful representation separates the observed pattern from its proposed mechanism, identifies the participating entities and relations, and records how strongly the evidence supports each claim.

This is a proposed synthesis. It is not presented as a classification already standardized by one of the cited sources. The constituent ideas have substantial precedent; the proposed combination and operational contract would need empirical validation.

## Minimal behavior and relation vocabulary

Established means a category or distinction is directly supported by an existing source classification. Adapted means a concept is transferred into the proposed infrastructure-recognition setting. Synthesized means this review combines prior structures. No behavioral leaf is labeled potentially new.

| Category or dimension | Status | Source support | Proposed operational use |
|---|---|---|---|
| Unwanted synchronization | Established | Mogul's proposed behavior classification; industrial-control forms [MOG06; PAR97] | Detect aligned actions or transitions across entities; separately record whether alignment is harmful. |
| Oscillation / nonconverging behavior | Established | Distributed-control classification and Kivi property taxonomy [PAR97; KIV24] | Record recurring state/action patterns; keep controller involvement as a separate attribute. |
| Cascading, escalating, common-cause relations | Established | Interdependent-infrastructure failure classification [RIN01] | Distinguish newly induced failure, worsening of a pre-existing disruption, and shared cause. |
| Applying those relations to service/workload telemetry | Adapted | Dependability propagation plus interdependency vocabulary [AVI04; RIN01] | Bind the relation to explicit service boundaries and typed edges. |
| Workload amplification / capacity-degradation amplification | Established | Metastable-failure mechanism classification [HUA22] | Distinguish more work being generated from less useful capacity being available. |
| Stable / vulnerable / metastable regime | Established | Distributed-systems metastability framework [BRO21] | Apply only under a specified model, not as a generic severity or duration label. |
| Recurrence and recovery/re-failure temporal qualifiers | Adapted | Industrial-control cycles, HPA flapping, and SRE recovery scenarios [PAR97; HPA; SRE16] | Attach recurrence to an explicitly stated recovery criterion. |
| Evidence-bound temporal pattern and episode record | Synthesized | Chronicle representation, episode mining, and dependability boundaries [DOU07; MAN97; AVI04] | Combine observations, entity bindings, temporal constraints, alternatives, and evidence status. |

Thrashing, deadlock, livelock, and phase-transition vocabulary remain available from the broader literature. They need not be implemented in an initial recognizer focused on the seven requested candidates. Deliberately limiting scope is preferable to implying exhaustive coverage. [MOG06]

## Orthogonal facets

The proposed core record has five independent facets.

**Observed temporal form** describes what the evidence directly shows: an ordered progression, aligned transitions, repeated alternation, or persistence. Multiple forms may apply. No mechanism is implied merely by a visually recognizable pattern.

**Mechanism hypothesis** identifies dependency propagation, displaced-load overload, workload amplification, reduced effective capacity, control interaction, or shared cause. A record can retain competing mechanisms and explicitly state that some remain untested.

**Scope and relation structure** identifies services, resources, requests, controllers, and workload populations. Edges are typed: invokes, depends on, controls, scheduled onto, shares capacity with, or transfers load to. This is an implementation proposal; a service-call graph alone may omit the relation needed for the explanation.

**Regime and outcome** separates local state from service consequences and recovery status. An episode may enter and leave several regimes. Recovered capacity, reported health, and recovered service should not be interchangeable fields.

**Evidence status** distinguishes observed, inferred, model-supported, and intervention-supported claims. These proposed statuses are not calibrated probabilities. Their purpose is to expose the inferential step, including missing telemetry or incompatible explanations.

The justification for separating these facets is the mismatch among existing classification units: forms versus causes, properties versus executions, and temporal patterns versus complete incidents. [PAR97; KIV24; MAN97]

## Minimum recognition contract

A reusable pattern definition should include a canonical term and source, participant types, required event/metric predicates, permissible temporal order, onset and termination rules, and explicit disqualifiers. It should also specify missing-data behavior, the allowed causal conclusion, and the evidence retained for review.

An instance should bind that definition to actual entities and timestamps. It should retain the observations that support the match, identify which requirements were not observed, and distinguish an incomplete match from a contradicted one. These are proposed engineering requirements, not claims that the reviewed sources already provide an interoperable format.

For continuous recognition, use provisional and completed matches. A pattern detected early should be revisable when later data changes its interpretation. Avoid declaring a complete incident merely because a sliding window ended. Overlapping patterns and episodes should be representable without forcing a single label.

## Testing the proposed six-level hierarchy

| Proposed level | Precedent and alternative terminology | Contradiction or collapse | Finding |
|---|---|---|---|
| 0. Observation | Timestamped symbolic events, sensor signals, alarms [DOU93; RFC3877; STI07] | A span or log line can already summarize a composite action; rawness is relative. | Established ingredient, not a universal bottom level. |
| 1. Local state | Alarm state and system state [RFC3877; AVI04] | Retry burst, one of the brief's examples, is already temporal behavior rather than an instantaneous state. | Established concept; the proposed boundary needs revision. |
| 2. Component behavior | State evolution and activity recognition [PAR97; AGG11] | The component boundary changes what counts as fault, error, or failure; one controller can oscillate. | Defensible scope annotation, not a mandatory abstraction tier. |
| 3. Interaction behavior | Propagation and interdependency relations [AVI04; RIN01] | Interaction is a relation structure, not necessarily a higher level of temporal complexity. | Established phenomenon; its placement in a ladder is inferential. |
| 4. Population/control behavior | Computational populations and cluster-control properties [KEP89; KIV24] | Control can be local; population behavior can be simple. Scale and control role are different axes. | Split into orthogonal scope and control facets. |
| 5. Reliability episode | Temporal situations and frequent episodes [DOU07; MAN97] | A mined episode can be a short partial-order pattern, not an entire incident. Patterns can overlap or recur within one incident. | Useful grouping convention; the complete-incident meaning is synthesized. |

The supported structural model is therefore **typed observations and states -> compositional temporal patterns -> episode grouping**, with participant scope and causal explanation represented separately. Even that is a proposed architecture rather than a newly discovered hierarchy. Chronicle recognition already provides strong precedent for symbolic temporal composition. [DOU07]

## Worked recognition example

The brief supplies:

> degradation -> migration -> destination saturation -> secondary failure

The initial annotation should be **an observed displacement-and-overload sequence**, with **load-redistribution-induced cascading overload** as the candidate mechanism. To promote that hypothesis, the record needs evidence that work left the original location, arrived at the destination, increased the relevant demand, and contributed to secondary service failure.

A false-positive control should include the same sequence when an independent destination fault, unrelated batch workload, or measurement delay explains the saturation. Another control should show successful redistribution with temporary high utilization but no failed service. These are proposed test cases, not incidents reported by the source papers.

Add synchronized only if the migrations are temporally aligned across relevant actors. Add recurrent recovery if an explicitly measured recovery repeatedly reverses. Add metastable only if the selected metastability definition is met, including the sustaining mechanism in the classic framework. [BRO21; MOT02]

No new behavior class is required to describe this example. The potentially valuable work is making the distinction between those claims reproducible from incomplete operational evidence.

---

# Research gaps and falsifiers

## What is already occupied

The strongest conceptual falsifier is **Mogul's emergent-misbehavior agenda**. The separation between classifying behaviors and classifying causes, followed by detection and diagnosis, substantially overlaps the proposed research framing. [MOG06]

The strongest domain-specific falsifiers are **metastable-failure classification**, **Kivi's cluster-management properties**, and **interdependency failure categories**. Together they cover sustaining amplification, oscillation, propagation, and common-cause relationships. They cannot honestly be summarized as component-fault lists. [HUA22; KIV24; RIN01]

The strongest methodological falsifier is **chronicle recognition**, reinforced by **frequent-episode mining**. Hierarchical symbolic temporal recognition and recurring patterns in operational alarm streams predate the proposed HAR-to-infrastructure transfer. **Eadro** additionally establishes multisource telemetry troubleshooting as existing work. [DOU93; DOU07; MAN97; EAD23]

Finally, formal **computational ecosystems** and industrial distributed-control research substantially predate the Reliability Ecologist framing. Ecology and population dynamics are available technical traditions, not newly discovered analogies. [KEP89; PAR97]

## Where narrower classifications stop short

Cause-centered production studies such as Oppenheimer et al. do not directly furnish an activity vocabulary. Alarm standards define resource events and lifecycle state, not complete multicomponent trajectories. A platform taxonomy in a chaos review classifies test capabilities rather than the behavior being tested. These are genuine scope limits, not evidence that the broader literature lacks behavior classifications. [OPP03; RFC3877; CHA25]

Other apparent matches stop short for different reasons. Kivi's unit is a property and execution model; Eadro's is a troubleshooting representation; HAR supplies another domain's activity concepts. A complete comparison must therefore ask what is classified, not merely whether the source uses the word taxonomy. [KIV24; EAD23; AGG11]

## The narrower gap that remains plausible

The review did not establish a single widely adopted package combining a cross-system behavior vocabulary, explicit online recognition definitions, heterogeneous telemetry bindings, and an evaluation corpus with alternative explanations. That is a bounded search finding, not proof of worldwide absence.

A promising contribution would be **operational compatibility and empirical discrimination**: giving several established concepts consistent evidence requirements and showing when those definitions distinguish look-alike incidents. It might be achievable by extending an existing event/chronicle framework rather than proposing a new taxonomy.

The phrase unified taxonomy is itself questionable here. Common cause, oscillation, amplification, and metastability occupy different semantic roles. A faceted schema may be more defensible than forcing them into an exhaustive single-parent hierarchy.

## Explicit falsification tests

| Proposed claim | Evidence that would falsify or materially weaken it | Present assessment |
|---|---|---|
| Nobody has classified emergent reliability behavior. | A prior behavior classification distinguished from causes. | Already contradicted by Mogul and earlier distributed-control work. [MOG06; PAR97] |
| Symbolic temporal recognition is new to infrastructure monitoring. | Prior online temporal-scenario recognition over operational events. | Already contradicted by chronicle recognition and telecom applications. [DOU93; DOU07] |
| Multi-controller instability is an unclassified gap. | Existing controller-conflict/property classifications and formal models. | Strongly weakened by Kivi; recent controller-model work needs deeper examination. [KIV24; FAR26; HAL25] |
| No deployable cross-domain recognition catalog exists. | A prior library with behavior semantics, input bindings, temporal rules, and comparable evaluations. | Not established either way. Search named-pattern libraries, telecom event-correlation systems, and standards profiles more deeply. |
| The proposed layer improves root-cause reasoning. | A baseline using original telemetry or ordinary event correlation matches its accuracy and cost. | Entirely empirical; no benefit has yet been demonstrated here. |
| A new taxonomy is necessary. | An existing taxonomy plus orthogonal annotations produces consistent labeling and useful discrimination. | Existing partial classifications make this a serious alternative. |
| Ecology-inspired modeling adds predictive value. | A simpler queueing/control/dependency model explains the same cases equally well. | Must be tested; metaphor is insufficient. |

## Priority areas for deeper review

**Complete the direct-predecessor citation chain.** Follow forward citations of Mogul and Parunak, especially tools that implemented generic misbehavior detection, software performance diagnosis, and production event correlation. The central uncertainty is whether the proposed operational catalog was developed elsewhere, not whether the research question had previously been asked. [MOG06; PAR97]

**Inspect the multi-controller report and recent formal work.** The HAL report was not available in full during this review, and the June 2026 metastability preprint could change the boundaries between controller oscillation and broader metastability. The detailed classifications and assumptions need direct inspection before declaring an open gap there. [HAL25; FAR26]

**Examine operational correlation libraries and recovery catalogs.** Telecommunications and enterprise event management may contain reusable chronicle/rule libraries beyond the academic recognition papers. The current StackGen catalog also merits a methods-level comparison, particularly its recovery categories. This review establishes those as leads, not as validated complete solutions. [DOU07; STA26]

**Deepen queueing and scheduling coverage.** Convoys, thrashing, bottleneck shifts, incast, cache stampedes, and load-balancing instability may require specialized operational definitions. This review found enough precedent to reject broad novelty, but not a single authoritative catalog that unifies those mechanisms.

**Separate normal adaptation from failure.** A production detector must reject harmless synchronization, healthy failover, transient scaling adjustments, and overload that resolves normally. Prior naming of a mechanism does not supply the deployment-specific boundary between adaptation and unacceptable service.

## Empirical study worth doing

Start with a limited set of established candidates: displaced-load overload, retry amplification, recurrent recovery, and interacting-controller oscillation. For each, construct cases with different triggers and look-alike cases with different mechanisms. Include successful adaptation as a negative case.

Label the observed sequence independently of the causal explanation. Ask independent reviewers to annotate participant bindings, onset and offset, recovery criteria, and unresolved alternatives. Evaluate agreement before claiming the proposed schema is a reliable taxonomy.

Measure event-level and episode-level precision/recall, onset delay, fragmentation, duplicate alerts, and boundary error. Separately measure explanation correctness and the frequency of unsupported causal claims. Report behavior under missing modalities and late or misaligned timestamps.

Compare an explicit pattern layer against simple threshold/rule baselines, temporal event-pattern baselines, and a direct multisource troubleshooting approach. Evaluate the same upstream evidence budget where possible. Measure whether the intermediate representation improves analyst decisions, causal discrimination, or cost rather than assuming that a symbolic label is useful by itself. [DOU07; MAN97; EAD23]

These are proposed evaluation criteria. The literature review has not produced a dataset, tested a recognizer, established detector performance, or validated the hackathon data's observability sufficiency.

## Final answer to the brief's test

**Degradation followed by workload migration, destination saturation, and secondary failure is most naturally described as load-redistribution-induced cascading overload.** It belongs to established cascade/propagation vocabulary, with an overload mechanism supported by SRE scenarios and network-load models. [SRE16; MOT02]

What may be missing is not the name of the behavior. It is a portable and empirically tested rule for deciding, from the available evidence, whether that mechanism occurred, when its episode began and ended, and which competing explanations remain plausible.

## Source register

**[MOG06]** Jeffrey C. Mogul. **Emergent (Mis)behavior vs. Complex Software Systems.** EuroSys, 2006, pp. 293-304. [Publication record](https://research.google/pubs/emergent-misbehavior-vs-complex-software-systems/). The full text reviewed was the author-posted technical-report version, HPL-2006-2, internally dated December 22, 2005: [author full text](https://www.researchgate.net/profile/Jeffrey-Mogul-2/publication/221351778_Emergent_Mis_behavior_vs_Complex_Software_Systems/links/0046353a2820ee859a000000/Emergent-Mis-behavior-vs-Complex-Software-Systems.pdf).

**[BRO21]** Nathan Bronson, Abutalib Aghayev, Aleksey Charapko, and Timothy Zhu. **Metastable Failures in Distributed Systems.** HotOS, 2021, pp. 221-227. DOI: 10.1145/3458336.3465286. [Full text](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf).

**[HUA22]** Lexiang Huang, Matthew Magnusson, Abishek Bangalore Muralikrishna, Salman Estyak, Rebecca Isaacs, Abutalib Aghayev, Timothy Zhu, and Aleksey Charapko. **Metastable Failures in the Wild.** OSDI, 2022, pp. 73-90. [Publication and paper](https://www.usenix.org/conference/osdi22/presentation/huang-lexiang).

**[KIV24]** Bingzhe Liu, Gangmuk Lim, Ryan Beckett, and P. Brighten Godfrey. **Kivi: Verification for Cluster Management.** USENIX ATC, 2024, pp. 509-527. [Publication and paper](https://www.usenix.org/conference/atc24/presentation/liu-bingzhe).

**[RIN01]** Steven M. Rinaldi, James P. Peerenboom, and Terrence K. Kelly. **Identifying, Understanding, and Analyzing Critical Infrastructure Interdependencies.** IEEE Control Systems Magazine 21(6), 2001, pp. 11-25. [Publisher record](https://ieeexplore.ieee.org/document/969131). [Author-posted full text](https://www.researchgate.net/profile/James-Peerenboom/publication/3206740_Identifying_understanding_and_analyzing_critical_infrastructure_interdependencies/links/5628c9fa08aef25a243d2137/Identifying-understanding-and-analyzing-critical-infrastructure-interdependencies.pdf).

**[DOU93]** Christophe Dousson, Paul Gaborit, and Malik Ghallab. **Situation Recognition: Representation and Algorithms.** IJCAI, 1993. [Official full text](https://www.ijcai.org/Proceedings/93-1/Papers/024.pdf).

**[DOU07]** Christophe Dousson and Pierre Le Maigat. **Chronicle Recognition Improvement Using Temporal Focusing and Hierarchization.** IJCAI, 2007, pp. 324-329. [Official full text](https://www.ijcai.org/Proceedings/07/Papers/050.pdf).

**[IEC]** International Electrotechnical Commission. **International Electrotechnical Vocabulary, Dependability.** IEV 192-03-18, common cause failures, and IEV 192-03-19, common mode failures, within a system. [Common cause](https://www.electropedia.org/iev/iev.nsf/17127c61f2426ed8c1257cb5003c9bec/2b59741869320136c1257d9700617db9); [common mode](https://www.electropedia.org/iev/iev.nsf/IEVref_xref/en%3A192-03-19). Definitions checked September 17, 2026. Terminology can differ across IEC subject areas; this review adopts the dependability vocabulary.

**[SRE16]** Mike Ulrich. **Addressing Cascading Failures.** Chapter 22 of Site Reliability Engineering, 2016. [Official chapter](https://sre.google/sre-book/addressing-cascading-failures/).

**[MOT02]** Adilson E. Motter and Ying-Cheng Lai. **Cascade-based Attacks on Complex Networks.** Physical Review E 66, 065102(R), 2002. DOI: 10.1103/PhysRevE.66.065102. [Publisher](https://link.aps.org/doi/10.1103/PhysRevE.66.065102). [Author preprint](https://arxiv.org/pdf/cond-mat/0301086v1).

**[HAL25]** Tengfei An and Maria Potop-Butucaru. **The Multi-controller Model in Cloud Management.** LIP6/Sorbonne, HAL-05352360, November 6, 2025. [Repository record/full-text endpoint](https://hal.science/hal-05352360/document). Search-index metadata and abstract were accessible; the full text was access-blocked during this review. Detailed classes are therefore not reported.

**[PAR97]** H. Van Dyke Parunak and Raymond S. VanderBok. **Managing Emergent Behavior in Distributed Control Systems.** ISA-Tech, 1997; archival report ADA361539. [Full text](https://archive.org/download/DTIC_ADA361539/DTIC_ADA361539_text.pdf).

**[CHE26]** Ming Chen, Muhammed Tawfiqul Islam, Maria Rodriguez Read, and Rajkumar Buyya. **Adaptive Management of Microservices in Dynamic Computing Environments: A Taxonomy and Future Directions.** arXiv preprint 2604.25222, April 28, 2026. DOI: 10.48550/arXiv.2604.25222. [Version reviewed](https://arxiv.org/html/2604.25222v1).

**[AVI04]** Algirdas Avizienis, Jean-Claude Laprie, Brian Randell, and Carl Landwehr. **Basic Concepts and Taxonomy of Dependable and Secure Computing.** IEEE Transactions on Dependable and Secure Computing 1(1), 2004, pp. 11-33. [Author full text](https://www.landwehr.org/2004-aviz-laprie-randell.pdf).

**[RFC2914]** Sally Floyd, editor. **Congestion Control Principles.** RFC 2914, BCP 41, September 2000. DOI: 10.17487/RFC2914. [RFC](https://www.rfc-editor.org/rfc/rfc2914.html).

**[RFC2309]** Bob Braden and coauthors. **Recommendations on Queue Management and Congestion Avoidance in the Internet.** RFC 2309, April 1998. DOI: 10.17487/RFC2309. [RFC](https://www.rfc-editor.org/rfc/rfc2309.html). Used for historical global-synchronization terminology; this RFC was obsoleted by RFC 7567 in 2015.

**[AST08]** Karl Johan Astrom and Richard M. Murray. **Feedback Systems: An Introduction for Scientists and Engineers.** Princeton University Press, 2008. [Author-hosted edition](https://www.cds.caltech.edu/~murray/books/AM05/pdf/am08-complete_28Sep12.pdf). Used as a terminology reference, not evidence for a unified reliability taxonomy.

**[KEP89]** J. O. Kephart, T. Hogg, and B. A. Huberman. **Dynamics of Computational Ecosystems.** Physical Review A 40, 404, 1989. DOI: 10.1103/PhysRevA.40.404. [Publisher](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.40.404).

**[SMI20]** Connie U. Smith. **Software Performance Antipatterns in Cyber-Physical Systems.** ICPE, 2020. DOI: 10.1145/3358960.3379138. [Author full text](https://www.spe-ed.com/papers/CPSAntiPatterns.pdf).

**[OPP03]** David Oppenheimer, Archana Ganapathi, and David Patterson. **Why Do Internet Services Fail, and What Can Be Done About It?** USITS, 2003. [Official full text](https://www.usenix.org/legacy/publications/library/proceedings/usits03/tech/full_papers/oppenheimer/oppenheimer_html/index.html).

**[RFC3877]** Sharon Chisholm and Dan Romascanu. **Alarm Management Information Base (MIB).** RFC 3877, September 2004. DOI: 10.17487/RFC3877. [RFC](https://www.rfc-editor.org/rfc/rfc3877.html).

**[LDF15]** Peter Alvaro, Joshua Rosen, and Joseph M. Hellerstein. **Lineage-driven Fault Injection.** SIGMOD, 2015. [Author full text](https://people.ucsc.edu/~palvaro/molly.pdf).

**[CHA25]** Joshua Owotogbe, Indika Kumara, Willem-Jan van den Heuvel, and Damian Andrew Tamburri. **Chaos Engineering: A Multi-Vocal Literature Review.** arXiv 2412.01416, version 2, June 19, 2025; first version December 2024. DOI: 10.48550/arXiv.2412.01416. [Record](https://arxiv.org/abs/2412.01416).

**[MAN97]** Heikki Mannila, Hannu Toivonen, and A. Inkeri Verkamo. **Discovery of Frequent Episodes in Event Sequences.** Data Mining and Knowledge Discovery 1, 1997, pp. 259-289. DOI: 10.1023/A:1009748302351. [Publisher](https://link.springer.com/article/10.1023/A:1009748302351). [Author full text](https://www.cs.helsinki.fi/u/htoivone/pubs/dmkd97episodes.pdf).

**[EAD23]** Cheryl Lee, Tianyi Yang, Zhuangbin Chen, Yuxin Su, and Michael R. Lyu. **Eadro: An End-to-End Troubleshooting Framework for Microservices on Multi-source Data.** ICSE, 2023. [Record](https://arxiv.org/abs/2302.05092). [Full text](https://arxiv.org/html/2302.05092v1).

**[AGG11]** J. K. Aggarwal and M. S. Ryoo. **Human Activity Analysis: A Review.** ACM Computing Surveys 43(3), article 16, 2011. DOI: 10.1145/1922649.1922653. [Author full text](https://cvrc.ece.utexas.edu/Publications/review_ryoo_hdr.pdf).

**[STA26]** John Jamie. **How Online Services Actually Break: A Data-Backed SRE Failure Mode Taxonomy.** StackGen, June 24, 2026. [Vendor publication](https://stackgen.com/blog/sre-failure-mode-taxonomy). Included as a competing named operational catalog, not as an independently validated scientific taxonomy.

**[FOR12]** Bryan Ford. **Icebergs in the Clouds: The Other Risks of Cloud Computing.** HotCloud, 2012. [Author full text](https://dedis.cs.yale.edu/cloud/papers/hotcloud12-icebergs.pdf).

**[HPA]** Kubernetes project. **Horizontal Pod Autoscaling.** Official documentation, checked September 17, 2026. [Documentation](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/).

**[FAR26]** Ali Farahbakhsh, Qingjie Lu, Lorenzo Alvisi, Andreas Haeberlen, and Robbert van Renesse. **Characterizing Metastable Faults and Failures.** arXiv preprint 2606.00942, version 2, June 2026. DOI: 10.48550/arXiv.2606.00942. [Record](https://arxiv.org/abs/2606.00942). [Version reviewed](https://arxiv.org/html/2606.00942v2). Not treated here as an established standard or confirmed peer-reviewed publication.

**[AWS]** Marc Brooker. **Timeouts, Retries, and Backoff with Jitter.** Amazon Builders' Library. [Official full text](https://d1.awsstatic.com/builderslibrary/pdfs/timeouts-retries-and-backoff-with-jitter.pdf). Publication year is not assigned here because current web republication dates do not establish the original date.

**[STI07]** Thomas Stiefmeier, Daniel Roggen, and Gerhard Troster. **Fusion of String-Matched Templates for Continuous Activity Recognition.** ISWC, 2007, pp. 41-44. DOI: 10.1109/ISWC.2007.4373775. [Institutional record](https://www.research-collection.ethz.ch/handle/20.500.11850/7534).
