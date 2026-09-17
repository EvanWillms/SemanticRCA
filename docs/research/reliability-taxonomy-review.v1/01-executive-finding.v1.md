# Executive finding

*Reliability Activity Recognition research review | September 17, 2026 | Version 1*


**The broad framing is already occupied. Several explicit classifications cover important proposed behaviors, including a remarkably close emergent-misbehavior taxonomy sketch. No single validated, detector-ready taxonomy spanning all the requested behaviors was established by this review.**

Mogul's 2006 work explicitly proposes classifying emergent software misbehavior separately from its causes and using that classification for detection and diagnosis. It is the closest conceptual predecessor, but remains a research agenda and provisional classification rather than a completed operational standard. [MOG06]

More developed partial classifications supply useful structure. Metastable-failure research distinguishes triggers from self-sustaining mechanisms; Kivi classifies cluster-management property violations, including oscillation; and infrastructure-interdependency research distinguishes cascading, escalating, and common-cause failures. These go beyond naming broken components. [BRO21; HUA22; KIV24; RIN01]

The recognition architecture also has strong predecessors. Chronicle recognition represents temporally constrained symbolic scenarios, supports hierarchy, and has been applied to telecommunications supervision. Consequently, converting telemetry into symbolic events and recognizing composite situations cannot itself establish novelty. [DOU93; DOU07]

Most provisional behavior names should therefore become aliases for established concepts, not new taxonomy leaves. The defensible synthesis is a small, multi-label vocabulary that separates **observed temporal form, propagation or feedback mechanism, participating entities, and strength of causal evidence**. A common cause is a causal relationship, for example, whereas synchronization is a temporal relationship; treating them as sibling activities would obscure that distinction. [IEC; RIN01]

A narrower contribution remains plausible: interoperable, evidence-bound recognition definitions for established behaviors, evaluated continuously across heterogeneous telemetry and multiple systems. Such a contribution would require operational definitions, negative cases, onset/offset rules, and comparative evaluation. The sources reviewed do not establish that this exact combination is absent everywhere, nor that implementing it would require a new taxonomy.

For the brief's example, the most defensible description is **load-redistribution-induced cascading overload**. Synchronization, recurrent recovery, or metastability should be added only when separate evidence supports those qualifiers. [SRE16; MOT02; BRO21]

**Recommendation:** retain Reliability Activity Recognition as a working implementation name, while positioning the research as operationalizing established emergent-misbehavior, dependability, and temporal-recognition concepts. Do not claim discovery of a previously unclassified family of system phenomena.


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
