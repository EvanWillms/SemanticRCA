# Distributed-system behavior classifications for symbolic telemetry

Research date: 2026-09-17. Scope: primary-source frameworks and terminology for temporally extended distributed-system behaviors, rather than component fault catalogues. This is a bounded literature search, not proof that no unified taxonomy exists.

## Main finding

The strongest directly applicable framework found is **metastable failure**, which separates a triggering disturbance from the feedback mechanism that sustains degraded operation. It is narrower than a taxonomy of all reliability behaviors. SRE literature contributes a practical catalogue of cascading mechanisms; networking literature contributes congestion-collapse and synchronization classifications. These overlap and should not be forced into mutually exclusive labels.

## Frameworks and source-backed vocabulary

### 1. Metastable failure: a behavioral lifecycle

Bronson et al., *Metastable Failures in Distributed Systems*, HotOS 2021, distinguish **stable**, **vulnerable**, and **metastable** states. A vulnerable system can operate normally until a disturbance activates a sustaining feedback loop. Degradation then persists after the original disturbance disappears. Their analytical emphasis is the sustaining effect, rather than merely the trigger; different triggers can produce the same problematic dynamics. They also describe spread across failure domains. This is a lifecycle and mechanism framework, not a component-fault inventory. [Primary paper, §§1–3](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf)

