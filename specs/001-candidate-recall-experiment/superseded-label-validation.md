> **Superseded planning history.** The active design is descriptive trace compression in [spec.md](spec.md) and [plan.md](plan.md). No experiment results are recorded here.

# Feature Specification: Validate behavior labels before fault localization

**Branch**: `001-candidate-recall-experiment` (retained for continuity)
**Updated**: 2026-09-17
**Status**: Revised scope; planning only
**Input**: Break the oversized experiment into independently testable assertions; do not assume labeling succeeds.

## Goal and scope

Establish whether a proposed behavior encoder can distinguish increasing values from elevated but steady values. Keep the benchmark definition of failure in [ADR 0001](../../docs/adr/0001-benchmark-failure-definition.md); this test neither identifies failures nor evaluates root causes.

The [plan](plan.md) records separately falsifiable assertions A0–A9. Only the direction-versus-level experiment is the immediate implementation scope. Candidate recall is deferred.

## User Scenarios & Testing

### User Story 1 — Validate the meaning of labels (Priority: P1)

As a researcher, I want to distinguish direction from relative level before relying on those labels in diagnosis.

**Independent test**: Present flat/rising series at low/high levels with reference answers fixed before encoding.
**Acceptance**: A high steady series is STEADY and ELEVATED; a low rising series is RISING without being persistently ELEVATED. A high rising series can carry both attributes.

### User Story 2 — Identify which assertion failed (Priority: P2)

As a researcher, I want each assertion to have its own input, independent reference, measurement, and falsifier.

**Independent test**: Audit each assertion in the plan without running a downstream ranker.
**Acceptance**: A labeling failure is visible directly; it cannot be explained away by a better or worse root-component score.

### Edge cases

Flat-high versus rising-low; rising-high; missing/ambiguous evidence; unknown outputs; reused reference labels; sensitivity to scale and noise deferred to their own tests.

## Requirements

- **FR-001**: Distinguish reference behavior annotations, generated symbols, and benchmark fault labels.
- **FR-002**: Freeze the semantic definitions and reference examples before selecting the encoder.
- **FR-003**: Evaluate direction and level independently; allow both RISING and ELEVATED.
- **FR-004**: Keep all eight fixture outcomes, including errors and abstentions.
- **FR-005**: Freeze the encoder before the second set of four examples.
- **FR-006**: Limit claims to the tested domain; no RCA, production-validity, or model-cost claim follows from a fixture pass.
- **FR-007**: Give every later assertion a separate falsifier and independent reference source.

### Key entities

Reference series; analysis segment; independent behavior reference; generated attribute pair; frozen encoder rule; assertion result with domain and limitations.

## Success Criteria

- **SC-001**: All four behavior combinations have defined meanings and unambiguous reference examples.
- **SC-002**: The proposed encoder passes only if all eight unambiguous examples receive both correct attributes without abstention.
- **SC-003**: The result is reviewable as one page of raw plots, references, predictions, and discrepancies.
- **SC-004**: Falsification is a completed experiment outcome; it blocks relying on the failed encoder rather than triggering a larger RCA build.

## Assumptions

This is a plan revision, not execution. A synthetic fixture supplies known behavior, not proof of real-world annotation quality. Independent raw-telemetry annotation is a later experiment. The old candidate-recall implementation artifacts are marked deferred. Full benchmark obligations remain unchanged.


---

# Experiment plan: validate the assertions before applying them to RCA

**Status**: Revised 2026-09-17 following user scope correction; planning only, no tests run.
**Specification**: [spec.md](spec.md)
**Previous plan**: [Deferred candidate-recall integration experiment](deferred-candidate-recall.md)

## What changed

The previous plan bundled symbol validity, segmentation, information retention, trace interpretation, evidence fusion, and causal discrimination into one candidate-recall score. A positive score would not establish which mechanism worked; a negative score would not identify which assumption failed.

Validate each assertion separately. Here, independent means independently falsifiable: a test uses known or separately annotated inputs instead of requiring all upstream implementations to work. These are not claims of statistical independence. Integration still requires all relevant stages to work together.

Three kinds of labels must remain distinct:

