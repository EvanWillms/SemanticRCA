# Research handoff prompt — existing taxonomies for reliability behaviors

## Role

You are conducting a **targeted literature and standards review** to determine whether there are already established taxonomies for the kinds of system behaviors we are considering under the working concept **Reliability Activity Recognition**.

The goal is **not** to validate a preferred framing or invent a new taxonomy. The goal is to find the strongest existing classifications, vocabularies, ontologies, failure-pattern catalogs, and behavior taxonomies that could either:

1. supply an existing taxonomy we should reuse;
2. provide dimensions from which a defensible taxonomy could be composed;
3. show that the proposed concept is already well covered under different terminology; or
4. establish a genuine gap between existing fault taxonomies and higher-order temporal/system-behavior taxonomies.

## Current research context

The immediate hackathon thesis is:

> **A multimodal symbolic evidence layer for efficient, explainable infrastructure root-cause analysis.**

The longer research direction is:

> **Continuous recognition of emergent reliability behaviors in distributed systems from fused telemetry streams.**

The motivating distinction is between identifying a **fault** and identifying a **temporally extended system behavior**.

Examples of candidate behaviors include:

- failover stampede;
- cascading workload migration;
- retry amplification;
- thundering-herd behavior;
- coupled-controller oscillation;
- scale-up / scale-down hunting;
- repeated recovery and re-failure;
- premature workload return after recovery;
- resource-pool depletion and recovery;
- shared-fate collapse;
- correlated failover;
- overload propagation;
- cascading degradation;
- synchronized remediation;
- pathological feedback between independently reasonable controllers.

Do **not** assume these labels are correct or novel. Search for the terminology used by existing disciplines.

## Central research question

> **What existing taxonomies classify temporally extended reliability behaviors, failure propagation patterns, control-system pathologies, or population-level dynamics in distributed computing infrastructure?**

A particularly important distinction to preserve is:

### Fault taxonomy

Examples:

- CPU saturation;
- memory exhaustion;
- packet loss;
- process crash;
- disk failure;
- configuration error.

These classify **what went wrong with a component**.

### Reliability-behavior taxonomy

Examples:

- cascading failure;
- retry storm;
- oscillatory control;
- synchronized failover;
- recurrent degradation after recovery.

These classify **how the system behaves over time as components, workloads, and controllers interact**.

We need to know how much prior work exists on the second category.

---

# Research areas to search

Investigate these literatures independently before attempting synthesis.

## 1. Distributed systems and cloud reliability

Look for:

- failure taxonomy;
- incident taxonomy;
- cascading failure taxonomy;
- fault propagation taxonomy;
- distributed-system failure modes;
- cloud outage classifications;
- microservice failure patterns;
- service dependency failure propagation;
- recovery failure patterns;
- resilience antipatterns;
- performance antipatterns.

Prioritize:

- ACM;
- IEEE;
- USENIX;
- SOSP;
- OSDI;
- NSDI;
- EuroSys;
- SRE literature;
- large-scale production incident studies.

## 2. Kubernetes and autonomic/cloud control systems

Search specifically for classifications of:

- autoscaling instability;
- controller interference;
- control-loop interaction;
- control-loop oscillation;
- Kubernetes controller conflicts;
- scheduler/autoscaler interaction;
- unstable resource management;
- feedback-loop antipatterns;
- remediation loops;
- self-healing failure modes.

Distinguish an individual controller being poorly tuned from **multiple correct controllers producing emergent instability**.

## 3. Control theory

Find established classifications for:

- oscillation;
- hunting;
- overshoot;
- limit cycles;
- positive feedback;
- delayed-feedback instability;
- coupled-loop interaction;
- controller saturation;
- integral windup;
- mode switching;
- hybrid-system instability;
- interacting decentralized controllers.

The goal is not to import control-theory terminology indiscriminately. Determine which categories plausibly transfer to cloud infrastructure.

## 4. Queueing, congestion, and network systems

Search for recognized patterns such as:

