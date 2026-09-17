"""User-authorized eight-case population adapter; frozen scoring logic unchanged.

This file is outside the original source freeze. It changes only the scheduled
population and output destination. Labels remain gated on every selected seal.
"""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime, timezone

from experiments.frontend_blind_v1 import seal, evaluate

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / "data/experiments/frontend-blind-v1"
SELECTION = RUN / "orchestration/random8_selection.json"
SCOPE = RUN / "orchestration/random8_scope.csv"
OUT = RUN / "random8-results"


def configure():
    selection = json.loads(SELECTION.read_text())
    rows = tuple(selection["selected_rows"])
    if rows != (3, 6, 14, 17, 29, 32, 36, 48):
        raise ValueError("Selection differs from the recorded seed-42 amendment")
    # Scope parameters only: do not mutate any source file or scoring function.
    seal.REQUIRED_ROW_IDS = rows
    evaluate.REQUIRED_ROW_IDS = rows
    return rows


def gate():
    rows = configure()
    result = seal.validate_all(RUN / "cases", scope_csv=SCOPE, require_final=True)
    # Require both immutable artifacts even for a failed investigation.
    for rid in rows:
        for stage in ("trace_only", "final"):
            seal.verify_seal(RUN / f"cases/{rid}", stage)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("gate", "evaluate"))
    parser.add_argument("--labels", type=Path, default=ROOT / "data/track-1/dev/query_dev.csv")
    args = parser.parse_args()
    verified = gate()  # Mandatory before any label-file access.
    if args.command == "gate":
        print(json.dumps(verified, indent=2))
        return
    rows = set(configure())
    original_loader = evaluate._load_labels
    evaluate._load_labels = lambda path: {rid: row for rid, row in original_loader(path).items() if rid in rows}
    OUT.mkdir(parents=True, exist_ok=True)
    audit = {
        "opened_after_gate_at": datetime.now(timezone.utc).isoformat(),
        "selected_rows": sorted(rows), "gate": verified,
        "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "selection_sha256": hashlib.sha256(SELECTION.read_bytes()).hexdigest(),
        "scope_sha256": hashlib.sha256(SCOPE.read_bytes()).hexdigest(),
        "amendment": "docs/research/experiments/frontend-blind-v1/RANDOM8-AMENDMENT.md",
        "population_change": "Eight selected rows only; original official scoring function unchanged",
    }
    audit_path = OUT / "unblinding.json"
    if not audit_path.exists():
        audit_path.write_text(json.dumps(audit, indent=2) + "\n")
    else:
        with (OUT / "evaluation_reruns.jsonl").open("a") as stream:
            stream.write(json.dumps(audit) + "\n")
    report = evaluate.evaluate(case_root=RUN / "cases", scope_path=SCOPE,
                               labels_path=args.labels, output_dir=OUT)
    report["population"] = {"selected_rows": sorted(rows), "seed": 42,
                            "amendment": audit["amendment"]}
    for values in report["stages"].values():
        # The frozen evaluator's legacy key contains a number in its name.
        # Rename the output key only; its computed denominator already uses 8.
        values["canonical_selected"] = values.pop("canonical_56")
    (OUT / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(OUT), "gate": report["gate"],
                      "stages": {stage: values["by_task"] for stage, values in report["stages"].items()}}, indent=2))


if __name__ == "__main__":
    main()
