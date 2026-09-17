# Candidate synthesis

*Reliability Activity Recognition research review | September 17, 2026 | Version 1*


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


## Source register

**[MOG06]** Jeffrey C. Mogul. **Emergent (Mis)behavior vs. Complex Software Systems.** EuroSys, 2006, pp. 293-304. [Publication record](https://research.google/pubs/emergent-misbehavior-vs-complex-software-systems/). The full text reviewed was the author-posted technical-report version, HPL-2006-2, internally dated December 22, 2005: [author full text](https://www.researchgate.net/profile/Jeffrey-Mogul-2/publication/221351778_Emergent_Mis_behavior_vs_Complex_Software_Systems/links/0046353a2820ee859a000000/Emergent-Mis-behavior-vs-Complex-Software-Systems.pdf).

**[PAR97]** H. Van Dyke Parunak and Raymond S. VanderBok. **Managing Emergent Behavior in Distributed Control Systems.** ISA-Tech, 1997; archival report ADA361539. [Full text](https://archive.org/download/DTIC_ADA361539/DTIC_ADA361539_text.pdf).

**[KIV24]** Bingzhe Liu, Gangmuk Lim, Ryan Beckett, and P. Brighten Godfrey. **Kivi: Verification for Cluster Management.** USENIX ATC, 2024, pp. 509-527. [Publication and paper](https://www.usenix.org/conference/atc24/presentation/liu-bingzhe).

**[RIN01]** Steven M. Rinaldi, James P. Peerenboom, and Terrence K. Kelly. **Identifying, Understanding, and Analyzing Critical Infrastructure Interdependencies.** IEEE Control Systems Magazine 21(6), 2001, pp. 11-25. [Publisher record](https://ieeexplore.ieee.org/document/969131). [Author-posted full text](https://www.researchgate.net/profile/James-Peerenboom/publication/3206740_Identifying_understanding_and_analyzing_critical_infrastructure_interdependencies/links/5628c9fa08aef25a243d2137/Identifying-understanding-and-analyzing-critical-infrastructure-interdependencies.pdf).

**[AVI04]** Algirdas Avizienis, Jean-Claude Laprie, Brian Randell, and Carl Landwehr. **Basic Concepts and Taxonomy of Dependable and Secure Computing.** IEEE Transactions on Dependable and Secure Computing 1(1), 2004, pp. 11-33. [Author full text](https://www.landwehr.org/2004-aviz-laprie-randell.pdf).

**[HUA22]** Lexiang Huang, Matthew Magnusson, Abishek Bangalore Muralikrishna, Salman Estyak, Rebecca Isaacs, Abutalib Aghayev, Timothy Zhu, and Aleksey Charapko. **Metastable Failures in the Wild.** OSDI, 2022, pp. 73-90. [Publication and paper](https://www.usenix.org/conference/osdi22/presentation/huang-lexiang).

**[BRO21]** Nathan Bronson, Abutalib Aghayev, Aleksey Charapko, and Timothy Zhu. **Metastable Failures in Distributed Systems.** HotOS, 2021, pp. 221-227. DOI: 10.1145/3458336.3465286. [Full text](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf).

**[HPA]** Kubernetes project. **Horizontal Pod Autoscaling.** Official documentation, checked September 17, 2026. [Documentation](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/).

**[SRE16]** Mike Ulrich. **Addressing Cascading Failures.** Chapter 22 of Site Reliability Engineering, 2016. [Official chapter](https://sre.google/sre-book/addressing-cascading-failures/).

**[DOU07]** Christophe Dousson and Pierre Le Maigat. **Chronicle Recognition Improvement Using Temporal Focusing and Hierarchization.** IJCAI, 2007, pp. 324-329. [Official full text](https://www.ijcai.org/Proceedings/07/Papers/050.pdf).

**[MAN97]** Heikki Mannila, Hannu Toivonen, and A. Inkeri Verkamo. **Discovery of Frequent Episodes in Event Sequences.** Data Mining and Knowledge Discovery 1, 1997, pp. 259-289. DOI: 10.1023/A:1009748302351. [Publisher](https://link.springer.com/article/10.1023/A:1009748302351). [Author full text](https://www.cs.helsinki.fi/u/htoivone/pubs/dmkd97episodes.pdf).

**[DOU93]** Christophe Dousson, Paul Gaborit, and Malik Ghallab. **Situation Recognition: Representation and Algorithms.** IJCAI, 1993. [Official full text](https://www.ijcai.org/Proceedings/93-1/Papers/024.pdf).

**[RFC3877]** Sharon Chisholm and Dan Romascanu. **Alarm Management Information Base (MIB).** RFC 3877, September 2004. DOI: 10.17487/RFC3877. [RFC](https://www.rfc-editor.org/rfc/rfc3877.html).

**[STI07]** Thomas Stiefmeier, Daniel Roggen, and Gerhard Troster. **Fusion of String-Matched Templates for Continuous Activity Recognition.** ISWC, 2007, pp. 41-44. DOI: 10.1109/ISWC.2007.4373775. [Institutional record](https://www.research-collection.ethz.ch/handle/20.500.11850/7534).

**[AGG11]** J. K. Aggarwal and M. S. Ryoo. **Human Activity Analysis: A Review.** ACM Computing Surveys 43(3), article 16, 2011. DOI: 10.1145/1922649.1922653. [Author full text](https://cvrc.ece.utexas.edu/Publications/review_ryoo_hdr.pdf).

**[KEP89]** J. O. Kephart, T. Hogg, and B. A. Huberman. **Dynamics of Computational Ecosystems.** Physical Review A 40, 404, 1989. DOI: 10.1103/PhysRevA.40.404. [Publisher](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.40.404).

**[MOT02]** Adilson E. Motter and Ying-Cheng Lai. **Cascade-based Attacks on Complex Networks.** Physical Review E 66, 065102(R), 2002. DOI: 10.1103/PhysRevE.66.065102. [Publisher](https://link.aps.org/doi/10.1103/PhysRevE.66.065102). [Author preprint](https://arxiv.org/pdf/cond-mat/0301086v1).
