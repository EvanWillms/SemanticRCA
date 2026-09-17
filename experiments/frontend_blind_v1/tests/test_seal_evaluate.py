import csv
import json
from pathlib import Path

import pytest

from experiments.frontend_blind_v1.evaluate import (
    _best_assignment,
    evaluate,
    official_evaluate,
)
from experiments.frontend_blind_v1.seal import SealError, seal_stage, validate_all, verify_seal


def _incident(component="svc", reason="timeout", when="2022-03-20 10:00:00"):
    return {
        "occurrence_time": when,
        "component": component,
        "reason": reason,
        "observed_symptom_time": when,
        "confidence": 0.5,
        "evidence_refs": [],
    }


def _case(case_root: Path, row_id: int, count=1):
    case_root.mkdir(parents=True, exist_ok=True)
    case = case_root / str(row_id)
    case.mkdir()
    (case / "scope.json").write_text(json.dumps({
        "row_id": row_id, "failure_count": count, "task_index": "task_7",
    }))
    (case / "trace_only.json").write_text(json.dumps({
        "row_id": row_id, "stage": "trace_only",
        "incidents": [_incident(component=f"svc-{row_id}") for _ in range(count)],
        "candidates": [f"svc-{row_id}"],
    }))
    (case / "final.json").write_text(json.dumps({
        "row_id": row_id, "stage": "final",
        "incidents": [_incident(component=f"svc-{row_id}") for _ in range(count)],
        "candidates": [f"svc-{row_id}"],
    }))
    (case / "investigate.py").write_text("# synthetic investigator\n")
    (case / "evidence.md").write_text("synthetic evidence\n")
    (case / "run.json").write_text(json.dumps({"status": "completed"}))
    return case


def _scope(path: Path):
    fields = ("row_id", "task_index", "window_id", "query_start", "failure_count")
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row_id in range(70):
            writer.writerow({"row_id": row_id, "task_index": "task_7",
                             "window_id": f"w-{row_id}", "query_start": "2022-03-20T10:00:00+08:00",
                             "failure_count": 1})


def test_official_scorer_matches_exact_and_time_boundary():
    prediction = ('{"1": {"root cause occurrence datetime": "2022-03-20 10:01:00", '
                  '"root cause component": "svc", "root cause reason": "timeout"}}')
    points = ("The only predicted root cause component is svc\n"
              "The only predicted root cause reason is timeout\n"
              "The only root cause occurrence time is within 1 minutes (i.e., <=1min) of "
              "2022-03-20 10:00:00")
    assert official_evaluate(prediction, points)[2] == 1.0


def test_official_scorer_supports_scoring_point_exports(tmp_path):
    from experiments.frontend_blind_v1.evaluate import _extract_gold, _load_labels
    path = tmp_path / "labels.csv"
    path.write_text("row_id,scoring_points\n0,\"The only predicted root cause component is svc\"\n")
    loaded = _load_labels(path)
    gold, conflict = _extract_gold(loaded[0], ("component",))
    assert not conflict and gold == [{"component": "svc", "reason": "", "occurrence_time": ""}]


def test_assignment_keeps_fields_on_same_incident():
    predicted = [_incident("a", "wrong"), _incident("b", "right")]
    gold = [_incident("a", "right"), _incident("b", "wrong")]
    score, pairs = _best_assignment(predicted, gold, ("component", "reason"))
    assert score == 2
    assert pairs == [(0, 0), (1, 1)]


def test_trace_seal_survives_stage_m_mutation_and_is_write_once(tmp_path):
    case = _case(tmp_path / "cases", 0)
    trace_seal = seal_stage(case, "trace_only", source_snapshot={})
    # Stage M is allowed to update these files; they are covered by final.
    (case / "run.json").write_text(json.dumps({"status": "completed", "stage_m": True}))
    (case / "evidence.md").write_text("updated final evidence\n")
    (case / "investigate.py").write_text("# stage M extension\n")
    assert verify_seal(case, "trace_only")["stage"] == "trace_only"
    with pytest.raises(SealError):
        seal_stage(case, "trace_only")
    assert trace_seal.exists()
    seal_stage(case, "final", source_snapshot={})
    assert verify_seal(case, "final")["stage"] == "final"

    (case / "trace_only.json").write_text("{}")
    with pytest.raises(SealError):
        verify_seal(case, "trace_only")


def test_validate_all_accepts_all_trials_and_excludes_control(tmp_path):
    case_root = tmp_path / "cases"
    case_root.mkdir()
    scope = tmp_path / "scope.csv"
    _scope(scope)
    for row_id in range(70):
        if row_id != 25:
            case = _case(case_root, row_id)
            seal_stage(case, "trace_only", source_snapshot={})
            seal_stage(case, "final", source_snapshot={})
    report = validate_all(case_root, scope_csv=scope)
    assert report["expected_rows"] == 69
    assert 25 not in [row["row_id"] for row in report["rows"]]


def test_evaluate_synthetic_labels_writes_immutable_reports(tmp_path):
    case_root = tmp_path / "cases"
    case_root.mkdir()
    scope = tmp_path / "scope.csv"
    _scope(scope)
    labels = []
    for row_id in range(70):
        if row_id != 25:
            case = _case(case_root, row_id)
            seal_stage(case, "trace_only", source_snapshot={})
            seal_stage(case, "final", source_snapshot={})
            labels.append({"row_id": row_id, "incidents": [_incident(component=f"svc-{row_id}")]})
    label_path = tmp_path / "synthetic_labels.json"
    label_path.write_text(json.dumps(labels))
    out = tmp_path / "out"
    report = evaluate(case_root=case_root, scope_path=scope, labels_path=label_path, output_dir=out)
    assert report["stages"]["final"]["canonical_56"]["denominator"] == 69
    assert (out / "predictions_trace.csv").exists()
    assert (out / "predictions_final.csv").exists()
    assert (out / "results.csv").exists()
    assert (out / "comparisons.csv").exists()
