"""Write-once seals and coverage validation for frontend blind v1.

The seal command is intentionally label-free. It only reads a case's public
scope and investigator artifacts; it never opens a query label or answer key.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent
DEFAULT_SCOPE = Path("docs/research/experiments/frontend-blind-v1/scope.csv")
DEFAULT_CASE_ROOT = Path("data/experiments/frontend-blind-v1/cases")
REQUIRED_ROW_IDS = tuple(i for i in range(70) if i != 25)
STAGES = ("trace_only", "final")


class SealError(ValueError):
    """An artifact cannot be sealed or does not satisfy the protocol."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _relative(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SealError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SealError(f"{path} must contain a JSON object")
    return value


def _scope_count(case_dir: Path) -> int:
    scope = _read_json(case_dir / "scope.json")
    try:
        count = int(scope["failure_count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SealError(f"scope.json has no integer failure_count: {case_dir}") from exc
    if count < 1:
        raise SealError(f"failure_count must be positive: {case_dir}")
    return count


def validate_prediction(case_dir: Path, stage: str) -> dict[str, Any]:
    """Validate a stage prediction without changing it and return its object."""
    if stage not in STAGES:
        raise SealError(f"stage must be one of {STAGES}, got {stage!r}")
    path = case_dir / f"{stage}.json"
    value = _read_json(path)
    if value.get("stage") != stage:
        raise SealError(f"{path} has stage {value.get('stage')!r}, expected {stage!r}")
    scope = _read_json(case_dir / "scope.json")
    if str(value.get("row_id")) != str(scope.get("row_id")) or "row_id" not in value:
        raise SealError(f"{path} row_id does not match its assigned scope")
    incidents = value.get("incidents")
    if not isinstance(incidents, list):
        raise SealError(f"{path}.incidents must be a list")
    expected = _scope_count(case_dir)
    if len(incidents) != expected:
        raise SealError(f"{path} has {len(incidents)} incidents; scope requires {expected}")
    required = ("occurrence_time", "component", "reason", "observed_symptom_time",
                "confidence", "evidence_refs")
    for index, incident in enumerate(incidents, 1):
        if not isinstance(incident, dict):
            raise SealError(f"{path} incident {index} must be an object")
        missing = [key for key in required if key not in incident]
        if missing:
            raise SealError(f"{path} incident {index} missing {missing}")
        for key in ("occurrence_time", "component", "reason", "observed_symptom_time"):
            if not isinstance(incident[key], str):
                raise SealError(f"{path} incident {index} {key} must be a string")
        confidence = incident["confidence"]
        if confidence != "" and (not isinstance(confidence, (int, float)) or
                                   isinstance(confidence, bool) or not 0 <= confidence <= 1):
            raise SealError(f"{path} incident {index} confidence must be in [0,1] or ''")
        if not isinstance(incident["evidence_refs"], list) or not all(
                isinstance(ref, str) for ref in incident["evidence_refs"]):
            raise SealError(f"{path} incident {index} evidence_refs must be string list")
    candidates = value.get("candidates", [])
    if not isinstance(candidates, list) or not all(isinstance(c, str) for c in candidates):
        raise SealError(f"{path}.candidates must be a list of component strings")
    if stage == "trace_only" and (len(candidates) > 5 or any(not c for c in candidates)):
        raise SealError("trace_only candidates must contain at most five nonempty components")
    return value


def _declared_refs(case_dir: Path, stage: str) -> list[Path]:
    """Return protocol inputs declared by run.json plus standard artifacts."""
    refs: list[Path] = []
    # Stage T must remain verifiable while Stage M edits its narrative and
    # runtime record.  Those mutable files are covered by the final seal.
    names = ("scope.json", "rankings.json", "trace_evidence.json",
             "run_inputs.json", "index.json", f"{stage}.json")
    if stage == "trace_only":
        snapshot_dir = case_dir / "trace_only_snapshot"
        if snapshot_dir.is_dir():
            refs.extend(path for path in snapshot_dir.rglob("*") if path.is_file())
    if stage == "final":
        names += ("investigate.py", "evidence.md", "run.json", "retrieval.jsonl",
                  "trace_only.seal.json")
    for name in names:
        path = case_dir / name
        if path.exists():
            refs.append(path)
    run_path = case_dir / "run.json"
    if stage == "final" and run_path.exists():
        run = _read_json(run_path)
        for key in ("code_refs", "data_refs", "input_refs"):
            values = run.get(key, [])
            if isinstance(values, dict):
                values = list(values)
            if not isinstance(values, list):
                raise SealError(f"run.json {key} must be a list")
            for raw in values:
                path = Path(str(raw))
                if not path.is_absolute():
                    candidates = (case_dir / path, ROOT / path,
                                  REPO_ROOT / path, Path.cwd() / path)
                    path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
                if not path.exists() or not path.is_file():
                    raise SealError(f"declared {key} path does not exist: {raw}")
                refs.append(path)
        code_hashes = run.get("code_sha256", {})
        if isinstance(code_hashes, dict):
            for raw in code_hashes:
                candidates = (case_dir / str(raw), ROOT / str(raw),
                              REPO_ROOT / str(raw))
                path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
                if not path.is_file():
                    raise SealError(f"run.json code_sha256 path does not exist: {raw}")
                refs.append(path)
        index_raw = run.get("index")
        if index_raw:
            candidates = (Path(str(index_raw)), case_dir / str(index_raw),
                          REPO_ROOT / str(index_raw))
            path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
            # The index can be multi-gigabyte.  Its small index.json is already
            # hashed; retain stat provenance below instead of hashing the DB.
    seen: set[Path] = set()
    return [p for p in refs if not (p.resolve() in seen or seen.add(p.resolve()))]


def _snapshot_trace_inputs(case_dir: Path) -> None:
    """Freeze investigator code before Stage M may mutate it."""
    target = case_dir / "trace_only_snapshot"
    if target.exists():
        return
    sources: list[Path] = []
    for name in ("investigate.py",):
        path = case_dir / name
        if path.is_file():
            sources.append(path)
    run_path = case_dir / "run.json"
    if run_path.exists():
        run = _read_json(run_path)
        code_hashes = run.get("code_sha256", {})
        if isinstance(code_hashes, dict):
            for raw in code_hashes:
                candidates = (case_dir / str(raw), ROOT / str(raw), REPO_ROOT / str(raw))
                path = next((candidate for candidate in candidates if candidate.is_file()), None)
                if path is not None:
                    sources.append(path)
        for key in ("data_refs", "input_refs"):
            values = run.get(key, [])
            if isinstance(values, list):
                for raw in values:
                    candidates = (case_dir / str(raw), ROOT / str(raw), REPO_ROOT / str(raw), Path(str(raw)))
                    path = next((candidate for candidate in candidates
                                 if candidate.is_file() and candidate.stat().st_size <= 50 * 1024 * 1024), None)
                    if path is not None:
                        sources.append(path)
    if not sources:
        return
    target.mkdir()
    used: set[str] = set()
    for source in sources:
        name = source.name
        if name in used:
            name = f"{source.parent.name}-{name}"
        used.add(name)
        shutil.copy2(source, target / name)


def _source_snapshot(case_dir: Path) -> dict[str, str]:
    """Hash current experiment Python/markdown/config files without labels."""
    repo_root = REPO_ROOT
    frozen_manifest = repo_root / "data/experiments/frontend-blind-v1/orchestration/frozen_sources.json"
    if frozen_manifest.exists():
        try:
            frozen = json.loads(frozen_manifest.read_text())
            files = frozen.get("files", {})
        except (OSError, json.JSONDecodeError) as exc:
            raise SealError(f"invalid frozen source manifest: {frozen_manifest}") from exc
        if not isinstance(files, dict) or not files:
            raise SealError(f"frozen source manifest has no files: {frozen_manifest}")
        snapshot = {_relative(frozen_manifest, repo_root): sha256_file(frozen_manifest)}
        snapshot.update({str(raw): str(digest) for raw, digest in files.items()})
        return snapshot
    files: list[Path] = []
    for path in ROOT.iterdir():
        if path.is_file() and path.suffix in {".py", ".json", ".md"}:
            files.append(path)
    result: dict[str, str] = {}
    for path in sorted(files):
        result[_relative(path, repo_root)] = sha256_file(path)
    return result


def _index_path(case_dir: Path) -> Path | None:
    run_path = case_dir / "run.json"
    if not run_path.exists():
        return None
    run = _read_json(run_path)
    raw = run.get("index")
    if not raw:
        return None
    candidates = (Path(str(raw)), case_dir / str(raw), REPO_ROOT / str(raw))
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def seal_stage(case_dir: str | os.PathLike[str], stage: str = "trace_only",
               *, source_snapshot: dict[str, str] | None = None) -> Path:
    """Create a write-once seal for one stage and return its path."""
    case = Path(case_dir).resolve()
    if not case.is_dir():
        raise SealError(f"case directory does not exist: {case}")
    if stage not in STAGES:
        raise SealError(f"stage must be one of {STAGES}, got {stage!r}")
    seal_path = case / f"{stage}.seal.json"
    if seal_path.exists():
        raise SealError(f"refusing to overwrite existing seal: {seal_path}")
    output = case / f"{stage}.json"
    validate_prediction(case, stage)
    if stage == "final":
        for name in ("investigate.py", "evidence.md", "run.json"):
            if not (case / name).is_file():
                raise SealError(f"final stage requires {name}")
        run = _read_json(case / "run.json")
        if run.get("status") not in {"completed", "failed"}:
            raise SealError("final stage requires completed/failed run status")
    if stage == "trace_only":
        _snapshot_trace_inputs(case)
    refs = _declared_refs(case, stage)
    if not refs:
        raise SealError(f"no artifacts available to seal in {case}")
    hashes = {_relative(path, case): sha256_file(path) for path in refs}
    index = _index_path(case)
    manifest: dict[str, Any] = {
        "schema": "frontend-blind-v1/seal-1",
        "stage": stage,
        "case_dir": str(case),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output": _relative(output, case),
        "output_sha256": sha256_file(output),
        "input_sha256": hashes,
        "source_snapshot": source_snapshot if source_snapshot is not None else _source_snapshot(case),
    }
    if index is not None:
        stat = index.stat()
        manifest["index_provenance"] = {
            "path": _relative(index, REPO_ROOT), "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
    if stage == "final":
        trace_seal = case / "trace_only.seal.json"
        if not trace_seal.exists():
            raise SealError("final stage requires an existing trace_only.seal.json")
        verify_seal(case, "trace_only")
    if seal_path.exists():  # race-safe enough to fail before writing below
        raise SealError(f"refusing to overwrite existing seal: {seal_path}")
    # Exclusive create protects against two sealing processes racing.
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    try:
        fd = os.open(seal_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, "x") as fh:
            fh.write(payload)
    except FileExistsError as exc:
        raise SealError(f"refusing to overwrite existing seal: {seal_path}") from exc
    return seal_path


def verify_seal(case_dir: str | os.PathLike[str], stage: str) -> dict[str, Any]:
    case = Path(case_dir).resolve()
    seal_path = case / f"{stage}.seal.json"
    manifest = _read_json(seal_path)
    output = case / str(manifest.get("output", f"{stage}.json"))
    if manifest.get("stage") != stage:
        raise SealError(f"seal stage mismatch: {seal_path}")
    if manifest.get("output_sha256") != sha256_file(output):
        raise SealError(f"sealed output changed: {output}")
    for raw, expected in manifest.get("input_sha256", {}).items():
        path = case / raw
        if not path.exists() or sha256_file(path) != expected:
            raise SealError(f"sealed input changed or missing: {path}")
    index_info = manifest.get("index_provenance")
    if index_info:
        index = REPO_ROOT / str(index_info["path"])
        if not index.is_file():
            raise SealError(f"sealed index missing: {index}")
        stat = index.stat()
        if stat.st_size != int(index_info["size"]) or stat.st_mtime_ns != int(index_info["mtime_ns"]):
            raise SealError(f"sealed index provenance changed: {index}")
    # A source snapshot is a freeze, rather than metadata.  Recompute the
    # listed files and reject a post-seal infrastructure mutation.
    snapshot = manifest.get("source_snapshot", {})
    if snapshot:
        repo_root = REPO_ROOT
        for raw, expected in snapshot.items():
            path = repo_root / raw
            if not path.exists() or sha256_file(path) != expected:
                raise SealError(f"sealed source/config changed or missing: {path}")
    return manifest


def _iter_scope_row_ids(scope_csv: Path) -> set[int]:
    import csv
    with scope_csv.open(newline="") as fh:
        rows = csv.DictReader(fh)
        ids: set[int] = set()
        for row in rows:
            try:
                ids.add(int(row["row_id"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise SealError(f"invalid row_id in {scope_csv}: {row}") from exc
        return ids


def validate_all(case_root: str | os.PathLike[str] = DEFAULT_CASE_ROOT,
                 *, scope_csv: str | os.PathLike[str] = DEFAULT_SCOPE,
                 require_final: bool = True) -> dict[str, Any]:
    """Verify all scheduled rows are completed/failed and sealed."""
    root = Path(case_root).resolve()
    present = _iter_scope_row_ids(Path(scope_csv).resolve())
    expected = set(REQUIRED_ROW_IDS)
    allowed_scope = expected | {25}
    if present != allowed_scope:
        raise SealError(f"scope must contain exactly rows 0..69; got {sorted(present)}")
    records: list[dict[str, Any]] = []
    for row_id in sorted(expected):
        case = root / str(row_id)
        if not case.is_dir():
            raise SealError(f"missing case directory for row {row_id}")
        run = _read_json(case / "run.json")
        scope = _read_json(case / "scope.json")
        if str(scope.get("row_id")) != str(row_id):
            raise SealError(f"row {row_id} scope.json row_id mismatch: {scope.get('row_id')!r}")
        status = run.get("status")
        if status not in {"completed", "failed"}:
            raise SealError(f"row {row_id} run.json status must be completed/failed")
        if status == "failed" and not isinstance(run.get("failure"), dict):
            raise SealError(f"row {row_id} failed attempt needs a failure object")
        if status == "completed":
            verify_seal(case, "trace_only")
            if require_final:
                verify_seal(case, "final")
        elif (case / "trace_only.seal.json").exists():
            verify_seal(case, "trace_only")
        if status == "failed" and require_final and (case / "final.seal.json").exists():
            verify_seal(case, "final")
        records.append({"row_id": row_id, "status": status,
                        "stage_trace_sealed": True, "stage_final_sealed": require_final})
    return {"expected_rows": len(expected), "rows": records,
            "failed_rows": [r["row_id"] for r in records if r["status"] == "failed"]}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    seal = sub.add_parser("seal", help="write one stage seal")
    seal.add_argument("--case-dir", required=True)
    seal.add_argument("--stage", choices=STAGES, default="trace_only")
    check = sub.add_parser("validate-all", help="verify the all-case seal gate")
    check.add_argument("--case-root", default=str(DEFAULT_CASE_ROOT))
    check.add_argument("--scope", default=str(DEFAULT_SCOPE))
    check.add_argument("--trace-only", action="store_true", help="only require trace seals")
    args = parser.parse_args(argv)
    try:
        if args.command == "seal":
            print(seal_stage(args.case_dir, args.stage))
        else:
            report = validate_all(args.case_root, scope_csv=args.scope,
                                  require_final=not args.trace_only)
            print(json.dumps(report, indent=2, sort_keys=True))
    except SealError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
