# Research gaps and falsifiers

*Reliability Activity Recognition research review | September 17, 2026 | Version 1*


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

**[HUA22]** Lexiang Huang, Matthew Magnusson, Abishek Bangalore Muralikrishna, Salman Estyak, Rebecca Isaacs, Abutalib Aghayev, Timothy Zhu, and Aleksey Charapko. **Metastable Failures in the Wild.** OSDI, 2022, pp. 73-90. [Publication and paper](https://www.usenix.org/conference/osdi22/presentation/huang-lexiang).

**[KIV24]** Bingzhe Liu, Gangmuk Lim, Ryan Beckett, and P. Brighten Godfrey. **Kivi: Verification for Cluster Management.** USENIX ATC, 2024, pp. 509-527. [Publication and paper](https://www.usenix.org/conference/atc24/presentation/liu-bingzhe).

**[RIN01]** Steven M. Rinaldi, James P. Peerenboom, and Terrence K. Kelly. **Identifying, Understanding, and Analyzing Critical Infrastructure Interdependencies.** IEEE Control Systems Magazine 21(6), 2001, pp. 11-25. [Publisher record](https://ieeexplore.ieee.org/document/969131). [Author-posted full text](https://www.researchgate.net/profile/James-Peerenboom/publication/3206740_Identifying_understanding_and_analyzing_critical_infrastructure_interdependencies/links/5628c9fa08aef25a243d2137/Identifying-understanding-and-analyzing-critical-infrastructure-interdependencies.pdf).

**[DOU93]** Christophe Dousson, Paul Gaborit, and Malik Ghallab. **Situation Recognition: Representation and Algorithms.** IJCAI, 1993. [Official full text](https://www.ijcai.org/Proceedings/93-1/Papers/024.pdf).

**[DOU07]** Christophe Dousson and Pierre Le Maigat. **Chronicle Recognition Improvement Using Temporal Focusing and Hierarchization.** IJCAI, 2007, pp. 324-329. [Official full text](https://www.ijcai.org/Proceedings/07/Papers/050.pdf).

**[MAN97]** Heikki Mannila, Hannu Toivonen, and A. Inkeri Verkamo. **Discovery of Frequent Episodes in Event Sequences.** Data Mining and Knowledge Discovery 1, 1997, pp. 259-289. DOI: 10.1023/A:1009748302351. [Publisher](https://link.springer.com/article/10.1023/A:1009748302351). [Author full text](https://www.cs.helsinki.fi/u/htoivone/pubs/dmkd97episodes.pdf).

**[EAD23]** Cheryl Lee, Tianyi Yang, Zhuangbin Chen, Yuxin Su, and Michael R. Lyu. **Eadro: An End-to-End Troubleshooting Framework for Microservices on Multi-source Data.** ICSE, 2023. [Record](https://arxiv.org/abs/2302.05092). [Full text](https://arxiv.org/html/2302.05092v1).

**[KEP89]** J. O. Kephart, T. Hogg, and B. A. Huberman. **Dynamics of Computational Ecosystems.** Physical Review A 40, 404, 1989. DOI: 10.1103/PhysRevA.40.404. [Publisher](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.40.404).

**[PAR97]** H. Van Dyke Parunak and Raymond S. VanderBok. **Managing Emergent Behavior in Distributed Control Systems.** ISA-Tech, 1997; archival report ADA361539. [Full text](https://archive.org/download/DTIC_ADA361539/DTIC_ADA361539_text.pdf).

**[OPP03]** David Oppenheimer, Archana Ganapathi, and David Patterson. **Why Do Internet Services Fail, and What Can Be Done About It?** USITS, 2003. [Official full text](https://www.usenix.org/legacy/publications/library/proceedings/usits03/tech/full_papers/oppenheimer/oppenheimer_html/index.html).

**[RFC3877]** Sharon Chisholm and Dan Romascanu. **Alarm Management Information Base (MIB).** RFC 3877, September 2004. DOI: 10.17487/RFC3877. [RFC](https://www.rfc-editor.org/rfc/rfc3877.html).

**[CHA25]** Joshua Owotogbe, Indika Kumara, Willem-Jan van den Heuvel, and Damian Andrew Tamburri. **Chaos Engineering: A Multi-Vocal Literature Review.** arXiv 2412.01416, version 2, June 19, 2025; first version December 2024. DOI: 10.48550/arXiv.2412.01416. [Record](https://arxiv.org/abs/2412.01416).

**[AGG11]** J. K. Aggarwal and M. S. Ryoo. **Human Activity Analysis: A Review.** ACM Computing Surveys 43(3), article 16, 2011. DOI: 10.1145/1922649.1922653. [Author full text](https://cvrc.ece.utexas.edu/Publications/review_ryoo_hdr.pdf).

**[FAR26]** Ali Farahbakhsh, Qingjie Lu, Lorenzo Alvisi, Andreas Haeberlen, and Robbert van Renesse. **Characterizing Metastable Faults and Failures.** arXiv preprint 2606.00942, version 2, June 2026. DOI: 10.48550/arXiv.2606.00942. [Record](https://arxiv.org/abs/2606.00942). [Version reviewed](https://arxiv.org/html/2606.00942v2). Not treated here as an established standard or confirmed peer-reviewed publication.

**[HAL25]** Tengfei An and Maria Potop-Butucaru. **The Multi-controller Model in Cloud Management.** LIP6/Sorbonne, HAL-05352360, November 6, 2025. [Repository record/full-text endpoint](https://hal.science/hal-05352360/document). Search-index metadata and abstract were accessible; the full text was access-blocked during this review. Detailed classes are therefore not reported.

**[STA26]** John Jamie. **How Online Services Actually Break: A Data-Backed SRE Failure Mode Taxonomy.** StackGen, June 24, 2026. [Vendor publication](https://stackgen.com/blog/sre-failure-mode-taxonomy). Included as a competing named operational catalog, not as an independently validated scientific taxonomy.

**[SRE16]** Mike Ulrich. **Addressing Cascading Failures.** Chapter 22 of Site Reliability Engineering, 2016. [Official chapter](https://sre.google/sre-book/addressing-cascading-failures/).

**[MOT02]** Adilson E. Motter and Ying-Cheng Lai. **Cascade-based Attacks on Complex Networks.** Physical Review E 66, 065102(R), 2002. DOI: 10.1103/PhysRevE.66.065102. [Publisher](https://link.aps.org/doi/10.1103/PhysRevE.66.065102). [Author preprint](https://arxiv.org/pdf/cond-mat/0301086v1).
