# Crosswalk from provisional concepts to existing terminology

*Reliability Activity Recognition research review | September 17, 2026 | Version 1*


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


## Source register

**[MOG06]** Jeffrey C. Mogul. **Emergent (Mis)behavior vs. Complex Software Systems.** EuroSys, 2006, pp. 293-304. [Publication record](https://research.google/pubs/emergent-misbehavior-vs-complex-software-systems/). The full text reviewed was the author-posted technical-report version, HPL-2006-2, internally dated December 22, 2005: [author full text](https://www.researchgate.net/profile/Jeffrey-Mogul-2/publication/221351778_Emergent_Mis_behavior_vs_Complex_Software_Systems/links/0046353a2820ee859a000000/Emergent-Mis-behavior-vs-Complex-Software-Systems.pdf).

**[PAR97]** H. Van Dyke Parunak and Raymond S. VanderBok. **Managing Emergent Behavior in Distributed Control Systems.** ISA-Tech, 1997; archival report ADA361539. [Full text](https://archive.org/download/DTIC_ADA361539/DTIC_ADA361539_text.pdf).

**[SRE16]** Mike Ulrich. **Addressing Cascading Failures.** Chapter 22 of Site Reliability Engineering, 2016. [Official chapter](https://sre.google/sre-book/addressing-cascading-failures/).

**[HUA22]** Lexiang Huang, Matthew Magnusson, Abishek Bangalore Muralikrishna, Salman Estyak, Rebecca Isaacs, Abutalib Aghayev, Timothy Zhu, and Aleksey Charapko. **Metastable Failures in the Wild.** OSDI, 2022, pp. 73-90. [Publication and paper](https://www.usenix.org/conference/osdi22/presentation/huang-lexiang).

**[AWS]** Marc Brooker. **Timeouts, Retries, and Backoff with Jitter.** Amazon Builders' Library. [Official full text](https://d1.awsstatic.com/builderslibrary/pdfs/timeouts-retries-and-backoff-with-jitter.pdf). Publication year is not assigned here because current web republication dates do not establish the original date.

**[RFC2914]** Sally Floyd, editor. **Congestion Control Principles.** RFC 2914, BCP 41, September 2000. DOI: 10.17487/RFC2914. [RFC](https://www.rfc-editor.org/rfc/rfc2914.html).

**[HPA]** Kubernetes project. **Horizontal Pod Autoscaling.** Official documentation, checked September 17, 2026. [Documentation](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/).

**[KIV24]** Bingzhe Liu, Gangmuk Lim, Ryan Beckett, and P. Brighten Godfrey. **Kivi: Verification for Cluster Management.** USENIX ATC, 2024, pp. 509-527. [Publication and paper](https://www.usenix.org/conference/atc24/presentation/liu-bingzhe).

**[FOR12]** Bryan Ford. **Icebergs in the Clouds: The Other Risks of Cloud Computing.** HotCloud, 2012. [Author full text](https://dedis.cs.yale.edu/cloud/papers/hotcloud12-icebergs.pdf).

**[AST08]** Karl Johan Astrom and Richard M. Murray. **Feedback Systems: An Introduction for Scientists and Engineers.** Princeton University Press, 2008. [Author-hosted edition](https://www.cds.caltech.edu/~murray/books/AM05/pdf/am08-complete_28Sep12.pdf). Used as a terminology reference, not evidence for a unified reliability taxonomy.

**[IEC]** International Electrotechnical Commission. **International Electrotechnical Vocabulary, Dependability.** IEV 192-03-18, common cause failures, and IEV 192-03-19, common mode failures, within a system. [Common cause](https://www.electropedia.org/iev/iev.nsf/17127c61f2426ed8c1257cb5003c9bec/2b59741869320136c1257d9700617db9); [common mode](https://www.electropedia.org/iev/iev.nsf/IEVref_xref/en%3A192-03-19). Definitions checked September 17, 2026. Terminology can differ across IEC subject areas; this review adopts the dependability vocabulary.

**[AVI04]** Algirdas Avizienis, Jean-Claude Laprie, Brian Randell, and Carl Landwehr. **Basic Concepts and Taxonomy of Dependable and Secure Computing.** IEEE Transactions on Dependable and Secure Computing 1(1), 2004, pp. 11-33. [Author full text](https://www.landwehr.org/2004-aviz-laprie-randell.pdf).

**[RIN01]** Steven M. Rinaldi, James P. Peerenboom, and Terrence K. Kelly. **Identifying, Understanding, and Analyzing Critical Infrastructure Interdependencies.** IEEE Control Systems Magazine 21(6), 2001, pp. 11-25. [Publisher record](https://ieeexplore.ieee.org/document/969131). [Author-posted full text](https://www.researchgate.net/profile/James-Peerenboom/publication/3206740_Identifying_understanding_and_analyzing_critical_infrastructure_interdependencies/links/5628c9fa08aef25a243d2137/Identifying-understanding-and-analyzing-critical-infrastructure-interdependencies.pdf).

**[MOT02]** Adilson E. Motter and Ying-Cheng Lai. **Cascade-based Attacks on Complex Networks.** Physical Review E 66, 065102(R), 2002. DOI: 10.1103/PhysRevE.66.065102. [Publisher](https://link.aps.org/doi/10.1103/PhysRevE.66.065102). [Author preprint](https://arxiv.org/pdf/cond-mat/0301086v1).

**[BRO21]** Nathan Bronson, Abutalib Aghayev, Aleksey Charapko, and Timothy Zhu. **Metastable Failures in Distributed Systems.** HotOS, 2021, pp. 221-227. DOI: 10.1145/3458336.3465286. [Full text](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf).

**[KEP89]** J. O. Kephart, T. Hogg, and B. A. Huberman. **Dynamics of Computational Ecosystems.** Physical Review A 40, 404, 1989. DOI: 10.1103/PhysRevA.40.404. [Publisher](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.40.404).