- congestion collapse;
- synchronization;
- global synchronization;
- retransmission storms;
- retry storms;
- incast;
- traffic oscillation;
- queue instability;
- load shifting;
- load-balancing instability;
- hotspot migration;
- congestion waves.

Determine whether these literatures already contain behavior-level taxonomies rather than isolated mechanisms.

## 5. Dependable and fault-tolerant computing

Search canonical dependability literature for distinctions among:

- fault;
- error;
- failure;
- propagation;
- recovery;
- recurrence;
- common-mode failure;
- correlated failure;
- cascading failure;
- Byzantine behavior where relevant.

Start with established dependability taxonomies such as Avizienis/Laprie-style work, then trace later extensions.

Determine whether these taxonomies classify **temporal interaction patterns** or primarily failure origins/effects.

## 6. Complex systems and resilience engineering

Search for:

- cascading failures;
- systemic risk;
- resilience patterns;
- common-cause failure;
- correlated failure;
- recovery dynamics;
- network robustness;
- critical transitions;
- tipping points;
- propagation processes;
- synchronization phenomena.

Be careful to distinguish useful formal concepts from metaphorical analogy.

## 7. Population dynamics / ecology-inspired computing

Look for actual computing literature using concepts such as:

- resource competition;
- carrying capacity;
- population migration;
- ecological stability;
- diversity and resilience;
- predator-prey control analogies;
- resource-patch depletion;
- population synchronization;
- distributed adaptation.

The question is whether "Reliability Ecologist" has technical predecessors beyond metaphor.

## 8. Performance engineering and performance antipatterns

Search for named catalogs and taxonomies involving:

- thrashing;
- bottleneck migration;
- convoy effects;
- resource contention;
- cyclic overload;
- burst amplification;
- work amplification;
- retry amplification;
- cache stampede;
- fan-out amplification;
- load imbalance.

Look especially for **named temporal patterns** that could function as activity classes.

## 9. Chaos engineering and resilience testing

Search:

- failure scenario taxonomies;
- chaos experiment catalogs;
- fault models;
- resilience scenario catalogs;
- recovery-pattern taxonomies;
- incident archetypes.

Determine whether these classify injected faults only or the **resulting system dynamics**.

## 10. AIOps and observability research

Look for:

- anomaly taxonomies;
- incident clustering;
- fault propagation graphs;
- temporal motifs;
- root-cause pattern mining;
- failure episode clustering;
- distributed trace motifs;
- event sequence mining;
- process mining over telemetry.

Pay particular attention to any work that treats an incident as a recurring **temporal pattern across multiple modalities**.

## 11. Human activity recognition / symbolic time-series analysis

This is methodological precedent, not the primary taxonomy source.

Search for how HAR distinguishes:

- atomic actions;
- composite activities;
- continuous activities;
- overlapping activities;
- activity episodes;
- transition states;
- hierarchical activity taxonomies.

Determine whether the **activity hierarchy** offers a useful structural model for infrastructure behavior:

```text
signal
→ primitive
→ action
→ composite activity
→ episode
```

Possible infrastructure analogue:

```text
metric/event
→ local state transition
→ component behavior
→ multi-component activity
→ incident episode
```

---

# Specific terminology search

Search exact and related phrases including:

- "failure behavior taxonomy"
- "system behavior taxonomy reliability"
- "distributed systems failure pattern taxonomy"
- "failure propagation pattern"
- "cascading failure taxonomy"
- "resilience pattern taxonomy"
- "recovery failure taxonomy"
- "fault propagation taxonomy"
- "cloud incident taxonomy"
- "microservice failure taxonomy"
- "performance antipattern taxonomy"
- "distributed systems antipatterns"
- "controller interaction instability"
- "multiple control loop interaction"
- "autoscaling oscillation"
- "load balancing oscillation"
- "retry storm"
- "retry amplification"
- "thundering herd taxonomy"
- "congestion collapse"
- "common mode failure"
- "correlated failure"
- "synchronized failure"
- "failover storm"
- "cascading overload"
- "failure cascade"
- "resource contention patterns"
- "temporal failure motifs"
- "distributed trace motifs"
- "incident motifs"
- "system dynamics patterns cloud"
- "self-healing antipatterns"
- "autonomic computing failure modes"
- "MAPE-K failure taxonomy"
- "feedback loop instability cloud computing"
- "emergent behavior distributed systems"