- **Behavior reference**: What the observed series does, such as rising or steady. Established by controlled construction or independent annotation of raw observations.
- **Generated symbol**: What our encoder says the series does. This is the object under test, never its own answer key.
- **Benchmark incident label**: Recorded component, fault reason, and occurrence time. Useful for later fault-localization evaluation; it does not certify that any particular metric is rising, high, or causal.

## Independently testable assertions

| ID | Assertion | Small isolated test | Reference and measurement | What would falsify it? |
|---|---|---|---|---|
| A0 | The behavioral vocabulary has operational meaning. | Define RISING and ELEVATED separately; present flat-high, rising-low, rising-high, and flat-low examples, plus an ambiguous example. | Written definitions fixed before encoding. Check whether each example has an unambiguous expected pair of labels or a declared ambiguity. | Definitions cannot distinguish level from direction, or require knowing the fault answer. |
| A1 | The encoder applies those meanings correctly. | Give it controlled series with known slope and level, including counterexamples that share a maximum but differ in trend. | Generator parameters and reference interval, not the encoder's threshold output. Measure the full confusion table and abstentions. | A flat-high series is called RISING; a rising-low series is missed because it never becomes high. |
| A2 | Segmentation preserves when behavior changes. | Supply series with planted change times and isolated spikes; vary the change's position relative to sampling/bin boundaries. | Planted boundaries; measure onset error, interval coverage, extra segments, and missed segments. | Boundaries move arbitrarily with bin alignment, or a spike becomes a sustained episode. |
| A3 | Labels survive irrelevant perturbations but respond to meaningful changes. | Pair a series with unit conversions, small bounded noise, and timestamp shifts; separately change a flat line into a ramp or ramp into a step. | Known transformations. Measure stability on equivalent pairs and sensitivity on changed pairs; count missing/unknown outputs. | Noise or unit choice changes meaning, or a constant labeler passes stability while ignoring real changes. |
| A4 | Symbols preserve specific useful facts while reducing size. | Give a reader/decoder only an independently prepared symbolic packet and ask fixed factual questions: direction, persistence, ordering, onset interval. Compare with raw observations. | Answers fixed from raw data before packet creation. Measure answer agreement AND serialized bytes under the same encoding. | Smaller packets lose a required fact; equal factual accuracy has no size reduction. This does not test root cause or model cost. |
| A5 | Trace representation preserves observed dependency structure. | Use tiny known trace graphs containing siblings, nested spans, orphans, and overlapping children. | Authored parent links and times. Measure edge preservation, missing-link flags, and invented ordering. | Concurrent siblings become a false causal sequence, a missing parent becomes a fabricated link, or start gap is labelled proven network delay. |
| A6 | Cross-channel alignment pairs evidence from the same entity and time. | Hand-author metric and trace episodes with known IDs/clocks, including mismatched IDs and millisecond/second timestamps. | Known mapping and alignment. Count correct joins, false joins, and unresolved mappings. | Different entities/events fuse, or ambiguity silently disappears. No real encoder is needed. |
| A7 | Fusion retains agreement, disagreement, and missingness. | Feed hand-authored channel evidence that agrees, conflicts, duplicates an observation, or omits one channel. | Explicit evidence cases. Check provenance, contradiction flags, duplicate handling, and confidence claims. | Duplication is presented as independent corroboration; conflict or absence becomes agreement. No root ranking is needed. |
| A8 | The representation carries information about fault identity. | Use a small, frozen set of independently labelled fault and matched non-fault/control episodes; compare the proposed representation with matched numerical features. | External incident labels plus independently defined controls. Measure separability and collisions between different events. | Different faults or normal workload changes collapse into indistinguishable signatures. This is an empirical research test, not a coding unit test. |
| A9 | That information improves root-component selection. | Only later run a grouped, held-out ranking comparison with identical candidate budgets and a numerical control. | Benchmark components; paired recall and uncertainty. | No reliable gain, or gain disappears under fair controls. |

A0–A3 concern metric labeling. A4–A7 can be tested with hand-authored correct inputs, independently of the metric encoder. A8 and A9 are later empirical studies. Passing fixture tests establishes behavior within their stated domain; it does not establish validity on production telemetry.

