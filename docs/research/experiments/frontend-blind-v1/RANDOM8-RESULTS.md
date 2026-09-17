# Eight random blind trials: results and output review

**Result: 2/8 requested answers were fully correct; mean official score was 25%, versus 6.25% for trace-only predictions.** Final exact component accuracy was 1/9, reason accuracy 2/7, and occurrence-time accuracy 0/3. The two successes were case 29 (frontend network latency) and case 32 (process termination reason). The observations show that packaged anomaly scoring is readily executable, but this frontend-first investigation procedure did not reliably solve blind diagnosis.

Eight prompts were randomly selected with seed 42 before opening labels: **3, 6, 14, 17, 29, 32, 36, 48**. They contain twelve incident slots across eight unique windows, six on March 20 and two on March 21. All used independent Luna-high investigators and unchanged PyOD MAD/Isolation Forest scoring alongside raw-duration sorting. The original 69-prompt run was stopped at the user's request; completed pilots 0–2 are excluded.

The [population amendment](RANDOM8-AMENDMENT.md) supersedes the original 69-case gate. All eight trace-only and final seals passed before labels were opened. The coordinator's evidence-quality reviews below were recorded before unblinding. Original predictions remain unchanged.

## Official requested-field scores

| Stage | Prompts | Mean official score | All requested fields correct |
| --- | --- | --- | --- |
| trace_only | 8 | 0.0625 | 0 |
| final | 8 | 0.2500 | 2 |

| Stage | Requested field | Correct / labelled | Accuracy |
| --- | --- | --- | --- |
| trace_only | occurrence_time | 0/3 | 0.0% |
| trace_only | component | 1/9 | 11.1% |
| trace_only | reason | 0/7 | 0.0% |
| final | occurrence_time | 0/3 | 0.0% |
| final | component | 1/9 | 11.1% |
| final | reason | 2/7 | 28.6% |

Official scores are equally weighted per prompt and rounded by the unchanged official scorer. These prompts do not request a full time/component/reason tuple, so a fully correct requested answer is not evidence that all three fields were solved.

## Per-case predictions and answers

| Case | Task | Scored fields | Expected | Final prediction | Trace score | Final score |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | task_6 | component, reason | node-1 / node memory consumption | node-5 / node disk space consumption | 0.0 | 0.0 |
| 6 | task_6 | component, reason | node-1 / node disk read I/O consumption<br>recommendationservice / container CPU load | recommendationservice-2 / container memory load<br>recommendationservice-2 / container memory load | 0.0 | 0.0 |
| 14 | task_5 | occurrence_time, component | 2022-03-20 17:12:41 / node-4<br>2022-03-20 17:23:19 / paymentservice | 2022-03-20 17:00:00 / node-6<br>2022-03-20 17:17:00 / node-5 | 0.0 | 0.0 |
| 17 | task_2 | reason | container memory load<br>container network packet corruption | container network latency<br>container CPU load | 0.0 | 0.0 |
| 29 | task_6 | component, reason | frontend-1 / container network latency | frontend-1 / container network latency | 0.5 | 1.0 |
| 32 | task_2 | reason | container process termination | container process termination | 0.0 | 1.0 |
| 36 | task_5 | occurrence_time, component | 2022-03-21 01:44:35 / node-5 | 2022-03-21 01:30:05 / checkoutservice-1 | 0.0 | 0.0 |
| 48 | task_3 | component | productcatalogservice<br>checkoutservice | productcatalogservice-1<br>productcatalogservice-1 | 0.0 | 0.0 |

## Detector discovery

All three arms return 0/9 exact component hits at request budgets 1, 3, 5, and 10, for both immediate attribution and broader reachability. The complete counts and candidate lists are retained in metrics.json.

**The all-zero exact discovery scores do not provide a useful comparison of detector quality in this sample.** Of nine component labels, four are nodes, four are whole-service names, and one is the frontend root itself. The metric compares descendant replica span IDs: nodes are not spans, service names do not equal replica names, and the frontend root is excluded from descendant lists. The extracted lists are nonempty and contain 10–24 reachable replica IDs at budget ten; this is an evaluation-granularity limitation, not evidence that no useful dependency was found. Only the six selected prompts with component labels enter this denominator. Broad reachability also contains routine dependencies and is weaker evidence than attribution of delay. No post-hoc identity normalization or rescoring was applied.