Huang et al., *Metastable Failures in the Wild*, OSDI 2022, refine that framework with two classification axes: **load-spike versus capacity-decreasing triggers**, and **workload amplification versus capacity-degradation amplification**. Either amplification mechanism, or both, can sustain overload. They distinguish original demand and capacity from load and capacity after amplification. Their case-study inventory records triggers, sustaining mechanisms, impact, and mitigations separately. This supplies a real classification scheme for a subset of the proposed behaviors, supported by incident analysis and controlled reproductions. It does not make every prolonged outage metastable: persistence after trigger removal and a sustaining mechanism are essential. [Primary paper, §§2–3 and Table 1](https://www.usenix.org/system/files/osdi22-huang-lexiang.pdf)

### 2. Cascading failure: positive-feedback propagation

Google's SRE chapter treats cascading failure as a failure that expands through positive feedback. Mechanisms include traffic redistribution after replica loss, retries adding work, exclusion of unhealthy backends reducing serving capacity, and inter-backend communication spreading resource contention. It also describes servers repeatedly recovering and immediately failing again under the remaining load. This is an operational mechanism catalogue, not a formal exhaustive taxonomy. It supports mapping “cascading workload migration” to **load redistribution causing cascading overload**, and some “recovery and re-failure” episodes to **crash-looping under overload**. Those mappings require the described mechanism, rather than merely similar metric shapes. [Google SRE, “Addressing Cascading Failures”](https://sre.google/sre-book/addressing-cascading-failures/)

### 3. Congestion collapse: useful work versus offered load

RFC 2914 distinguishes **classical congestion collapse**, involving unnecessary retransmission, from **congestion collapse from undelivered packets**, where packets consume upstream resources before being dropped later. Its behavioral criterion is that increasing offered load reduces useful work. This is a concrete subtype classification, not simply “packet loss.” It motivates preserving successful work separately from total work in a symbolic representation. [IETF RFC 2914, §§3 and 5](https://www.ietf.org/rfc/rfc2914)

### 4. Synchronization: a population-level phenomenon

Floyd and Jacobson's *The Synchronization of Periodic Routing Messages* (1994) distinguishes examples involving shared external clocks, client/server recovery, TCP window cycles, and initially independent periodic routing processes. Their model shows abrupt transitions to synchronized traffic through weak coupling. This is a theory and mechanism study of **inadvertent synchronization**, not an incident taxonomy. It is a better starting vocabulary for “synchronized remediation” or coordinated recovery than assuming these are new phenomena. Synchronization must be demonstrated across participants; a periodic aggregate metric alone is insufficient. [Authors' paper, introduction and model](https://www.icir.org/floyd/papers/sync_94.pdf)

### 5. Thundering herd and retry amplification: established mechanisms

Amazon's caching account uses **thundering herd** for many clients concurrently requesting the same uncached downstream resource. Cold cache startup can provoke it; request coalescing addresses duplicate concurrent work. This is a named interaction pattern, not a general label for any traffic spike. [Amazon Builders' Library, “Caching challenges and strategies”](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/)

AWS retry guidance explains **unintentionally coordinated retries**, where clients retry on common intervals, and prescribes backoff, jitter, and retry limits. Thus “retry amplification” and synchronization should be distinct dimensions: retry volume can amplify without participants synchronizing. [AWS Well-Architected, “Control and limit retry calls”](https://docs.aws.amazon.com/wellarchitected/2024-06-27/framework/rel_mitigate_interaction_failure_limit_retries.html)

### 6. Correlated failure is different from propagation

Amazon's account of **correlated failures** explains why redundancy assumptions fail when several failures share an underlying cause. This offers vocabulary for “shared-fate collapse,” but observed temporal correlation does not itself establish a common cause. A shared initiating dependency differs from one failed component driving another into failure. Those explanations may coexist. [Amazon Builders' Library, “Minimizing correlated failures in distributed systems”](https://d1.awsstatic.com/builderslibrary/pdfs/minimizing-correlated-failures-in-distributed-systems.pdf)

### 7. Emerging formal work on harmful composition

Farahbakhsh et al., *Characterizing Metastable Faults and Failures*, arXiv:2606.00942, explicitly analyze destabilizing cycles formed by components that individually tend to stabilize. They distinguish a structural metastable fault from an execution that actually produces metastable failure. This is exceptionally close to “pathological feedback between independently reasonable controllers.” It is a **2026 preprint**, with the source listing submission to SOSP 2026; publication acceptance and broad adoption are not established here. [Primary preprint and version history](https://arxiv.org/abs/2606.00942)

### 8. Recovery cascades can reintroduce failure

Porter and Charapko's first-party SREcon talk, *When the Cure Is Worse than the Disease: Metastability in Recovery*, explicitly names **recovery cascades**: recovery in one component starts recovery in another, multiplying the cost. Effects can propagate back into already recovered systems, establishing feedback that renews the failure. This is particularly relevant to “repeated recovery and re-failure”; it supplies stronger terminology than merely describing an oscillating graph. It is a practitioner case account, not a comprehensive classification. The page's URL identifies SREcon26, while its displayed session date says March 26, 2025; this note therefore does not assign an exact presentation year. [USENIX presentation abstract](https://www.usenix.org/conference/srecon26americas/presentation/porter)

### 9. Formal abstraction already supports behavioral analysis

Isaacs et al., *Analyzing Metastable Failures*, HotOS 2025, present a shared modeling language for thread pools, queues, requests, and retry policies, interpreted by continuous-time Markov chains, simulation, and emulation. Concrete observations calibrate abstract models. Their running experiment contrasts recovery and persistent degradation following the same temporary demand surge. The paper explicitly exposes an abstraction-versus-fidelity tradeoff and checks predictions against more concrete representations. This is an analysis method, not another fault taxonomy; it is useful prior art for proposing semantically meaningful compression, although the paper does not establish LLM usefulness. [Primary paper, §§2–5](https://sigops.org/s/conferences/hotos/2025/papers/hotos25-106.pdf)

## Implications for symbolic evidence — proposed synthesis

The following is a research design inference, not a taxonomy claimed by any one source.

Do not compress an episode directly into a single asserted diagnosis such as `RETRY_STORM`. Preserve a compact evidence structure with separate fields for:

- **Observed temporal structure:** onset, duration, order, lag, repeated cycles, and recovery interval.
- **Population structure:** which participants changed, concurrency or synchronization, and where effects spread.
- **Work accounting:** original requests, attempts, successful work, waiting work, and resource availability.
- **Mechanism evidence:** request lineage, dependency edges, routing changes, retries, controller actions, and health-state changes.
- **Episode hypothesis:** candidate behavior and the observations that support it, contradict it, or remain unavailable.

A useful semantic distinction is between `RETRIES_INCREASED` (observation), `WORK_AMPLIFICATION` (relationship requiring original-versus-total work evidence), and `METASTABLE_FAILURE` (episode-level hypothesis requiring persistence beyond the initiating disturbance and a sustaining mechanism). This hierarchy avoids hiding the diagnosis in the encoder and then measuring whether an LLM repeats it.

For example, an evidence package could say: original demand returned to baseline; repeated attempts remained elevated; successful completions stayed depressed; queues remained occupied; reducing retries was followed by recovery. The LLM can reason over those relations without receiving an asserted final class. Recovery after intervention strengthens a causal interpretation, but should not be encoded as proof from observational telemetry alone.

## A narrow experiment that tests the thesis

Proposed question: **Can compression preserve the evidence needed to distinguish a transient overload that recovers from overload sustained by retries, without giving the LLM the behavior label?**

Use controlled episodes with the same initial disturbance and similar peak resource utilization but different recovery dynamics. Include ordinary high demand and missing retry telemetry as confounders. Compare raw telemetry, a token-matched numerical summary, and symbolic relational evidence. Keep the task, model, and prompt fixed. Evaluate whether the LLM correctly identifies demand versus attempt amplification, orders events, distinguishes recovery from persistence, cites supporting observations, and abstains when required evidence is absent. Measure representation size alongside those semantic outcomes.

The independent assertions are that the encoder preserves these relations, that compression does not manufacture them, and that an LLM can use the retained relations at lower input cost. Root-component recall is a subsequent application test. Neither this experiment nor the cited frameworks establish novelty for the overall system.

## Boundaries

“Failover stampede,” “premature workload return,” and “resource-pool depletion and recovery” were not verified here as canonical taxonomy entries. They should remain provisional descriptions until the actual mechanism and disciplinary term are established. Metastability, cascading propagation, correlation, and synchronization can characterize different aspects of one episode. Classification therefore likely needs multiple axes rather than one flat list of mutually exclusive behaviors.