Do not limit the search to these terms.

---

# Questions to answer for every candidate taxonomy

For each source, extract:

### Identity

- taxonomy or framework name;
- authors;
- publication;
- year;
- domain;
- canonical citation;
- stable URL/DOI.

### What is being classified?

Choose or describe:

- fault cause;
- failure manifestation;
- affected component;
- incident type;
- propagation pattern;
- recovery behavior;
- control behavior;
- temporal sequence;
- population/system dynamics;
- performance pathology;
- other.

### Unit of classification

Examples:

- component;
- request;
- service;
- node;
- dependency edge;
- controller;
- workload;
- cluster;
- system episode.

### Temporal structure

Does the taxonomy describe:

- instantaneous states;
- transitions;
- ordered sequences;
- repeated cycles;
- onset/offset;
- propagation;
- recurrence;
- oscillation?

### Interaction structure

Does it represent:

- one component;
- pairwise dependency;
- many interacting components;
- multiple controllers;
- workload/resource populations;
- shared environmental constraints?

### Causality

Does it classify:

- symptoms;
- causal mechanisms;
- both;
- merely correlated patterns?

### Observability requirements

What signals would be needed to recognize the class?

Examples:

- metrics;
- logs;
- traces;
- topology;
- controller actions;
- scheduler events;
- workload placement;
- user/job data.

### Formalism

Is it represented as:

- hierarchy;
- ontology;
- graph;
- state machine;
- event sequence;
- fault tree;
- Petri net;
- causal graph;
- control model;
- prose catalog;
- pattern language.

### Empirical basis

Was it derived from:

- production incidents;
- controlled experiments;
- simulation;
- theoretical models;
- practitioner synthesis?

### Reuse potential

Could the taxonomy be:

- directly adopted;
- partially adopted;
- used only as a vocabulary source;
- unsuitable for our problem?

---

# Build a taxonomy comparison matrix

Construct a table with at least these columns:

| Taxonomy / sourceDomainPrimary unitFault vs behaviorTemporal?Multi-component?Controller interaction?Population/resource dynamics?Production-derived?Relevance |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- |

Do not rank sources numerically unless the underlying evidence supports such a comparison.

---

# Look explicitly for hierarchy candidates

Test whether existing literature supports some version of this hierarchy:

```text
Level 0 — Observation
metric, log event, span, scheduler event

Level 1 — Local state
CPU pressure, elevated latency, retry burst

Level 2 — Component behavior
degradation, restart, recovery, saturation

Level 3 — Interaction behavior
retry amplification, workload migration, dependency propagation

Level 4 — Population/control behavior
stampede, oscillation, synchronized failover, concentration cascade

Level 5 — Reliability episode
complete temporally bounded incident/recovery behavior
```

Do **not** accept this hierarchy simply because it is convenient.

For each level:

- find precedent;
- identify alternative terminology;
- identify sources that contradict or collapse levels;
- state whether the level appears established, inferential, or novel.

---

# Particular candidate behaviors to trace

For each candidate below, find the **canonical existing term**, strongest prior literature, and whether it is already part of a taxonomy.

### A. Synchronized migration / failover

Possible labels:

- failover storm;
- thundering herd;
- synchronized failover;
- hotspot migration;
- cascading overload.

### B. Retry amplification

Possible labels:

- retry storm;
- retry amplification;
- positive feedback;
- overload cascade.

### C. Repeated recovery and immediate relapse

Possible labels:

- flapping;
- oscillation;
- unstable recovery;
- hysteresis failure;
- recurrent failure.