## The actual first experiment: distinguish direction from level

**Question**: Can a proposed symbolizer distinguish an increasing series from an elevated but steady series?

**Why this comes first**: The former plan defined RISE by an amplitude band. That does not establish increasing behavior. Fault ranking would conceal this semantic mistake.

**Scope**: One metric, one known reference interval, two independent attributes, one labeler. No fault labels, incident loader, traces, fusion, topology, shortlist, or LLM.

### Reference examples

Use an explicitly supplied stable reference around value 10. Construct four noiseless 12-sample analysis segments:

| Segment | Values | Expected direction | Expected relative level |
|---|---|---|---|
| Low and steady | 10 repeated | STEADY | BASELINE |
| High and steady | 30 repeated | STEADY | ELEVATED |
| Low and rising | Evenly increases from 10 to 15 | RISING | Not persistently ELEVATED |
| High and rising | Evenly increases from 30 to 40 | RISING | ELEVATED |

For this fixture only, ELEVATED means at least 10 of 12 samples exceed 20; RISING refers to a sustained upward trend rather than level. The noiseless ramps increase at every step and the flat lines do not increase at all, so no fitted noise threshold is needed for the reference answers. These are experimental definitions, not universal CPU, latency, or failure thresholds. Freeze them before selecting an implementation.

The labeler receives the reference and observations, but not the generator class or expected labels. It outputs a direction and relative-level attribute separately, plus UNKNOWN where unsupported. RISING and ELEVATED can both be true. Do not force them into mutually exclusive states.

### Procedure and stopping rule

1. Write the definitions and expected labels before writing or configuring the encoder.
2. Render the four segments together to make the semantic distinction reviewable.
3. Run one simple candidate encoder; record both attributes, including UNKNOWN.
4. Freeze it and test another four series in the same four classes, with changed magnitudes and ramp slopes that remain clearly inside the specified classes. Fix their values and references before running; do not tune on these results.
5. Report all eight classifications. The local gate is 8/8 correct attribute pairs with zero abstentions on these unambiguous fixtures. Any failure rejects this encoder for this elementary domain and identifies the failed assertion. This is a counterexample check, not a population accuracy estimate.
6. Stop here. A pass authorizes a separate A3 nuisance/sensitivity experiment and A2 onset experiment; it does not authorize a claim about fault detection, causal localization, or real-data labeling accuracy.

**Deliverable**: One page showing eight raw-series plots, reference labels, generated labels, mismatches, and the encoder's declared rule. No generalized framework is needed. Suggested timebox: 30–45 minutes for a throwaway test after task definition, not a promise about a full system.

## Real-data bridge, after the elementary tests

Before claiming labeling works on telemetry, select a small set of raw metric segments without looking at incident answers. Have behavior annotations recorded from raw plots using the frozen vocabulary before revealing encoder outputs. Record annotator identity, ambiguities and, if multiple reviewers are available, disagreement. Do not use a second copy of the encoding rule as the independent annotation source.

Report agreement, unknown rate, and disagreements by behavior class. Annotation disagreement challenges A0; encoder disagreement with clear references challenges A1. Label preservation under nuisance changes challenges A3. Keep this as its own experiment. Benchmark cause labels remain evaluator-only for A8/A9 and cannot settle behavior-label disagreements.

## Evidence and governance

Every assertion gets its own result: not tested, supported within stated conditions, falsified, or inconclusive. Record input provenance, reference provenance, frozen rule, observations, and limits. No aggregate pass score can hide a failed assertion. The assertions above are a research backlog, not tasks to implement together.

This revision follows the user's instruction to reduce the first experiment. It overrides earlier scheduling language in the constitution/ADR that calls candidate recall the first experiment; the benchmark failure definition and final deliverable remain unchanged. Scope exception: full routed-agent evaluation, Docker/submission outputs, and candidate recall are deferred to the later integration work. Owner: project maintainer. Follow-up: reconcile the first-experiment wording when those governance documents are next amended. No change to benchmark eligibility is implied.

Next implementation planning should generate tasks only for the eight-series direction-versus-level test. The old five-arm experiment and its CLI/data model are archived/deferred, not prerequisites for this test. No empirical outcome has been claimed.