Every paired arm contrast consequently has zero wins, zero losses, and six ties. These ties cannot establish detector equivalence or support a best-in-class claim.

## Absolute latency and coverage

| Case | Frontend requests | Eligible requests | Duration top-1 ms | MAD top-1 ms | IForest top-1 ms |
| --- | --- | --- | --- | --- | --- |
| 3 | 8028 | 8028 | 154.558 | 94.422 | 94.422 |
| 6 | 9204 | 9204 | 1300.425 | 1300.425 | 1300.425 |
| 14 | 4723 | 4723 | 153.242 | 0.921 | 0.921 |
| 17 | 5591 | 5590 | 60002.808 | 43359.294 | 3384.224 |
| 29 | 3027 | 3027 | 4985.286 | 4592.084 | 3919.199 |
| 32 | 9182 | 9182 | 26860.170 | 18978.996 | 13769.611 |
| 36 | 2697 | 2697 | 151.500 | 107.869 | 107.869 |
| 48 | 3825 | 3825 | 6100.103 | 5504.144 | 812.580 |

In case 14, MAD and Isolation Forest choose a 0.921 ms request against a 0.172 ms reference median (0.749 ms excess), while raw sorting selects 153.242 ms. This is a real relative departure, but it illustrates why an unusual request is not automatically an important delay. No post-hoc threshold was added.

## Review of the sealed outputs

### Case 3

Pre-label review: Executed numerical trace/metric analysis and explicit pod-host mappings preserved Trace-only abstention and live alternatives retained

Limitations: The final disk-space reason is inferred from inode-count growth; no inode-capacity or free-disk-pressure evidence establishes exhaustion or explains latency causally Median inode-count change is about0.00885% on node5, so a high MAD departure alone does not establish an operationally important resource change One of the four cited top-duration symptoms precedes the proposed10:40 onset; late high checkout traces are not unique to the asserted onset Final JSON and evidence say8 metric calls but persistent log records7; preserve original and use ledger counts

### Case 6

Pre-label review: All three detector arms identify recommendation-service calls, with explicit receiver links and substantial latency Actual executable analysis and14 bounded retrieval responses preserved; memory limits and negative counters reported

Limitations: Both incident slots use the same replica and reason; two metric peaks do not alone establish two independent failures Synchronized resource changes occur on all three replicas;7 of11 selected receivers being replica2 does not prove that replica initiated both incidents Memory rise is associated with increased threads and long client calls; memory-load causation is not established by usage alone Report calls client-minus-receiver interval receiver-uncovered time; this differs from uncovered time inside a receiver span and must remain distinct Final incident evidence pointers are incorrect: retrieval11 series30 is productcatalogservice0 working-set memory, series32 is recommendationservice0 working-set memory, and retrieval14 series0 is productcatalogservice0 container_last_seen; none directly supports the claimed replica2 memory incidents.

### Case 14

Pre-label review: Explicitly rejects tiny high-MAD requests as failure evidence Uses recorded host mappings, interval unions, bounded targeted retrieval and qualified low-confidence hypotheses

Limitations: Load averages below1 and CPU-system samples around4.49 do not establish CPU saturation without units/core capacity or scheduling evidence; baseline shift alone is weak causal evidence The17:00 onset is the query boundary and is not an independently isolated initiating event Two separate CPU incidents are inferred from different hosts and timepoints without strong fault episode separation

### Case 17

Pre-label review: Strong delay localization to the email dependency:43-60s client calls with tiny or absent recorded receivers Actual error-filtered DNS and timeout logs plus nonzero CPU-throttling measurements provide more mechanism evidence than a generic resource-score departure Explicitly records alternatives and corrected execution errors

Limitations: DNS/name-resolution failure is not itself a measurement of injected container network latency; a shared DNS/mesh issue remains viable CPU signals occur across three replicas; timing correlation does not uniquely identify replica2 or separate two initiating failures Trace evidence references use trace IDs as array indexes and therefore do not resolve as JSON pointers Reported10 metric calls differs from9 actual metric calls in persistent log

