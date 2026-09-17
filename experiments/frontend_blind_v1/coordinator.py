"""Label-free scheduling ledger for the human-visible subagent orchestration.

Does not spawn agents or inspect answer keys. Subagents are launched through
the Codex collaboration tool with the recorded model and reasoning settings.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "data/experiments/frontend-blind-v1"
SCOPE = ROOT / "docs/research/experiments/frontend-blind-v1/scope.csv"
LEDGER = RUN / "orchestration/dispatch.jsonl"


def now():
    return datetime.now(timezone.utc).isoformat()


def scopes():
    with SCOPE.open() as stream:
        return {int(r["row_id"]): r for r in csv.DictReader(stream) if r["role"] == "trial"}


def append(event):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as stream:
        stream.write(json.dumps(dict(timestamp=now(), **event)) + "\n")


def events():
    return [json.loads(line) for line in LEDGER.read_text().splitlines()] if LEDGER.exists() else []


def status():
    records = scopes()
    dispatched = {e["row_id"]: e for e in events() if e["event"] == "dispatch"}
    sealed = sorted(r for r in records if (RUN / f"cases/{r}/final.seal.json").exists())
    return {"scheduled": len(records), "dispatched": len(dispatched), "sealed_count": len(sealed),
            "sealed_rows": sealed,
            "active_or_unsealed": [{"row_id": r, "task_name": e["task_name"], "started": e["timestamp"]}
                                   for r, e in dispatched.items() if r not in sealed],
            "undispatched": sorted(set(records) - set(dispatched))}


def freeze():
    target = RUN / "orchestration/frozen_sources.json"
    if target.exists():
        raise SystemExit("Source freeze already exists; create a declared revision instead of overwriting")
    paths = [p for p in sorted((ROOT / "experiments/frontend_blind_v1").rglob("*"))
             if p.is_file() and p.suffix in {".py", ".json", ".md", ".txt"}]
    paths += [SCOPE, RUN / "orchestration/telemetry_sources.json",
              ROOT / "docs/research/experiments/frontend-blind-v1/PLAN.md"]
    manifest = {"frozen_at": now(), "model": "gpt-5.6-luna", "reasoning_effort": "high",
                "files": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in paths}}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def prompt(row_id):
    row = scopes()[row_id]
    case = RUN / f"cases/{row_id}"
    return f"""You are the independent Luna-high investigator for development prompt {row_id}.
Work in {ROOT}. Do not spawn agents. You have a fresh context and a 15-minute
investigation budget. First read ONLY these instruction/API files:
  experiments/frontend_blind_v1/INVESTIGATOR.md
  experiments/frontend_blind_v1/SCHEMA.md
  experiments/frontend_blind_v1/DATA_API.md
and your own {case}/scope.json, rankings.json, trace_evidence.json.
Your exact public instruction is: {row['instruction']}
Your case directory is {case}. Write only inside this directory.
Use /private/tmp/symbolicrca-pyod-venv/bin/python with PYTHONPATH={ROOT}.
Write and execute investigate.py that recomputes trace evidence, inspect the results,
then write and seal trace_only.json BEFORE any metrics/log retrieval. Complete the
bounded Stage M investigation through retrieval.py, write final.json and evidence.md,
then seal final. All shared source/config is frozen: do not change it.
Never read dev/query_dev.csv, scoring_points, record.csv, gold, previous reports,
other case directories, frozen control reports, or Git history. No web lookup of
benchmark answers. Never inspect outputs from other investigators.
If an API fails, report the exact exception to root; do not bypass retrieval limits
or read raw metrics/logs directly. Keep the original failed execution record.
Read data programmatically and print compact summaries, not whole giant JSON files.
You must actually write AND run case code and finish the two sealed artifacts.
In your final message report case ID, artifact paths, execution outcome, and any
protocol exposure or error. No answer-key evaluation is allowed in this task.
"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("freeze")
    a = sub.add_parser("dispatch")
    a.add_argument("row_id", type=int)
    a.add_argument("task_name")
    a = sub.add_parser("prompt")
    a.add_argument("row_id", type=int)
    a = sub.add_parser("event")
    a.add_argument("row_id", type=int)
    a.add_argument("event")
    a.add_argument("note")
    args = p.parse_args()
    if args.command == "status":
        print(json.dumps(status(), indent=2))
    elif args.command == "freeze":
        print(json.dumps(freeze(), indent=2))
    elif args.command == "dispatch":
        if args.row_id not in scopes():
            raise SystemExit("Not a trial row")
        if any(e["event"] == "dispatch" and e["row_id"] == args.row_id for e in events()):
            raise SystemExit("Already dispatched; log explicit retry instead")
        append({"event": "dispatch", "row_id": args.row_id, "task_name": args.task_name,
                "model": "gpt-5.6-luna", "reasoning_effort": "high", "fork_turns": "none"})
    elif args.command == "prompt":
        print(prompt(args.row_id))
    else:
        append({"event": args.event, "row_id": args.row_id, "note": args.note})


if __name__ == "__main__":
    main()
