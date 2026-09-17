# Python anomaly detector selection for the Case 25 demonstration

Source review: 2026-09-17. This is a library-selection note, not a comparative benchmark.

## Recommendation

Use **PyOD** as the off-the-shelf toolkit. For this univariate, slow-request task, its **MAD** detector directly replaces the existing calculation, while its **IForest** wrapper provides a frozen-reference machine-learning comparator. **ECOD** is another strong empirical-distribution option, but its query-batch behavior below makes it a poorer fit for this particular frozen-reference demonstration. None can honestly be called universally best from this example.

PyOD MAD stores the reference median and median absolute deviation at fit time and reuses them for query scoring. Its absolute score needs a direction rule to prioritize slow requests. The executed demo fits MAD separately to each operation-count cohort, then fits one pooled Isolation Forest on the signed, cohort-standardized reference latencies. This gives the forest a common feature scale without comparing independently fitted forest scores. [MAD official implementation](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/mad.html), [IForest official implementation](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/iforest.html).

ECOD's authors report experiments against eleven baselines on thirty datasets and emphasize computational efficiency and interpretability. That supports trying it; those experiments do not establish superiority on these trace cohorts. [ECOD paper](https://arxiv.org/abs/2201.00382)

## Behavior that matters here

| Choice | Verified behavior | Consequence for this demonstration |
|---|---|---|
| PyOD ECOD | Uses empirical marginal tails; larger scores are more unusual. `contamination` sets the binary-label threshold. | Rank raw scores without presenting an arbitrary contamination setting as a measured incident rate. |
| PyOD ECOD scoring | `decision_function(X)` concatenates the stored training data with `X`, then recomputes ECDFs and skew. It considers both tails. | A query-batch call is transductive: other query requests influence the result. Singleton scoring avoids influence from other query points, but still includes the point being scored. Explicitly enforce the task's slow-only policy. |
| IsolationForest | Uses random tree splits and scores fitted-tree path lengths; lower `score_samples` values mean more abnormal. | Fit only on the earlier interval, negate `score_samples` for descending anomaly ranking, and fix `random_state`. |

Sources: [ECOD official implementation](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/ecod.html), [IsolationForest official API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).

Inference from these implementations: neither detector naturally measures “milliseconds contributed to user delay.” Empirical ranks can tie despite different excess durations. Tree partitions can likewise assign equal scores to different latencies in the same leaves. Report tied ranks honestly and disclose any impact-based tie breaker. A generic outlier detector can prioritize unusually fast observations unless a separate direction rule removes them.

## Experimental policy

Preserve the existing operation-count cohorts and preceding 30-minute reference. Use only latency as the detector input within each cohort; do not include component identity, known onset, or the known trace ID. Keep a minimum reference size rule fixed before reading the ranking. Inspect parent-linked dependencies only after selecting a request. Show the existing median/MAD result alongside the packaged result rather than altering features until they agree.

The existing [case analysis](track-1-case-25-anomaly-discovery.md) records a 6.7-second reference outlier and only 102 reference samples in the selected request's cohort. Therefore this comparison establishes deviation from an observed reference, not health, calibrated significance, or a false-positive guarantee. Different cohort sizes also complicate cross-cohort score comparisons. State these as limitations rather than interpreting a score as a failure probability.

Anomaly detection offers mature reusable implementations, but workload definition, reference contamination, direction of interest, alarm policy, and causal attribution remain separate decisions. The scikit-learn guide explicitly describes unconstrained/high-dimensional outlier detection as challenging and separates outlier detection from novelty detection. [Official user guide](https://scikit-learn.org/stable/modules/outlier_detection.html)