### Case 29

Pre-label review: Repeated roughly353ms client-minus-receiver excess across325 linked calls, plus3.9s frontend proxy timings and5-7ms downstream processing, supports a much more specific delay-path hypothesis Temporal cluster derived from multiple high-duration requests rather than a single selected request Explicit alternatives and absence of direct network-latency KPI retained; retrieval within8 metric/10 log limits

Limitations: Network latency remains inferred from elapsed-call gaps and proxy observations; client-side scheduling, application waits, or transport behavior are not experimentally separated Inferred occurrence is symptom-cluster onset, not an independently identified injection/event timestamp

### Case 32

Pre-label review: Repeated13-19s cartservice0 receiver stalls coincide with a large memory/RSS discontinuity and a targeted upstream connection-reset record Checks exact mapped container identity and separates an earlier long checkout trace as an alternative Significant absolute state change plus temporal and log evidence is stronger than a high MAD resource score alone

Limitations: Process termination/replacement is inferred; no direct lifecycle/start-time change is supplied, and two samples sharing a timestamp do not by themselves establish before/after ordering Confidence0.92 is high relative to the acknowledged missing lifecycle event Four of five final evidence refs use trace IDs or KPI names as array indexes and do not resolve as JSON pointers; raw source files are present for manual verification

### Case 36

Pre-label review: Quantifies repeated downstream client-minus-receiver differences and distinguishes shared checkout behavior from a unique replica Retains low confidence and missing direct network metrics; records corrected API path error

Limitations: Final onset is exactly the earliest selected slow-request timestamp at the query boundary; no new initiating-event evidence justifies changing trace-only onset abstention to a precise occurrence time All three checkout replicas show similar paths, so choosing checkoutservice1 as the initiating component is weakly identified The50-60ms gaps are not compared with the same downstream-operation gap distribution in the reference period; recurring client duration alone does not establish new network latency

### Case 48

Pre-label review: Strong absolute CPU raw-value increase across Product Catalog replicas overlaps long linked receiver spans Honest onset abstention because two independent temporal episodes were not identified Counter semantics and missing telemetry remain explicit; denied direct-node call preserved and mapped node evidence retained

Limitations: Duplicates the same component in both incident slots while acknowledging only one supported episode; it does not establish two root causes Largest median departure on replica1 is weak evidence of initiating replica when all replicas show synchronized spikes Trace-ID/KPI-name array references do not resolve as JSON pointers; final claims require manual source lookup Metric counts should distinguish12 successful metric retrievals plus1 denied attempt from1 successful log call

An [independent Luna-high audit](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/orchestration/independent_audit.md) of six completed cases, performed without labels or the coordinator's review notes, confirmed the citation and causal-attribution issues. Case 14 additionally cites CPU percentage where its narrative relies on CPU-system samples. Case 17's first DNS citation belongs to emailservice-0, while its first prediction names emailservice-1. These are substantive evidence-quality issues even when nearby source files contain relevant observations.

## What failed, and what worked

The strongest successful path was case 29: repeated roughly 353 ms client-call excess across many downstream operations, short receiver processing, and corroborating proxy timings pointed to frontend network latency. Case 32 supplied a coherent memory-discontinuity/connection-reset timeline and matched the requested process-termination reason, although a direct lifecycle event was absent and citations need manual repair outside the sealed result.

The failures include wrong resource mechanisms inferred from small changes (cases 3 and 14), symptom timing substituted for causal onset (case 36), unsupported splitting of one correlated episode into two failures (cases 6 and 48), and confusion among different network fault mechanisms (case 17). Identity granularity also matters: the labels name recommendationservice in case 6 and productcatalogservice plus checkoutservice in case 48, while the outputs choose individual replicas. Those family-level associations are useful leads, but normalizing them would not fix the wrong reasons, the missed node incident, or the missing second service. The official results above remain unchanged.

## Comparison with the short-window baselining report

The user supplied [Short-window baselining: execution and analysis](/Users/nonadmin/Development/SymbolicRCA/data/experiments/short-window-baselining-v1/final-report.md). It was read after all eight outputs were sealed. Its conclusions and these results answer different questions and are compatible.

