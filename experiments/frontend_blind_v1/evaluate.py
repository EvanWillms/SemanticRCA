"""Label-gated evaluation for the frontend blind v1 trial.

This module is deliberately dependency-free.  ``official_evaluate`` below is
the pure scorer from the official starter, copied without changing its scoring
logic so that synthetic tests can run without pandas.  The CLI will not open a
label file until :func:`seal.validate_all` has verified every scheduled case.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .seal import DEFAULT_CASE_ROOT, DEFAULT_SCOPE, REQUIRED_ROW_IDS, SealError, validate_all, verify_seal

DIFFICULTY = {"task_1": "easy", "task_2": "easy", "task_3": "easy",
              "task_4": "middle", "task_5": "middle", "task_6": "middle",
              "task_7": "hard"}
TASK_FIELDS = {
    "task_1": ("occurrence_time",), "task_2": ("reason",),
    "task_3": ("component",), "task_4": ("occurrence_time", "reason"),
    "task_5": ("occurrence_time", "component"),
    "task_6": ("component", "reason"),
    "task_7": ("occurrence_time", "component", "reason"),
}
ARMS = ("duration", "mad", "isolation_forest")
BUDGETS = (1, 3, 5, 10)
COMPONENT_KS = (1, 3, 5)


# Vendored unchanged from track-1/starter/score.py.  Keep this function's body
# byte-for-byte equivalent to the official pure function; only the surrounding
# pandas CLI has been omitted.  Provenance is recorded in reports below.
def official_evaluate(prediction: str, scoring_points: str):
    predict_pattern = (
        r'{\s*'
        r'(?:"root cause occurrence datetime":\s*"(.*?)")?,?\s*'
        r'(?:"root cause component":\s*"(.*?)")?,?\s*'
        r'(?:"root cause reason":\s*"(.*?)")?\s*}'
    )
    predict_results = [
        {"root cause occurrence datetime": d, "root cause component": c,
         "root cause reason": r}
        for d, c, r in re.findall(predict_pattern, str(prediction))
    ]
    prediction_length = len(predict_results)

    components = re.findall(
        r"The (?:\d+-th|only) predicted root cause component is ([^\n]+)", scoring_points)
    reasons = re.findall(
        r"The (?:\d+-th|only) predicted root cause reason is ([^\n]+)", scoring_points)
    times = re.findall(
        r"The (?:\d+-th|only) root cause occurrence time is within 1 minutes "
        r"\(i.e., <=1min\) of ([^\n]+)", scoring_points)

    scoringpoints_length = max(len(components), len(reasons), len(times))
    scores_num = len(components) + len(reasons) + len(times)

    def close_enough(a: str, b: str) -> bool:
        try:
            t1 = datetime.strptime(a, "%Y-%m-%d %H:%M:%S")
            t2 = datetime.strptime(b, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False
        return abs((t1 - t2).total_seconds()) <= 60

    best, passing = -1, []
    if scoringpoints_length == prediction_length:
        for perm in itertools.permutations(predict_results):
            cur, cur_pass = 0, []
            for i in range(scoringpoints_length):
                if len(components) == scoringpoints_length and \
                        perm[i]["root cause component"] == components[i]:
                    cur += 1; cur_pass.append(components[i])
                if len(reasons) == scoringpoints_length and \
                        perm[i]["root cause reason"] == reasons[i]:
                    cur += 1; cur_pass.append(reasons[i])
                if len(times) == scoringpoints_length and \
                        close_enough(times[i], perm[i]["root cause occurrence datetime"]):
                    cur += 1; cur_pass.append(times[i])
            if cur > best:
                best, passing = cur, cur_pass
    scores_get = max(best, 0)
    failing = list(set(components + reasons + times) - set(passing))
    return passing, failing, round(scores_get / scores_num, 2) if scores_num else 0.0


OFFICIAL_PROVENANCE = {
    "source": "track-1/starter/score.py",
    "function": "evaluate",
    "contract": "OpenRCA main.evaluate; vendored pure function; pandas CLI omitted",
}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def _scope_rows(scope_path: Path) -> dict[int, dict[str, str]]:
    with scope_path.open(newline="") as fh:
        rows = {}
        for row in csv.DictReader(fh):
            rows[int(row["row_id"])] = row
    return rows


def _prediction_text(value: Mapping[str, Any]) -> str:
    """Serialize unchanged field strings in official datetime/component/reason order."""
    objects = []
    for incident in value.get("incidents", []):
        objects.append({
            "root cause occurrence datetime": incident.get("occurrence_time", ""),
            "root cause component": incident.get("component", ""),
            "root cause reason": incident.get("reason", ""),
        })
    return "```json\n" + json.dumps({str(i + 1): obj for i, obj in enumerate(objects)},
                                            indent=4, ensure_ascii=False) + "\n```"


def _safe_artifact(case_dir: Path, stage: str, expected_count: int) -> tuple[dict[str, Any] | None, str | None]:
    path = case_dir / f"{stage}.json"
    try:
        value = _read_json(path)
        if not isinstance(value, dict) or not isinstance(value.get("incidents"), list):
            return None, "malformed"
        if len(value["incidents"]) != expected_count:
            return value, "count_error"
        for incident in value["incidents"]:
            if not isinstance(incident, dict):
                return value, "malformed"
            if any(not isinstance(incident.get(key, ""), str)
                   for key in ("occurrence_time", "component", "reason")):
                return value, "malformed"
        return value, None
    except (OSError, ValueError):
        return None, "malformed"


def _canonical_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S",):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def _best_assignment(predicted: Sequence[Mapping[str, Any]], gold: Sequence[Mapping[str, Any]],
                     fields: Sequence[str]) -> tuple[int, list[tuple[int, int]]]:
    """Maximize field matches while keeping fields on the same incident tuple."""
    if len(predicted) != len(gold):
        return 0, []
    best_score, best_pairs = -1, []
    for perm in itertools.permutations(range(len(gold))):
        score = 0
        for pidx, gidx in enumerate(perm):
            for field in fields:
                pv, gv = predicted[pidx].get(field, ""), gold[gidx].get(field, "")
                if field == "occurrence_time":
                    pt, gt = _canonical_time(pv), _canonical_time(gv)
                    ok = pt is not None and gt is not None and abs((pt - gt).total_seconds()) <= 60
                else:
                    ok = bool(pv) and pv == gv
                score += int(ok)
        if score > best_score:
            best_score, best_pairs = score, list(enumerate(perm))
    return max(best_score, 0), best_pairs


def _scoring_points(incidents: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> str:
    lines: list[str] = []
    for index, incident in enumerate(incidents, 1):
        ordinal = "only" if len(incidents) == 1 else f"{index}-th"
        if "component" in fields:
            lines.append(f"The {ordinal} predicted root cause component is {incident.get('component', '')}")
        if "reason" in fields:
            lines.append(f"The {ordinal} predicted root cause reason is {incident.get('reason', '')}")
        if "occurrence_time" in fields:
            lines.append(f"The {ordinal} root cause occurrence time is within 1 minutes (i.e., <=1min) of {incident.get('occurrence_time', '')}")
    return "\n".join(lines)


def _load_labels(path: Path) -> dict[int, dict[str, Any]]:
    """Load a post-gate synthetic/full label file; never called before validate_all."""
    if path.suffix.lower() == ".json":
        raw = _read_json(path)
        rows = raw.get("rows", raw) if isinstance(raw, dict) else raw
        if isinstance(rows, dict):
            rows = [{"row_id": k, **v} for k, v in rows.items()]
        if not isinstance(rows, list):
            raise ValueError("JSON labels must be a list or {rows: [...]}")
    else:
        with path.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        rid = int(row["row_id"])
        incidents = row.get("incidents", [])
        if isinstance(incidents, str):
            incidents = json.loads(incidents) if incidents else []
        if not incidents and all(key in row for key in ("occurrence_time", "component", "reason")):
            incidents = [{key: row.get(key, "") for key in ("occurrence_time", "component", "reason")}]
        if isinstance(incidents, dict):
            incidents = list(incidents.values())
        result[rid] = {**row, "incidents": incidents}
    return result


def _extract_gold(row: Mapping[str, Any], fields: Sequence[str]) -> tuple[list[dict[str, Any]], bool]:
    incidents = row.get("incidents")
    if isinstance(incidents, list) and incidents and all(isinstance(x, Mapping) for x in incidents):
        return [dict(x) for x in incidents], False
    scoring = row.get("scoring_points", "")
    if scoring:
        components = re.findall(r"The (?:\d+-th|only) predicted root cause component is ([^\n]+)", str(scoring))
        reasons = re.findall(r"The (?:\d+-th|only) predicted root cause reason is ([^\n]+)", str(scoring))
        times = re.findall(r"The (?:\d+-th|only) root cause occurrence time is within 1 minutes \(i\.e\., <=1min\) of ([^\n]+)", str(scoring))
        n = max(len(components), len(reasons), len(times))
        # Labels parsed from independent scoring lists cannot be paired safely.
        # Keep positional pairing only when every requested list has equal length.
        if n and all(len(values) in (0, n) for values in (components, reasons, times)):
            return [{"component": components[i] if components else "",
                     "reason": reasons[i] if reasons else "",
                     "occurrence_time": times[i] if times else ""} for i in range(n)], False
        return [], True
    return [], False


def _load_discovery(case_dir: Path) -> Any:
    for name in ("trace_evidence.json", "rankings.json", "discovery.json"):
        path = case_dir / name
        if path.exists():
            try:
                return _read_json(path)
            except ValueError:
                return None
    return None


def _discovery_prefix(data: Any, arm: str, budget: int, kind: str) -> list[str]:
    """Read canonical or compatible per-arm rank evidence without gold filtering."""
    if not isinstance(data, Mapping):
        return []
    arms = data.get("arms") or data.get("arm_evidence") or data.get("leaders") or data
    if not isinstance(arms, Mapping):
        return []
    aliases = [arm, arm.replace("_", " ")]
    if arm == "isolation_forest":
        aliases.append("iforest")
    entry = next((arms.get(alias) for alias in aliases if arms.get(alias) is not None), None)
    if not isinstance(entry, Mapping):
        return []
    prefixes = entry.get("top_requests", entry.get("request_prefixes", {}))
    if isinstance(prefixes, list):
        prefixes = {str(budget): prefixes}
    if not isinstance(prefixes, Mapping):
        return []
    values = prefixes.get(str(budget), prefixes.get(budget, []))
    if not values and isinstance(entry.get("traces"), list):
        # Native run_case evidence stores the top-10 trace records directly;
        # derive each fixed request prefix from that already-ranked sequence.
        values = entry["traces"][:budget]
        if kind == "reachable":
            out: list[str] = []
            for record in values:
                for component in record.get("dependency_reachability", {}).get("components", []):
                    if isinstance(component, str) and component not in out:
                        out.append(component)
            return out
        out = []
        for record in values:
            for receiver in record.get("immediate_attribution", {}).get("linked_receivers", []):
                component = receiver.get("cmdb_id", receiver.get("component", "")) if isinstance(receiver, Mapping) else ""
                if isinstance(component, str) and component and component not in out:
                    out.append(component)
        return out
    if not isinstance(values, list):
        return []
    key = "immediate_components" if kind == "immediate" else "reachable_components"
    out: list[str] = []
    for item in values:
        comps = item.get(key, item.get("components", [])) if isinstance(item, Mapping) else item
        if isinstance(comps, str):
            comps = [comps]
        if isinstance(comps, list):
            for component in comps:
                if isinstance(component, str) and component not in out:
                    out.append(component)
    return out


def _components_from_gold(gold_rows: Mapping[int, Mapping[str, Any]], scope_rows: Mapping[int, Mapping[str, str]]) -> tuple[dict[str, set[str]], dict[str, bool]]:
    by_window: dict[str, set[str]] = defaultdict(set)
    conflicts: dict[str, bool] = defaultdict(bool)
    observed_sets: dict[str, set[tuple[str, ...]]] = defaultdict(set)
    for rid, row in gold_rows.items():
        window = str(scope_rows.get(rid, row).get("window_id", rid))
        incidents, conflict = _extract_gold(row, ("component",))
        if conflict:
            conflicts[window] = True
        row_components = sorted({str(incident.get("component", "")) for incident in incidents
                                 if incident.get("component", "")})
        if row_components:
            observed_sets[window].add(tuple(row_components))
        for incident in incidents:
            component = incident.get("component", "")
            if component:
                by_window[window].add(component)
    for window, variants in observed_sets.items():
        if len(variants) > 1:
            conflicts[window] = True
    return by_window, conflicts


def _discovery_metrics(case_root: Path, scope_rows: Mapping[int, Mapping[str, str]],
                       gold_rows: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    gold_components, conflicts = _components_from_gold(gold_rows, scope_rows)
    metrics: dict[str, Any] = {"component_conflicts": sorted(k for k, v in conflicts.items() if v), "arms": {}}
    # Use one canonical row per window for discovery; query projections can differ.
    canonical: dict[str, int] = {}
    for rid in sorted(scope_rows):
        if rid == 25:
            continue
        window = scope_rows[rid].get("window_id", str(rid))
        canonical.setdefault(window, rid)
    discovery_by_row = {rid: _load_discovery(case_root / str(rid)) for rid in canonical.values()}
    for arm in ARMS:
        arm_out: dict[str, Any] = {}
        for kind in ("immediate", "reachable"):
            for budget in BUDGETS:
                denom = hits = any_hits = all_hits = component_denominator = 0
                ranks: list[int] = []
                for window, rid in canonical.items():
                    labels = gold_components.get(window, set())
                    if not labels or conflicts.get(window):
                        continue
                    data = discovery_by_row[rid]
                    shortlist = _discovery_prefix(data, arm, budget, kind)
                    denom += 1
                    matched = labels & set(shortlist)
                    any_hits += bool(matched)
                    all_hits += labels.issubset(set(shortlist))
                    component_denominator += len(labels)
                    if matched:
                        hits += len(matched)
                        ranks.extend(shortlist.index(component) + 1 for component in matched)
                arm_out[f"{kind}_budget_{budget}"] = {
                    "windows": denom, "any_incident_hits": any_hits,
                    "any_incident_recall": any_hits / denom if denom else None,
                    "all_labelled_components_hits": all_hits,
                    "all_labelled_components_recall": all_hits / denom if denom else None,
                    "component_denominator": component_denominator,
                    "component_hits": hits, "component_ranks": ranks,
                }
            for k in COMPONENT_KS:
                denom = hits = 0
                for window, rid in canonical.items():
                    labels = gold_components.get(window, set())
                    if not labels or conflicts.get(window):
                        continue
                    shortlist = _discovery_prefix(discovery_by_row[rid], arm, 10, kind)[:k]
                    denom += len(labels)
                    hits += len(labels & set(shortlist))
                arm_out[f"{kind}_components_{k}"] = {"denominator": denom, "hits": hits,
                    "recall": hits / denom if denom else None}
        metrics["arms"][arm] = arm_out
    metrics["per_window"] = []
    for window, rid in canonical.items():
        labels = gold_components.get(window, set())
        if not labels or conflicts.get(window):
            continue
        data = discovery_by_row[rid]
        metrics["per_window"].append({
            "window_id": window, "canonical_row_id": rid,
            "labelled_components": sorted(labels),
            "failure_count": int(scope_rows[rid]["failure_count"]),
            "arms": {arm: {f"{kind}_budget_{budget}": _discovery_prefix(data, arm, budget, kind)
                            for kind in ("immediate", "reachable") for budget in BUDGETS}
                     for arm in ARMS},
        })
    return metrics


def _stage_rows(stage: str, case_root: Path, scope_rows: Mapping[int, Mapping[str, str]],
                gold_rows: Mapping[int, Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rid in sorted(REQUIRED_ROW_IDS):
        scope = scope_rows[rid]
        count = int(scope["failure_count"])
        case = case_root / str(rid)
        artifact, error = _safe_artifact(case, stage, count)
        run_status = ""
        run_path = case / "run.json"
        if run_path.exists():
            try:
                run_status = str(_read_json(run_path).get("status", ""))
            except ValueError:
                run_status = "failed"
        label = gold_rows.get(rid, {})
        fields = TASK_FIELDS.get(scope.get("task_index", ""), ())
        gold, pairing_conflict = _extract_gold(label, fields)
        prediction = _prediction_text(artifact or {"incidents": []}) if artifact else ""
        scoring_points = str(label.get("scoring_points", ""))
        if not scoring_points and gold:
            scoring_points = _scoring_points(gold, fields)
        passed, failed, official_score = official_evaluate(prediction, scoring_points) if scoring_points else ([], [], 0.0)
        result: dict[str, Any] = {"row_id": rid, "task_index": scope.get("task_index", ""),
            "window_id": scope.get("window_id", ""), "query_start": scope.get("query_start", ""),
            "day": scope.get("query_start", "")[:10],
            "status": run_status if run_status in {"completed", "failed"} else ("failed" if error else "completed"),
            "malformed": error == "malformed",
            "count_error": error == "count_error", "pairing_conflict": pairing_conflict,
            "official_score": official_score, "official_passed": passed, "official_failed": failed,
            "failure_count": count, "gold_count": len(gold), "abstention": {}}
        for field in ("occurrence_time", "component", "reason"):
            result["abstention"][field] = sum(1 for incident in (artifact or {}).get("incidents", [])
                                               if not incident.get(field, ""))
        score, pairs = _best_assignment((artifact or {}).get("incidents", []), gold, fields)
        result["field_score"] = score
        result["field_denominator"] = len(gold) * len(fields) if len(gold) == count else 0
        result["field_accuracy"] = (score / result["field_denominator"]
                                     if result["field_denominator"] else None)
        field_scores: dict[str, dict[str, Any]] = {}
        for field in fields:
            field_hits = 0
            for pidx, gidx in pairs:
                pv, gv = (artifact or {}).get("incidents", [])[pidx].get(field, ""), gold[gidx].get(field, "")
                if field == "occurrence_time":
                    pt, gt = _canonical_time(pv), _canonical_time(gv)
                    field_hits += int(pt is not None and gt is not None and abs((pt - gt).total_seconds()) <= 60)
                else:
                    field_hits += int(bool(pv) and pv == gv)
            field_scores[field] = {"hits": field_hits, "denominator": len(gold) if len(gold) == count else 0,
                                   "accuracy": field_hits / len(gold) if len(gold) == count and gold else None}
        result["field_scores"] = field_scores
        errors: list[float] = []
        if not error and not pairing_conflict:
            for pidx, gidx in pairs:
                if "occurrence_time" in fields:
                    pt, gt = _canonical_time(artifact["incidents"][pidx].get("occurrence_time")), _canonical_time(gold[gidx].get("occurrence_time"))
                    if pt is not None and gt is not None:
                        errors.append(abs((pt - gt).total_seconds()))
        result["time_errors_seconds"] = errors
        rows.append(result)
    return rows, {"stage": stage, "official_provenance": OFFICIAL_PROVENANCE}


def _group_scores(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, ""))].append(row)
    return {group: {"rows": len(subset),
                    "mean_official_score": sum(float(r["official_score"]) for r in subset) / len(subset),
                    "fully_solved": sum(float(r["official_score"]) == 1.0 for r in subset),
                    "malformed": sum(bool(r["malformed"]) for r in subset),
                    "count_errors": sum(bool(r["count_error"]) for r in subset)}
            for group, subset in sorted(groups.items()) if group}


def _duplicate_consistency(rows: Sequence[Mapping[str, Any]], scope_rows: Mapping[int, Mapping[str, str]], case_root: Path, stage: str) -> dict[str, Any]:
    groups: dict[str, list[int]] = defaultdict(list)
    for rid, scope in scope_rows.items():
        if rid in REQUIRED_ROW_IDS:
            groups[scope.get("window_id", str(rid))].append(rid)
    out = {}
    for window, ids in sorted(groups.items()):
        if len(ids) < 2:
            continue
        serialized = []
        for rid in sorted(ids):
            value, _ = _safe_artifact(case_root / str(rid), stage, int(scope_rows[rid]["failure_count"]))
            if value is None:
                serialized.append(None)
            else:
                incidents = value.get("incidents", [])
                tuples = sorted(tuple(str(incident.get(field, "")) for field in
                                      ("occurrence_time", "component", "reason"))
                                for incident in incidents if isinstance(incident, Mapping))
                serialized.append(json.dumps(tuples, ensure_ascii=False))
        out[window] = {"row_ids": sorted(ids), "consistent": len(set(serialized)) <= 1}
    return out


def evaluate(*, case_root: str | Path = DEFAULT_CASE_ROOT, scope_path: str | Path = DEFAULT_SCOPE,
             labels_path: str | Path, output_dir: str | Path, require_final: bool = True) -> dict[str, Any]:
    """Run label-gated evaluation and write immutable input-derived reports."""
    # Gate first: this call must precede _load_labels so no label bytes are read
    # when an attempt is missing, unsealed, or has been modified.
    gate = validate_all(case_root, scope_csv=scope_path, require_final=require_final)
    scope_rows = _scope_rows(Path(scope_path))
    labels = _load_labels(Path(labels_path))
    missing = sorted(set(REQUIRED_ROW_IDS) - set(labels))
    if missing:
        raise ValueError(f"approved labels missing required rows: {missing}")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stages = ("trace_only", "final") if require_final else ("trace_only",)
    report: dict[str, Any] = {"protocol": "frontend-blind-v1", "gate": gate,
                              "official_provenance": OFFICIAL_PROVENANCE, "stages": {}}
    combined_rows: list[dict[str, Any]] = []
    for stage in stages:
        rows, info = _stage_rows(stage, Path(case_root), scope_rows, labels)
        combined_rows.extend({"stage": stage, **row} for row in rows)
        # Write predictions only from sealed artifacts; no mutation of input files.
        pred_path = out / f"predictions_{'trace' if stage == 'trace_only' else 'final'}.csv"
        with pred_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=("row_id", "task_index", "prediction"))
            writer.writeheader()
            for row in rows:
                value, _ = _safe_artifact(Path(case_root) / str(row["row_id"]), stage, int(row["failure_count"]))
                writer.writerow({"row_id": row["row_id"], "task_index": row["task_index"],
                                 "prediction": _prediction_text(value or {"incidents": []})})
        results_path = out / f"per_case_{'trace' if stage == 'trace_only' else 'final'}.csv"
        with results_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=("row_id", "task_index", "window_id", "status",
                "official_score", "field_score", "field_denominator", "field_accuracy",
                "field_scores", "malformed", "count_error", "pairing_conflict", "time_errors_seconds"))
            writer.writeheader()
            for row in rows:
                writer.writerow({**{key: (json.dumps(row[key]) if key == "field_scores" else row[key])
                                     for key in writer.fieldnames if key in row},
                                 "time_errors_seconds": json.dumps(row["time_errors_seconds"])})
        report["stages"][stage] = {**info, "rows": rows, "by_task": _group_scores(rows, "task_index"),
            "by_day": _group_scores(rows, "day"),
            "duplicate_window_consistency": _duplicate_consistency(rows, scope_rows, Path(case_root), stage)}
    report["discovery"] = _discovery_metrics(Path(case_root), scope_rows, labels)
    # Canonical-window and requested sensitivity summaries are computed from the
    # same per-row results, preserving denominators and excluding 24/26 only here.
    for stage, summary in report["stages"].items():
        rows = summary["rows"]
        canonical_ids = {min(rid for rid in REQUIRED_ROW_IDS if scope_rows[rid].get("window_id") == window)
                         for window in {scope_rows[rid].get("window_id") for rid in REQUIRED_ROW_IDS}}
        canonical = [row for row in rows if row["row_id"] in canonical_ids]
        sensitivity = [row for row in canonical if row["row_id"] not in {24, 26}]
        summary["canonical_56"] = {"denominator": len(canonical),
            "mean_official_score": sum(r["official_score"] for r in canonical) / len(canonical) if canonical else None}
        summary["sensitivity_excluding_24_26"] = {"denominator": len(sensitivity),
            "mean_official_score": sum(r["official_score"] for r in sensitivity) / len(sensitivity) if sensitivity else None}
        summary["abstention_by_field"] = {
            field: {"count": sum(int(r["abstention"].get(field, 0)) for r in rows)}
            for field in ("occurrence_time", "component", "reason")
        }
        summary["field_metrics"] = {
            field: {
                "hits": sum(int(r["field_scores"].get(field, {}).get("hits", 0)) for r in rows),
                "denominator": sum(int(r["field_scores"].get(field, {}).get("denominator", 0)) for r in rows),
                "accuracy": (
                    sum(int(r["field_scores"].get(field, {}).get("hits", 0)) for r in rows)
                    / sum(int(r["field_scores"].get(field, {}).get("denominator", 0)) for r in rows)
                    if sum(int(r["field_scores"].get(field, {}).get("denominator", 0)) for r in rows) else None
                ),
            }
            for field in ("occurrence_time", "component", "reason")
        }
        summary["time_error_seconds"] = [error for row in rows for error in row["time_errors_seconds"]]
        summary.pop("rows", None)
    result_fields = ("stage", "row_id", "task_index", "window_id", "status",
                     "official_score", "field_score", "field_denominator", "field_accuracy",
                     "field_scores", "malformed", "count_error", "pairing_conflict", "time_errors_seconds")
    with (out / "results.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=result_fields)
        writer.writeheader()
        for row in combined_rows:
            writer.writerow({key: (json.dumps(row[key]) if key in {"field_scores", "time_errors_seconds"} else row.get(key, ""))
                             for key in result_fields})
    by_stage_row = {(row["stage"], row["row_id"]): row for row in combined_rows}
    with (out / "comparisons.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=("row_id", "task_index", "window_id",
                                                "trace_score", "final_score", "delta"))
        writer.writeheader()
        for rid in sorted(REQUIRED_ROW_IDS):
            trace = by_stage_row.get(("trace_only", rid), {})
            final = by_stage_row.get(("final", rid), {})
            ts, fs = trace.get("official_score"), final.get("official_score")
            writer.writerow({"row_id": rid, "task_index": scope_rows[rid].get("task_index", ""),
                             "window_id": scope_rows[rid].get("window_id", ""),
                             "trace_score": ts if ts is not None else "",
                             "final_score": fs if fs is not None else "",
                             "delta": (fs - ts) if isinstance(fs, (int, float)) and isinstance(ts, (int, float)) else ""})
    (out / "metrics.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", default=str(DEFAULT_CASE_ROOT))
    parser.add_argument("--scope", default=str(DEFAULT_SCOPE))
    parser.add_argument("--labels", "--gold", dest="labels", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        evaluate(case_root=args.case_root, scope_path=args.scope, labels_path=args.labels,
                 output_dir=args.out)
    except (SealError, ValueError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
