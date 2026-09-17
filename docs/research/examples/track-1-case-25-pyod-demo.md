# Case 25: off-the-shelf Python anomaly detection

## Outcome

**The detector is commodity software for this example.** Installed PyOD 3.6.6 and ran its packaged MAD detector and Isolation Forest against the actual March 20 trace CSV. Both surface the previously inspected request without using the labelled fault time, component, or trace ID in scoring. This is one retrospective development example, not proof that anomaly detection in general is solved or that one algorithm is universally best.

| Ranking method | Known request's rank | First request duration |
|---|---:|---:|
| Absolute duration, no anomaly model | 1 / 2,729 | 428.249 ms |
| PyOD MAD, signed for slow latency | 1 / 2,729 | 428.249 ms |
| PyOD Isolation Forest, slow-only candidates | 2 / 1,332 | 0.929 ms |

All 2,729 query requests were scored. The forest ranking excludes requests at or below their cohort's reference median; this is a direction filter, not an incident threshold. No alarm labels or probabilities are reported. Its top result, trace `33ac121d12f9d81f70a93424c7312544`, has no recorded direct children, so this trace cannot provide a downstream-service attribution. Its rarity should not be mistaken for substantial user impact.

The PyOD MAD winner is trace `328e653dddef2f29d419a46895d85d12`:

| Measurement | Result |
|---|---:|
| Frontend duration | 428.249 ms |
| Matching reference requests | 102 |
| Reference median | 93.9525 ms |
| Reference MAD | 6.6125 ms |
| Excess over median | 334.2965 ms |
| PyOD signed MAD score | 34.099507 |
| Forest anomaly score | 0.190002 |
| Longest direct dependency | CheckoutService/PlaceOrder, 386.142 ms |
| Dependency / frontend duration | 90.1676% |
| Explicitly linked receiver | checkoutservice-2, 384.198 ms |

The script retrieves complete recorded traces from the full file after ranking and discovers the longest direct child and its cross-component receiver using span parent IDs. No checkout name or replica is hard-coded into this traversal.

```text
frontend-2                 428.249 ms   span d520fc2d7fae1ee0
  Checkout client          386.142 ms   span 1f5b3af5678bf1ca
    checkoutservice-2      384.198 ms   span 6b68c1e69127a30d
```

This attributes the bulk of this request's elapsed time to the checkout invocation. It does not prove the initiating fault mechanism. See the existing [trace investigation](track-1-case-25-trace-causality.md) for the deeper dependency analysis.

## What is actually off the shelf

[PyOD](https://pyod.readthedocs.io/en/latest/) supplies the detectors. Its [MAD implementation](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/mad.html) fits a reference median and MAD and reuses them for query scoring. The application-specific direction rule is small:

```python
from pyod.models.mad import MAD

detector = MAD().fit(reference_duration.reshape(-1, 1))
scores = detector.decision_function(query_duration.reshape(-1, 1))
slow_scores = scores * np.sign(query_duration - detector.median_)
```

Run that per recorded operation-count cohort. The cohorting, time windows, and trace traversal remain application code. PyOD does not infer the meaning of a frontend request or identify a service from span ancestry for us.

The [IForest wrapper](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/iforest.html) fits one pooled forest to signed cohort-standardized reference latencies. Query features use only reference cohort statistics. One pooled forest avoids treating scores from separate forests as interchangeable. Settings were fixed before viewing results: 100 trees, seed 42, default sample size, one worker. The default contamination setting is retained but its binary classifications are not used. No hyperparameter search or target-aware feature selection was performed.

MAD is the package replacement of the original method, not an independent algorithmic confirmation. Isolation Forest also shares the cohort normalization; its rank is a comparator under this representation, not a claim about its best achievable performance. ECOD was researched but not run: its implementation incorporates the query batch into its empirical distributions, unlike the frozen-reference setup here. See [library-selection evidence](python-anomaly-library-selection.md).

## Data and verification

- Reference: 22:30–23:00 UTC+8, 2,568 frontend roots. Query: 23:00–23:30, 2,729 roots. Nine recorded operation-count signatures; all query roots meet the minimum of 20 reference samples and nonzero reference MAD.
- Extraction preserves the original one-minute collection margin. Full-file retrieval of selected traces follows ranking. The source is unsorted, so both scans read the whole file.
- Compared all 2,729 packaged MAD scores and cohort medians against the existing independent baseline output. All match within floating-point tolerance after accounting for PyOD's coefficient `0.6745`, versus the original `1/1.4826`. The winner matches exactly. Numerically tied low scores can reorder at machine precision; strict full-list ordering is not claimed.
- Verified a forest score is unchanged when its query is scored alone instead of in the whole batch. Rank ranges are recorded for exact ties; trace ID supplies deterministic display ordering only.
- Installed versions: Python 3.11.15, PyOD 3.6.6, NumPy 2.4.6, scikit-learn 1.9.1, SciPy 1.17.1. All installed package versions are [pinned](../trace-audit/requirements-pyod-demo.txt).
- Measured extraction: 16.35 seconds; fitting, scoring, and ranking: 0.100 seconds; full-trace retrieval: 15.57 seconds. These are one local run, excluding installation and imports, not a performance benchmark.

Saved [summary and top rankings](track-1-case-25-pyod-results/summary.json), [all request scores](track-1-case-25-pyod-results/ranked.csv), and [selected full recorded traces](track-1-case-25-pyod-results/selected-traces.json).

## Reproduce

From the repository root, using `uv`:

```bash
UV_CACHE_DIR=/private/tmp/symbolicrca-uv-cache uv venv /private/tmp/symbolicrca-pyod-venv
UV_CACHE_DIR=/private/tmp/symbolicrca-uv-cache uv pip install \
  --python /private/tmp/symbolicrca-pyod-venv/bin/python \
  -r docs/research/trace-audit/requirements-pyod-demo.txt
/private/tmp/symbolicrca-pyod-venv/bin/python \
  docs/research/trace-audit/demo_pyod_latency.py \
  data/track-1/telemetry/2022_03_20/trace/trace_span.csv \
  /private/tmp/symbolicrca-pyod-demo \
  --evaluate-trace 328e653dddef2f29d419a46895d85d12
```

The optional evaluation argument only looks up a known request after all scores and rankings have been computed. Omit it to discover the MAD winner and forest winner without a known trace ID. The downloaded dataset is required and is not included in these artifacts.

## What remains unresolved

The reference cohort includes a 6,746.740 ms request, so it is not a verified healthy reference. These scores do not establish false-positive rates, alert precision, or an SLA breach. Operation-count cohorts can change under faults or missing instrumentation. Duration units retain the existing audit's provisional microsecond interpretation. Selecting the largest child is elapsed-time localization, not critical-path analysis for arbitrary concurrent traces or proof of root cause.

For this project, a reasonable engineering conclusion is to reuse an existing detector and focus evaluation on cohort quality, operational impact, reference selection, and dependency-based causal investigation. This example provides no evidence that replacing MAD with a more complex model would improve the outcome.
