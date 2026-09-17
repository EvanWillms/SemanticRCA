"""The three frozen frontend ranking arms for frontend-blind-v1."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from bisect import bisect_left, bisect_right
from typing import Iterable, Mapping

import numpy as np
from pyod.models.iforest import IForest
from pyod.models.mad import MAD


def operation_signature(rows: Iterable[Mapping[str, str]]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(Counter(str(row.get("operation_name", "")) for row in rows).items()))


def attach_signatures(roots: list[dict], frontend_rows: Iterable[Mapping[str, str]]) -> list[dict]:
    children: dict[tuple[str, str], list[Mapping[str, str]]] = defaultdict(list)
    for row in frontend_rows:
        if not str(row.get("cmdb_id", "")).startswith("frontend-"):
            continue
        children[(str(row["trace_id"]), str(row.get("parent_span", "")))].append(row)
    output = []
    for root in roots:
        key = (str(root["trace_id"]), str(root["span_id"]))
        signature = operation_signature(children.get(key, ()))
        copy = dict(root)
        copy["signature"] = signature
        copy["signature_key"] = [[name, count] for name, count in signature]
        copy["empty_child_signature"] = not bool(signature)
        output.append(copy)
    return output


def rank_range(rows: list[dict], key: str, value: float) -> list[int]:
    vals = [float(row[key]) for row in rows if row.get(key) is not None]
    ordered = sorted(vals)
    return [len(ordered) - bisect_right(ordered, value) + 1,
            len(ordered) - bisect_left(ordered, value)]


def _ordered(rows: list[dict], key: str) -> list[dict]:
    candidates = [row for row in rows if row.get(key) is not None]
    ordered = sorted(candidates, key=lambda row: (-float(row[key]), str(row["trace_id"]), str(row["span_id"])))
    return [dict(row, rank_range=rank_range(candidates, key, float(row[key]))) for row in ordered]


@dataclass
class DetectionResult:
    rows: list[dict]
    leaders: dict[str, list[dict]]
    reference_count: int
    query_count: int
    cohort_count: int
    eligible_count: int
    excluded_count: int
    coverage: dict

    def as_dict(self) -> dict:
        return {
            "rows": self.rows,
            "leaders": self.leaders,
            "reference_roots": self.reference_count,
            "query_roots": self.query_count,
            "cohorts": self.cohort_count,
            "eligible": self.eligible_count,
            "excluded": self.excluded_count,
            "coverage": self.coverage,
        }


def detect(reference_roots: list[dict], query_roots: list[dict]) -> DetectionResult:
    """Fit B/C from references and rank query roots, without cross-arm borrowing."""
    refs_by_sig: dict[tuple, list[dict]] = defaultdict(list)
    query_by_sig: dict[tuple, list[dict]] = defaultdict(list)
    for row in reference_roots:
        refs_by_sig[tuple(tuple(item) for item in row.get("signature_key", []))].append(row)
    for row in query_roots:
        query_by_sig[tuple(tuple(item) for item in row.get("signature_key", []))].append(row)
    rows = [dict(row, duration_ms=int(row["duration"]) / 1000.0, arm_a_eligible=True) for row in query_roots]
    training_scores: list[float] = []
    eligible_cohorts = 0
    zero_mad_cohorts = 0
    sparse_cohorts = 0
    row_by_key = {(str(row["trace_id"]), str(row["span_id"])): row for row in rows}
    for signature, queries in query_by_sig.items():
        # Preserve streaming/source order for the fitted reference values. It
        # is deterministic and keeps the exposed control equivalent to the
        # original full-file scan when IForest samples a training matrix.
        refs = sorted(refs_by_sig.get(signature, []), key=lambda row: (str(row.get("source_file", "")), int(row.get("source_record", 0))))
        values = np.asarray([int(row["duration"]) / 1000.0 for row in refs], dtype=float)
        median = float(np.median(values)) if len(values) else 0.0
        reference_mad = float(np.median(np.abs(values - median))) if len(values) else 0.0
        if not refs:
            sparse_cohorts += 1
            reason = "no_matching_reference_cohort"
        elif len(values) < 20:
            sparse_cohorts += 1
            reason = "reference_cohort_lt_20"
        elif median <= 0:
            zero_mad_cohorts += 1
            reason = "reference_median_nonpositive"
        elif reference_mad <= 0:
            zero_mad_cohorts += 1
            reason = "reference_mad_zero"
        else:
            reason = ""
        if reason:
            for row in queries:
                target = row_by_key[(str(row["trace_id"]), str(row["span_id"]))]
                target["b_eligible"] = False
                target["c_eligible"] = False
                target["eligibility_reason"] = reason
            continue
        eligible_cohorts += 1
        model = MAD().fit(values.reshape(-1, 1))
        signed_train = model.decision_scores_ * np.sign(values - float(model.median_))
        training_scores.extend(float(value) for value in signed_train)
        for row in queries:
            target = row_by_key[(str(row["trace_id"]), str(row["span_id"]))]
            value = int(row["duration"]) / 1000.0
            signed = float(model.decision_function(np.asarray([[value]]))[0] * np.sign(value - float(model.median_)))
            target.update({
                "b_eligible": True,
                "c_eligible": True,
                "baseline_n": int(len(values)),
                "baseline_median_ms": float(model.median_),
                "baseline_mad_ms": float(model.median_diff_),
                "baseline_max_ms": float(values.max()),
                "excess_ms": float(value - float(model.median_)),
                "mad_score": signed,
                "mad_positive": signed > 0,
                "iforest_score": None,
                "iforest_raw_score": None,
            })
    # B is explicitly slow-only; C uses the same signed reference score, then
    # applies one pooled forest to eligible reference/query values.
    if training_scores and any(row.get("b_eligible") for row in rows):
        forest = IForest(n_estimators=100, random_state=42, max_samples="auto", n_jobs=1)
        forest.fit(np.asarray(training_scores, dtype=float).reshape(-1, 1))
        eligible = [row for row in rows if row.get("c_eligible")]
        if eligible:
            scores = forest.decision_function(np.asarray([[row["mad_score"]] for row in eligible], dtype=float))
            for row, score in zip(eligible, scores):
                score = float(score)
                row["iforest_raw_score"] = score
                row["iforest_score"] = score if row.get("excess_ms", 0) > 0 else None
    for row in rows:
        row["b_score"] = row.get("mad_score") if row.get("b_eligible") and row.get("mad_positive") else None
        row["c_score"] = row.get("iforest_score") if row.get("iforest_score") is not None and row.get("excess_ms", 0) > 0 else None
        row.setdefault("b_eligible", False)
        row.setdefault("c_eligible", False)
        row.setdefault("eligibility_reason", "")
    leaders = {
        "duration": _ordered(rows, "duration_ms"),
        "mad": _ordered(rows, "b_score"),
        "iforest": _ordered(rows, "c_score"),
    }
    leaders = {name: values for name, values in leaders.items()}
    for name, values in leaders.items():
        for limit in (1, 3, 5, 10):
            # JSON-friendly prefixes are materialized below in run_case; retain
            # exactly the requested ranking rows here.
            pass
    return DetectionResult(
        rows=rows,
        leaders=leaders,
        reference_count=len(reference_roots),
        query_count=len(query_roots),
        cohort_count=len(set(refs_by_sig) | set(query_by_sig)),
        eligible_count=sum(bool(row.get("b_eligible")) for row in rows),
        excluded_count=sum(not bool(row.get("b_eligible")) for row in rows),
        coverage={
            "arm_a": {"query_roots": len(rows), "eligible": len(rows)},
            "arm_b": {"eligible": sum(bool(row.get("b_score") is not None) for row in rows)},
            "arm_c": {"eligible": sum(bool(row.get("c_score") is not None) for row in rows)},
            "sparse_cohorts": sparse_cohorts,
            "zero_mad_cohorts": zero_mad_cohorts,
            "eligible_cohorts": eligible_cohorts,
        },
    )