| Dimension | Short-window study | This eight-case trial |
| --- | --- | --- |
| Question | Can a short reference support qualified latency comparisons? | Can frontend-first investigation recover requested fault fields? |
| Frozen reference | 5 minutes, pooled C1 recorded operation-presence sets; parallel C0 structural channel | 30 minutes, pooled recorded operation/count signatures |
| Reported quantity | Median and signed absolute excess; support and stability screens | Raw duration, signed cohort MAD, pooled IForest; sealed diagnoses |
| Eligibility | Count/time-concentration rules, completion filtering, explicit unknown structure, interval-width screen | At least 20 references, positive median, nonzero MAD; no comparable bootstrap-width gate |
| Empirical coverage | 9,763/9,802 core comparisons (99.60%); 50,366/50,933 confirmation primary comparisons (98.89%) | 46,276/46,277 full-window requests eligible for cohort scores |
| Outcome claim | Broad descriptive availability, with important abstention/stability failures; no RCA evaluation | 2/8 requested answers fully correct; no request-level anomaly accuracy or false-positive estimate |

The coverage percentages are not directly comparable: the request slices, cohort definitions, completion rules, and stability requirements differ. The short-window study's safeguards and signed absolute-excess reporting address weaknesses visible here, especially tiny high-relative-score requests and reference contamination. They do not establish healthy references, incident sensitivity, or diagnosis accuracy. Switching from 30 to 5 minutes was not tested in this trial, so no improvement from that change is claimed.

## Execution and reproducibility

| Case | Status | Minutes dispatch to seal | Metric calls | Log calls | Evidence | Executed code |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | completed | 10.2 | 7 | 2 | [evidence](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/3/evidence.md) | [code](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/3/investigate.py) |
| 6 | completed | 9.1 | 12 | 2 | [evidence](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/6/evidence.md) | [code](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/6/investigate.py) |
| 14 | completed | 11.1 | 14 | 7 | [evidence](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/14/evidence.md) | [code](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/14/investigate.py) |
| 17 | completed | 10.9 | 9 | 3 | [evidence](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/17/evidence.md) | [code](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/17/investigate.py) |
| 29 | completed | 9.0 | 8 | 10 | [evidence](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/29/evidence.md) | [code](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/29/investigate.py) |
| 32 | completed | 10.6 | 20 | 9 | [evidence](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/32/evidence.md) | [code](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/32/investigate.py) |
| 36 | completed | 8.4 | 7 | 1 | [evidence](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/36/evidence.md) | [code](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/36/investigate.py) |
| 48 | completed | 9.1 | 12 | 1 | [evidence](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/48/evidence.md) | [code](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/cases/48/investigate.py) |

Machine-recorded retrieval counts and dispatch-to-seal times take precedence over inconsistent agent-written summaries. Failed analysis commands and corrected runs remain in each run.json. Model token usage and dollar cost were not available.

- [Evaluation metrics](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/random8-results/metrics.json)
- [Per-case score CSV](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/random8-results/results.csv)
- [Unblinding audit](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/random8-results/unblinding.json)
- [Pre-label review records](/Users/nonadmin/Development/SymbolicRCA/data/experiments/frontend-blind-v1/orchestration/review_before_labels.jsonl)

Reproduce from the repository root with the pinned Python environment and PYTHONPATH set to the repository root:

```sh
/private/tmp/symbolicrca-pyod-venv/bin/python docs/research/experiments/frontend-blind-v1/review_random8.py gate
/private/tmp/symbolicrca-pyod-venv/bin/python docs/research/experiments/frontend-blind-v1/review_random8.py evaluate
/private/tmp/symbolicrca-pyod-venv/bin/python docs/research/experiments/frontend-blind-v1/collect_random8.py
```

## Limits

This is an exploratory development sample with incident-conditioned windows and potentially contaminated reference traffic. There are no independently labelled healthy windows or request-level anomaly labels, so false-positive rates and anomaly-classification accuracy are not measured. Adjacent intervals share traffic. Eight cases from one deployment cannot establish a generally best detector, production readiness, or causal identification. The final investigation combines all three arms, so final diagnosis accuracy cannot be credited to one detector.