### D. Coupled-controller oscillation

Possible labels:

- hunting;
- control-loop interference;
- interacting-loop instability;
- limit cycle;
- policy oscillation.

### E. Shared-fate collapse

Possible labels:

- common-mode failure;
- correlated failure;
- common-cause failure;
- hidden dependency failure.

### F. Resource-pool exhaustion after displacement

Possible labels:

- cascading overload;
- load concentration;
- resource depletion;
- congestion collapse.

### G. Cascading degradation across dependency graph

Possible labels:

- cascading failure;
- fault propagation;
- failure propagation;
- dependency cascade.

For each, identify whether our proposed label should be retained, replaced by established terminology, or treated as a user-facing alias.

---

# Important novelty boundary

Do not conflate the following:

### Already-established areas

- fault taxonomies;
- anomaly taxonomies;
- root-cause classification;
- symbolic time-series representation;
- multimodal telemetry fusion;
- distributed trace analysis;
- cascading-failure research;
- control-loop stability analysis.

### Candidate gap

The possible gap is specifically:

> **A practical taxonomy of temporally extended, multi-component reliability activities that can be continuously recognized from heterogeneous observability streams and used as an intermediate abstraction between raw telemetry and root-cause/remediation reasoning.**

The review should determine whether this gap is real.

Search aggressively for work that invalidates it.

---

# Research quality requirements

Prefer:

1. canonical papers;
2. standards and reference models;
3. peer-reviewed systems/control/dependability literature;
4. major industry incident studies;
5. well-established practitioner pattern catalogs.

Use vendor blogs only when they introduce a concrete named operational pattern not otherwise documented.

For each major conclusion:

- cite primary sources;
- distinguish the source's terminology from our interpretation;
- do not attribute "taxonomy" status to an ad hoc list unless authors explicitly present it that way;
- distinguish fault **causes**, fault **effects**, and system **behaviors**;
- distinguish single-controller instability from emergent multi-controller behavior;
- distinguish metaphorical ecological language from formal population-dynamics models.

---

# Deliverables

Produce five artifacts.

## 1. Executive finding

Answer in no more than \~500 words:

> **Does an existing taxonomy already cover Reliability Activity Recognition's proposed behavior classes?**

Use one of these evidence-based conclusions, or a more precise alternative:

- an established taxonomy already exists;
- several partial taxonomies exist but no unified one was found;
- the space is fragmented across distinct disciplines;
- the proposed framing mostly renames established concepts;
- a meaningful taxonomy gap appears to remain.

Do not force one of these conclusions.

## 2. Taxonomy landscape

Organize discovered taxonomies by discipline and explain what each classifies.

## 3. Crosswalk

Map our provisional concepts to existing terms:

\| Provisional concept | Existing term(s) | Discipline | Canonical source | Same concept? | Important distinction |
\|---|---|---|---|---|

## 4. Candidate synthesis

Only after completing the literature review, propose the **smallest defensible synthesis** that could support Reliability Activity Recognition.

Mark each category:

- **Established** — directly supported by existing taxonomy.
- **Adapted** — established concept transferred to infrastructure behavior.
- **Synthesized** — composed from multiple prior frameworks.
- **Potentially new** — no sufficiently close classification found.

Every "potentially new" item must include the search evidence supporting that judgment.

## 5. Research gaps and falsifiers

List:

- strongest evidence that this research direction is already occupied;
- strongest evidence that existing taxonomies stop at component faults;
- areas requiring deeper review;
- terminology we should stop using;
- concepts that appear promising enough for empirical study.

---

# Final test

The review succeeds if it lets the next researcher answer:

> **When we observe a sequence such as degradation → migration → destination saturation → secondary failure, what established scientific vocabulary should we use for that behavior, what taxonomy does it belong to, and what—if anything—is genuinely missing from the existing literature?**

Do not optimize for confirming the "Reliability Ecologist" or "Reliability Activity Recognition" framing. Optimize for finding the terminology and taxonomy the field already has.