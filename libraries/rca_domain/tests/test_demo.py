from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from rca_domain.demo import run_demo


def test_demo_runs_public_happy_path_and_cli_emits_the_same_json():
    result = run_demo()

    assert result["demo"] == {
        "mode": "synthetic",
        "live_llm": False,
        "real_diagnosis_accuracy_claim": False,
    }
    assert result["answer"]
    assert result["answer"] == [{"component": "worker-1", "reason": "resource saturation"}]
    assert result["investigation_stop_reason"] == "evidence_sufficient"
    assert result["execution_status"] == "completed"
    assert result["evidence_adequacy"] == "supported"
    assert len(result["assessments"]) == 2
    assert len(result["operations"]) == 1
    assert result["operations"][0]["name"] == "inspect_worker"

    observations = result["evidence"]["observations"]
    assert any(item["recording_component"] == "frontend-1" for item in observations.values())
    worker_observation = next(
        item for item in observations.values() if item["recording_component"] == "worker-1"
    )
    assert worker_observation["raw"]["status_code"] == "unknown-status"
    assert worker_observation["raw"]["queue_depth"] == 64
    assert worker_observation["raw"]["queue_capacity"] == 64
    assert worker_observation["raw"]["resource_state"] == "saturated"

    repo = Path(__file__).resolve().parents[3]
    pythonpath = os.pathsep.join(
        [
            str(repo / "libraries" / "rca_domain" / "src"),
            str(repo / "libraries" / "trace_semantics" / "src"),
            os.environ.get("PYTHONPATH", ""),
        ]
    )
    completed = subprocess.run(
        [sys.executable, "-m", "rca_domain.demo"],
        cwd=repo,
        env={**os.environ, "PYTHONPATH": pythonpath},
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout) == result
