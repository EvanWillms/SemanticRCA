"""Frozen-reference PyOD demo; no incident labels enter extraction or scoring."""

import argparse
from collections import Counter, defaultdict
import csv
import importlib.metadata
import json
import os
from pathlib import Path
import time

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/symbolicrca-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/symbolicrca-numba")
import numpy as np
from pyod.models.iforest import IForest
from pyod.models.mad import MAD


def read_rows(source):
    with source.open(newline="") as stream:
        for record, row in enumerate(csv.DictReader(stream), 2):
            yield dict(row, source_record=record)


def extract(source, start, width):
    rows = [r for r in read_rows(source)
            if r["cmdb_id"].startswith("frontend-")
            and start - width - 60000 <= int(r["timestamp"]) < start + width + 60000]
    children = defaultdict(list)
    for row in rows:
        children[row["trace_id"], row["parent_span"]].append(row)
    roots = []
    for row in rows:
        if row["parent_span"] or not start - width <= int(row["timestamp"]) < start + width:
            continue
        signature = tuple(sorted(Counter(
            c["operation_name"] for c in children[row["trace_id"], row["span_id"]]
        ).items()))
        roots.append(dict(row, signature=signature,
                          period="reference" if int(row["timestamp"]) < start else "query"))
    return roots


def rank_range(rows, key, row):
    score = row[key]
    return [1 + sum(r[key] > score for r in rows), sum(r[key] >= score for r in rows)]


def dependency_path(root, spans):
    """Follow largest direct child, then its explicit cross-component receivers."""
    direct = [s for s in spans if s["parent_span"] == root["span_id"]]
    if not direct:
        return {"root": root, "largest_direct_child": None}
    child = max(direct, key=lambda s: int(s["duration"]))
    receivers = [s for s in spans if s["parent_span"] == child["span_id"]
                 and s["cmdb_id"] != child["cmdb_id"]]
    return {"root": root, "largest_direct_child": child,
            "child_fraction_of_root": int(child["duration"]) / int(root["duration"]),
            "linked_receivers": receivers,
            "recorded_span_count": len(spans)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--query-start-ms", type=int, default=1647788400000)
    parser.add_argument("--window-ms", type=int, default=1800000)
    parser.add_argument("--evaluate-trace", help="Optional known trace, looked up only after ranking")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    began = time.perf_counter()
    roots = extract(args.source, args.query_start_ms, args.window_ms)
    extraction_seconds = time.perf_counter() - began
    reference, query = defaultdict(list), defaultdict(list)
    for row in roots:
        (reference if row["period"] == "reference" else query)[row["signature"]].append(row)
    began = time.perf_counter()
    scored, excluded, training_z = [], [], []
    for signature, queries in query.items():
        refs = reference[signature]
        x = np.array([int(r["duration"]) / 1000 for r in refs]).reshape(-1, 1)
        if len(x) < 20 or np.median(np.abs(x - np.median(x))) <= 0:
            excluded.extend(queries)
            continue
        # Package detector replaces the hand-written baseline. Fit only reference.
        model = MAD().fit(x)
        test = np.array([int(r["duration"]) / 1000 for r in queries]).reshape(-1, 1)
        # MAD scores both tails; the task specifically asks for slow requests.
        signed_train = model.decision_scores_ * np.sign(x[:, 0] - model.median_)
        signed_test = model.decision_function(test) * np.sign(test[:, 0] - model.median_)
        training_z.extend(signed_train.tolist())
        for row, duration, z in zip(queries, test[:, 0], signed_test):
            scored.append(dict(row, duration_ms=float(duration), baseline_n=len(x),
                               baseline_median_ms=float(model.median_),
                               baseline_mad_ms=float(model.median_diff_),
                               baseline_max_ms=float(x.max()),
                               excess_ms=float(duration - model.median_), mad_score=float(z)))
    if not scored:
        raise ValueError("No eligible query cohorts")
    # One pooled model on cohort-standardized latency avoids comparing scores
    # from separately fitted forests. Seed and settings fixed before inspecting results.
    forest = IForest(n_estimators=100, random_state=42, n_jobs=1)
    forest.fit(np.array(training_z).reshape(-1, 1))
    features = np.array([r["mad_score"] for r in scored]).reshape(-1, 1)
    scores = forest.decision_function(features)
    for row, score in zip(scored, scores):
        row["iforest_raw_score"] = float(score)
        row["iforest_score"] = float(score) if row["excess_ms"] > 0 else None
    # Verify that query batching does not alter fitted-model scores.
    np.testing.assert_allclose(forest.decision_function(features[:1]), scores[:1], atol=1e-12)
    slow = [r for r in scored if r["excess_ms"] > 0]
    methods = {"mad_score": scored, "duration_ms": scored, "iforest_score": slow}
    leaders = {}
    for key, candidates in methods.items():
        ordered = sorted(candidates, key=lambda r: (-r[key], r["trace_id"], r["span_id"]))
        leaders[key] = [dict(r, rank_range=rank_range(candidates, key, r)) for r in ordered[:10]]
    scoring_seconds = time.perf_counter() - began
    # Candidate IDs derive from ranking; the evaluation trace cannot affect models.
    selected = {rows[0]["trace_id"] for rows in leaders.values()}
    evaluations = []
    if args.evaluate_trace:
        for row in scored:
            if row["trace_id"] == args.evaluate_trace:
                evaluations.append(dict(row, ranks={k: rank_range(v, k, row)
                    for k, v in methods.items() if row in v}))
                selected.add(row["trace_id"])
    began = time.perf_counter()
    traces = defaultdict(list)
    for row in read_rows(args.source):
        if row["trace_id"] in selected:
            traces[row["trace_id"]].append(row)
    paths = [dependency_path(row, traces[row["trace_id"]]) for row in scored
             if row["trace_id"] in selected]
    summary = dict(
        source=str(args.source.resolve()), query_start_ms=args.query_start_ms,
        window_ms=args.window_ms, reference_roots=sum(map(len, reference.values())),
        query_roots=sum(map(len, query.values())), eligible=len(scored), excluded=len(excluded),
        slow_query_roots=len(slow), signatures=len(set(reference) | set(query)),
        versions={p: importlib.metadata.version(p) for p in ("pyod", "numpy", "scikit-learn", "scipy")},
        iforest_params=forest.get_params(), leaders=leaders, evaluations=evaluations,
        dependency_paths=paths, timings_seconds=dict(extraction=extraction_seconds,
            scoring=scoring_seconds, full_trace_retrieval=time.perf_counter() - began))
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output / "selected-traces.json").write_text(json.dumps(traces, indent=2) + "\n")
    fields = ["trace_id", "span_id", "timestamp", "cmdb_id", "duration_ms", "baseline_n",
              "baseline_median_ms", "baseline_mad_ms", "baseline_max_ms", "excess_ms",
              "mad_score", "iforest_raw_score", "iforest_score", "source_record"]
    with (args.output / "ranked.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(scored, key=lambda r: -r["mad_score"]))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("leaders", "dependency_paths")}, indent=2))
    for method, rows in leaders.items():
        print(method, [(r["trace_id"], r["duration_ms"], r["rank_range"]) for r in rows[:3]])


if __name__ == "__main__":
    main()
