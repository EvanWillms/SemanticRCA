# Taxonomy landscape

*Reliability Activity Recognition research review | September 17, 2026 | Version 1*


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


## Source register

**[HAL25]** Tengfei An and Maria Potop-Butucaru. **The Multi-controller Model in Cloud Management.** LIP6/Sorbonne, HAL-05352360, November 6, 2025. [Repository record/full-text endpoint](https://hal.science/hal-05352360/document). Search-index metadata and abstract were accessible; the full text was access-blocked during this review. Detailed classes are therefore not reported.

**[MOG06]** Jeffrey C. Mogul. **Emergent (Mis)behavior vs. Complex Software Systems.** EuroSys, 2006, pp. 293-304. [Publication record](https://research.google/pubs/emergent-misbehavior-vs-complex-software-systems/). The full text reviewed was the author-posted technical-report version, HPL-2006-2, internally dated December 22, 2005: [author full text](https://www.researchgate.net/profile/Jeffrey-Mogul-2/publication/221351778_Emergent_Mis_behavior_vs_Complex_Software_Systems/links/0046353a2820ee859a000000/Emergent-Mis-behavior-vs-Complex-Software-Systems.pdf).

**[PAR97]** H. Van Dyke Parunak and Raymond S. VanderBok. **Managing Emergent Behavior in Distributed Control Systems.** ISA-Tech, 1997; archival report ADA361539. [Full text](https://archive.org/download/DTIC_ADA361539/DTIC_ADA361539_text.pdf).

**[BRO21]** Nathan Bronson, Abutalib Aghayev, Aleksey Charapko, and Timothy Zhu. **Metastable Failures in Distributed Systems.** HotOS, 2021, pp. 221-227. DOI: 10.1145/3458336.3465286. [Full text](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf).

**[HUA22]** Lexiang Huang, Matthew Magnusson, Abishek Bangalore Muralikrishna, Salman Estyak, Rebecca Isaacs, Abutalib Aghayev, Timothy Zhu, and Aleksey Charapko. **Metastable Failures in the Wild.** OSDI, 2022, pp. 73-90. [Publication and paper](https://www.usenix.org/conference/osdi22/presentation/huang-lexiang).

**[KIV24]** Bingzhe Liu, Gangmuk Lim, Ryan Beckett, and P. Brighten Godfrey. **Kivi: Verification for Cluster Management.** USENIX ATC, 2024, pp. 509-527. [Publication and paper](https://www.usenix.org/conference/atc24/presentation/liu-bingzhe).

**[CHE26]** Ming Chen, Muhammed Tawfiqul Islam, Maria Rodriguez Read, and Rajkumar Buyya. **Adaptive Management of Microservices in Dynamic Computing Environments: A Taxonomy and Future Directions.** arXiv preprint 2604.25222, April 28, 2026. DOI: 10.48550/arXiv.2604.25222. [Version reviewed](https://arxiv.org/html/2604.25222v1).

**[AVI04]** Algirdas Avizienis, Jean-Claude Laprie, Brian Randell, and Carl Landwehr. **Basic Concepts and Taxonomy of Dependable and Secure Computing.** IEEE Transactions on Dependable and Secure Computing 1(1), 2004, pp. 11-33. [Author full text](https://www.landwehr.org/2004-aviz-laprie-randell.pdf).

**[RIN01]** Steven M. Rinaldi, James P. Peerenboom, and Terrence K. Kelly. **Identifying, Understanding, and Analyzing Critical Infrastructure Interdependencies.** IEEE Control Systems Magazine 21(6), 2001, pp. 11-25. [Publisher record](https://ieeexplore.ieee.org/document/969131). [Author-posted full text](https://www.researchgate.net/profile/James-Peerenboom/publication/3206740_Identifying_understanding_and_analyzing_critical_infrastructure_interdependencies/links/5628c9fa08aef25a243d2137/Identifying-understanding-and-analyzing-critical-infrastructure-interdependencies.pdf).

**[RFC2914]** Sally Floyd, editor. **Congestion Control Principles.** RFC 2914, BCP 41, September 2000. DOI: 10.17487/RFC2914. [RFC](https://www.rfc-editor.org/rfc/rfc2914.html).

**[RFC2309]** Bob Braden and coauthors. **Recommendations on Queue Management and Congestion Avoidance in the Internet.** RFC 2309, April 1998. DOI: 10.17487/RFC2309. [RFC](https://www.rfc-editor.org/rfc/rfc2309.html). Used for historical global-synchronization terminology; this RFC was obsoleted by RFC 7567 in 2015.

**[AST08]** Karl Johan Astrom and Richard M. Murray. **Feedback Systems: An Introduction for Scientists and Engineers.** Princeton University Press, 2008. [Author-hosted edition](https://www.cds.caltech.edu/~murray/books/AM05/pdf/am08-complete_28Sep12.pdf). Used as a terminology reference, not evidence for a unified reliability taxonomy.

**[KEP89]** J. O. Kephart, T. Hogg, and B. A. Huberman. **Dynamics of Computational Ecosystems.** Physical Review A 40, 404, 1989. DOI: 10.1103/PhysRevA.40.404. [Publisher](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.40.404).

**[SMI20]** Connie U. Smith. **Software Performance Antipatterns in Cyber-Physical Systems.** ICPE, 2020. DOI: 10.1145/3358960.3379138. [Author full text](https://www.spe-ed.com/papers/CPSAntiPatterns.pdf).

**[OPP03]** David Oppenheimer, Archana Ganapathi, and David Patterson. **Why Do Internet Services Fail, and What Can Be Done About It?** USITS, 2003. [Official full text](https://www.usenix.org/legacy/publications/library/proceedings/usits03/tech/full_papers/oppenheimer/oppenheimer_html/index.html).

**[RFC3877]** Sharon Chisholm and Dan Romascanu. **Alarm Management Information Base (MIB).** RFC 3877, September 2004. DOI: 10.17487/RFC3877. [RFC](https://www.rfc-editor.org/rfc/rfc3877.html).

**[LDF15]** Peter Alvaro, Joshua Rosen, and Joseph M. Hellerstein. **Lineage-driven Fault Injection.** SIGMOD, 2015. [Author full text](https://people.ucsc.edu/~palvaro/molly.pdf).

**[CHA25]** Joshua Owotogbe, Indika Kumara, Willem-Jan van den Heuvel, and Damian Andrew Tamburri. **Chaos Engineering: A Multi-Vocal Literature Review.** arXiv 2412.01416, version 2, June 19, 2025; first version December 2024. DOI: 10.48550/arXiv.2412.01416. [Record](https://arxiv.org/abs/2412.01416).

**[DOU93]** Christophe Dousson, Paul Gaborit, and Malik Ghallab. **Situation Recognition: Representation and Algorithms.** IJCAI, 1993. [Official full text](https://www.ijcai.org/Proceedings/93-1/Papers/024.pdf).

**[DOU07]** Christophe Dousson and Pierre Le Maigat. **Chronicle Recognition Improvement Using Temporal Focusing and Hierarchization.** IJCAI, 2007, pp. 324-329. [Official full text](https://www.ijcai.org/Proceedings/07/Papers/050.pdf).

**[MAN97]** Heikki Mannila, Hannu Toivonen, and A. Inkeri Verkamo. **Discovery of Frequent Episodes in Event Sequences.** Data Mining and Knowledge Discovery 1, 1997, pp. 259-289. DOI: 10.1023/A:1009748302351. [Publisher](https://link.springer.com/article/10.1023/A:1009748302351). [Author full text](https://www.cs.helsinki.fi/u/htoivone/pubs/dmkd97episodes.pdf).

**[EAD23]** Cheryl Lee, Tianyi Yang, Zhuangbin Chen, Yuxin Su, and Michael R. Lyu. **Eadro: An End-to-End Troubleshooting Framework for Microservices on Multi-source Data.** ICSE, 2023. [Record](https://arxiv.org/abs/2302.05092). [Full text](https://arxiv.org/html/2302.05092v1).

**[AGG11]** J. K. Aggarwal and M. S. Ryoo. **Human Activity Analysis: A Review.** ACM Computing Surveys 43(3), article 16, 2011. DOI: 10.1145/1922649.1922653. [Author full text](https://cvrc.ece.utexas.edu/Publications/review_ryoo_hdr.pdf).

**[STA26]** John Jamie. **How Online Services Actually Break: A Data-Backed SRE Failure Mode Taxonomy.** StackGen, June 24, 2026. [Vendor publication](https://stackgen.com/blog/sre-failure-mode-taxonomy). Included as a competing named operational catalog, not as an independently validated scientific taxonomy.

**[SRE16]** Mike Ulrich. **Addressing Cascading Failures.** Chapter 22 of Site Reliability Engineering, 2016. [Official chapter](https://sre.google/sre-book/addressing-cascading-failures/).

**[FOR12]** Bryan Ford. **Icebergs in the Clouds: The Other Risks of Cloud Computing.** HotCloud, 2012. [Author full text](https://dedis.cs.yale.edu/cloud/papers/hotcloud12-icebergs.pdf).

**[HPA]** Kubernetes project. **Horizontal Pod Autoscaling.** Official documentation, checked September 17, 2026. [Documentation](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/).

**[FAR26]** Ali Farahbakhsh, Qingjie Lu, Lorenzo Alvisi, Andreas Haeberlen, and Robbert van Renesse. **Characterizing Metastable Faults and Failures.** arXiv preprint 2606.00942, version 2, June 2026. DOI: 10.48550/arXiv.2606.00942. [Record](https://arxiv.org/abs/2606.00942). [Version reviewed](https://arxiv.org/html/2606.00942v2). Not treated here as an established standard or confirmed peer-reviewed publication.

**[AWS]** Marc Brooker. **Timeouts, Retries, and Backoff with Jitter.** Amazon Builders' Library. [Official full text](https://d1.awsstatic.com/builderslibrary/pdfs/timeouts-retries-and-backoff-with-jitter.pdf). Publication year is not assigned here because current web republication dates do not establish the original date.

**[IEC]** International Electrotechnical Commission. **International Electrotechnical Vocabulary, Dependability.** IEV 192-03-18, common cause failures, and IEV 192-03-19, common mode failures, within a system. [Common cause](https://www.electropedia.org/iev/iev.nsf/17127c61f2426ed8c1257cb5003c9bec/2b59741869320136c1257d9700617db9); [common mode](https://www.electropedia.org/iev/iev.nsf/IEVref_xref/en%3A192-03-19). Definitions checked September 17, 2026. Terminology can differ across IEC subject areas; this review adopts the dependability vocabulary.

**[MOT02]** Adilson E. Motter and Ying-Cheng Lai. **Cascade-based Attacks on Complex Networks.** Physical Review E 66, 065102(R), 2002. DOI: 10.1103/PhysRevE.66.065102. [Publisher](https://link.aps.org/doi/10.1103/PhysRevE.66.065102). [Author preprint](https://arxiv.org/pdf/cond-mat/0301086v1).

**[STI07]** Thomas Stiefmeier, Daniel Roggen, and Gerhard Troster. **Fusion of String-Matched Templates for Continuous Activity Recognition.** ISWC, 2007, pp. 41-44. DOI: 10.1109/ISWC.2007.4373775. [Institutional record](https://www.research-collection.ethz.ch/handle/20.500.11850/7534).
