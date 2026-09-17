# Reliability behavior: dependability and cascade terminology

Research date: 2026-09-17. Bounded primary-source inquiry; not an exhaustive survey or a claim of novelty. This note distinguishes a taxonomy, a named mechanism, a formal model, and a possible analogy. Suggested symbolic representations below are our synthesis, not terminology standardized by the cited papers.

## Finding

There is a direct antecedent for a taxonomy of interacting reliability behaviors: Pertet and Narasimhan's **initial taxonomy of cascading failures**. Dependability terminology supplies the boundary-aware semantics around it. Network science supplies several distinct cascade mechanisms, while metastability supplies a temporal distinction that root-cause labels lose: a trigger can end while a degraded behavior sustains itself. These do not collectively constitute one accepted, comprehensive behavior ontology.

## 1. An actual taxonomy of cascading failures

[Soila Pertet and Priya Narasimhan, *Handling Cascading Failures: The Case for Topology-Aware Fault-Tolerance*, HotDep 2005, Table 1 and §2.1–3](https://research.ece.cmu.edu/mead/dsn-hotdep-2005.pdf) explicitly presents an **initial taxonomy**, with these categories:

| Source category | Mechanism, paraphrased |
|---|---|
| Malicious faults | Attacks spread through vulnerable components |
| Recovery escalation | Recovery processing generates additional neighboring failures |
| Unhandled exceptions | Unanticipated conditions cause exceptions to cascade |
| Cumulative, progressive error propagation | Propagation increases the magnitude of damage |
| Chained reconfiguration | A transient problem initiates successive reconfigurations |

The paper separately distinguishes **normal, failure-driven, and recovery-driven dependencies**, and proposes recording failure and recovery signatures. It is a workshop proposal with a preliminary case study, not an exhaustive or universally adopted classification. Its categories also mix initiators and propagation mechanisms.

**Implication (our synthesis):** A call graph alone cannot represent reliability behavior. The representation may need edges for error propagation, shared resources, workload reassignment, and recovery actions. “Recovery escalation” and “chained reconfiguration” are better literature anchors than assuming “failover stampede” is an established category.

## 2. Dependability: the semantic foundation

[Avižienis, Laprie, Randell, and Landwehr, *Basic Concepts and Taxonomy of Dependable and Secure Computing*, IEEE TDSC 2004, §2.1–2.2, §3.3–3.5](https://www.landwehr.org/2004-aviz-laprie-randell.pdf) distinguishes:

- **Fault:** the adjudged or hypothesized cause of an error.
- **Error:** a state that can lead to incorrect service.
- **Service failure:** delivered service departs from correct service.
- **Behavior:** a sequence of system states.
- **Internal/external error propagation:** transformation inside a component versus transmission across a service boundary.
- **Related faults/common cause:** faults share a cause; **common-mode failures** concern similar errors. These are not interchangeable with temporal correlation.

The same component failure may be an external fault for its consumer. Its recovery taxonomy (§5.2.1) covers error handling and fault handling, including rollback, rollforward, compensation, isolation, and reconfiguration.

**Scope:** This established taxonomy already covers propagation and recovery, not merely component faults. It is not a catalog of retry storms or controller oscillations.

**Implication (our synthesis):** Store the system boundary and role—trigger, internal state, service consequence, or extended behavior—rather than attaching one undifferentiated “failure” label.

## 3. Different kinds of cascade must remain distinct

### Critical infrastructure interdependency classification

[Rinaldi, Peerenboom, and Kelly, *Identifying, Understanding, and Analyzing Critical Infrastructure Interdependencies*, IEEE Control Systems Magazine 21(6), 11–25 (December 2001)](https://doi.org/10.1109/37.969131), particularly “Types of Failures” on pp. 21–22, supplies an explicit three-way classification. Full text was verified in the [author-uploaded paper](https://www.researchgate.net/publication/3206740_Identifying_understanding_and_analyzing_critical_infrastructure_interdependencies).

- **Cascading:** disruption in one infrastructure causes a failure and resulting disruption in another.
- **Escalating:** one disruption worsens an independent disruption elsewhere, increasing severity or delaying restoration.
- **Common cause:** a shared cause disrupts multiple infrastructure networks together.

It also distinguishes physical, cyber, geographic, and logical interdependencies, and normal, stressed/disrupted, and repair/restoration conditions.

**Transfer boundary (our synthesis):** This is a cross-infrastructure framework, originally encompassing sectors such as electricity, transport, and telecommunications. Applying it within a cloud requires explicit analogous boundaries and dependencies. In particular, “escalating” does not merely mean that one original failure becomes progressively worse. It requires an independently disrupted second system whose condition or restoration is worsened. A recovery controller failing during an existing service outage is a plausible cloud example if independence and interference are established. Concurrent alarms alone prove neither common cause nor cascading causation.

### Load redistribution and overload cascades

[Motter and Lai, *Cascade-based attacks on complex networks*, Physical Review E 66, 065102 (2002); author preprint](https://arxiv.org/abs/cond-mat/0301086) models removal of a node followed by redistributed flows, overload of other nodes, and further failure. Network topology and heterogeneous initial loads affect vulnerability.

This is a **mechanistic mathematical model**, not a complete taxonomy of computing incidents. Its load abstraction must be validated before applying it to microservice workloads.

**Candidate evidence motif (our synthesis):** capacity loss → load movement → receiving resource saturation → further capacity loss. This fits “cascading workload migration” or “overload propagation” only when those intermediate relations are observed; a group of high CPU readings alone does not establish redistribution.

### Interdependent-network cascades

[Buldyrev et al., *Catastrophic cascade of failures in interdependent networks*, Nature 464, 1025–1028 (2010)](https://doi.org/10.1038/nature08932) models recursive failure across dependency-linked networks. A loss in one network disables dependent nodes in another, which can cause additional losses in the first.

This is a **network dependency model**, distinct from flow overload. The study's idealized connectivity assumptions and fragmentation outcomes do not automatically match service availability.

**Candidate distinction (our synthesis):** service-to-service dependency cascade versus shared underlying dependency. Simultaneous service loss from a shared power or network dependency is different evidence from sequential overload propagation. “Shared-fate collapse” is an informal proposed label until the dependency and its failure are established.

### Threshold cascades and collective activation

[Watts, *A simple model of global cascades on random networks*, PNAS 99, 5766–5771 (2002)](https://pmc.ncbi.nlm.nih.gov/articles/PMC122850/) models agents changing state when sufficient neighbors have changed. The paper relates global cascades to network structure and threshold distributions.

This is a **population-dynamics model**, not a distributed-computing behavior taxonomy. It provides a possible analogy for clustered controller decisions, not a license to call synchronized remediation a contagion. Controllers independently responding to one shared metric can synchronize without influencing each other.

## 4. Metastability captures a genuinely temporal distinction

[Huang et al., *Metastable Failures in the Wild*, OSDI 2022](https://www.usenix.org/conference/osdi22/presentation/huang-lexiang) investigates sustained degraded behavior whose maintaining mechanism survives the original trigger. The paper studies 22 incidents from 11 organizations; the related [author-written USENIX article](https://www.usenix.org/publications/loginonline/metastable-failures-wild) explains stable, vulnerable, and metastable states and examples such as retries, queue growth, and garbage collection amplification. Its article version uses 21 incidents; cite the conference paper for the final study count.

**Scope:** A failure framework and empirical classification of triggers, sustaining effects, and mitigations. Not all overload, retry storms, or recurrent failures are metastable.

**Candidate evidence motif (our synthesis):** trigger → degraded state → trigger removed → degradation persists with a sustaining loop → recovery after breaking that loop. Distinguishing this from a long-running external disturbance requires evidence that the trigger ceased. “Repeated recovery and re-failure” might instead be repeated triggers, oscillation, or premature return; it should not be automatically mapped to metastability.

Two recent sources refine this framework:

- [Alvaro et al., *Formal Analysis of Metastable Failures in Software Systems*, arXiv:2510.03551v2, October 2025](https://arxiv.org/abs/2510.03551v2): a formal model using calibrated continuous-time Markov chains, escape probabilities, eigenvalue structure, and predicted recovery times. This is mathematical behavior characterization, not a label inventory. The abstract and bibliographic record were checked; this note does not claim independent verification of its proofs.
- [Farahbakhsh et al., *Characterizing Metastable Faults and Failures*, arXiv:2606.00942v2, June 2026](https://arxiv.org/abs/2606.00942v2): proposes destabilizing interaction cycles among individually stabilizing components as a causal characterization, extending beyond overload symptoms. This is especially close to “pathological feedback between independently reasonable controllers.” The record says submitted to SOSP 2026; treat it as a preprint, not an accepted consensus taxonomy. The abstract and bibliographic record were checked.

## Consequences for the symbolic-evidence thesis

The following are design inferences from the distinctions above:

1. **A behavior symbol must retain a relation over time, not merely quantize one value.** “High” CPU is a state observation; “load was reassigned and receiving nodes subsequently saturated” is an evidence pattern.
2. **Separate observations from mechanism hypotheses.** A symbol may encode observed recurrence or synchronization while remaining uncertain about feedback, common cause, or propagation.
3. **Store relations, timing, scope, and missing evidence.** For example: participating components, state transitions, temporal ordering, dependency type, recovery action, observed response, and confidence/provenance.
4. **Test discriminating information, not attractive labels.** Paired episodes could have similar aggregate utilization while differing in redistribution, a common trigger, or self-sustaining retries. The question is whether a compressed representation preserves the evidence needed to distinguish them.
5. **Avoid making the answer the encoding.** Providing an LLM a preassigned `RETRY_STORM` label and asking it to recognize a retry storm mostly evaluates the upstream classifier. Encode the relevant observations and relationships, then test whether the LLM can recover the behavior distinction with less input.

These sources justify a research target broader than fault localization. They do not establish that any proposed behavior is observable in the hackathon dataset, that the symbolic method will preserve its evidence, or that an LLM improves upon a non-LLM recognizer.
