# SymbolicRCA evidence and benchmark diagnosis

The domain is describing telemetry for comparison and diagnosing incidents designated by the supplied Track 1 benchmark.

## Language

**Failure**:
A labelled benchmark incident represented by its occurrence time, root-cause component, and fault reason. Occurrence time means the fault's start time.
_Avoid_: Outage or SLO breach as a synonym or prerequisite.

**Incident tuple**:
The associated when, where, and why of one failure. A task requests a projection of this tuple; fields from separate failures must not be mixed.

**Investigation scope**:
The deployment, bounded time window, requested fields, and supplied failure count. These constrain the investigation without providing telemetry evidence for the diagnosis.

**Descriptive symbol**:
A stable, defined statement about an observation or observed relationship, with its context and evidence. It does not by itself assert unusualness, success, or cause.
_Avoid_: Treating a semantic token as one model tokenizer token.

**Evidence packet**:
A compact description of observed execution, retaining the relationships, measurements, uncertainty, and provenance needed for specified questions.

**Structural pattern**:
A recurring arrangement of observed operations and relationships. Its recurrence alone establishes neither retry behavior nor healthy execution.

**Reliability behavior**:
A temporally extended pattern of interacting components, workloads, or controllers. A behavior description is distinct from an explanation of its sustaining mechanism or originating fault.

**Reference cohort**:
A set of observations or executions selected using explicit context and eligibility criteria, including their allowed variation. A typical cohort need not be successful or healthy.

**Baseline**:
A versioned description of reference behavior for a declared context, with its variation, supporting observations, and eligibility limitations. It does not by itself define successful behavior or an acceptable service outcome.

**Recorded-trace coverage**:
The scope and completeness of retrieved span records for an execution within the available telemetry. Complete retrieval does not establish complete instrumentation of that execution.

**Track-1 source snapshot**:
The identified deployment and available telemetry partitions supplied for one investigation or reproducible run. It defines the boundary of evidence available to the agent, not all activity that occurred in the system.

**Trace selection**:
The declared rule for choosing executions to inspect from the available observations. Selection does not define which other records belong to a selected execution.

**Recorded-trace recovery**:
Retrieval of the available span records belonging to a selected execution across the declared source snapshot. Recovery can be complete relative to that snapshot while ancestry or instrumentation remains unresolved.

**Recording component**:
The component identified by a span's raw recording identity. It is not automatically the called service, the target replica, or the root-cause component.

**Frontend root observation**:
A blank-parent span satisfying a declared frontend entry rule in the supplied deployment. Its identity and recorded execution context may remain qualified even when its duration is usable.

**Resource relationship**:
An evidence-supported association between recording entities, logical services, replicas, hosts, or endpoints at an observed time. Its kind distinguishes span ancestry, service dependency, placement, endpoint association, and temporal association.

**Unresolved target**:
The unknown resource identity associated with an observed operation. A known operation name or nearby resource measurement alone does not resolve it.

**Verified success**:
An outcome that satisfies an independently specified criterion, with a verification source and scope. Span completion, lack of logged errors, and absence from a fault window do not establish it.

**Comparison finding**:
A difference between descriptive evidence and an eligible reference cohort under a declared comparison policy. It is a candidate diagnostic signal, not proof of causation.

**Diagnostic hypothesis**:
A proposed incident explanation supported by evidence, with uncertainty and alternatives. The benchmark fault reason and a descriptive behavior label are different concepts.

**Candidate shortlist**:
An ordered set of possible root-cause components. Inclusion of the correct component is only one part of diagnosis.
