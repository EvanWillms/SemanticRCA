"""Checkpoint preservation and credential-free integration behavior."""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from run import main


def _write_queries(path: Path, rows: list[tuple[int, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("row_id", "instruction"))
        writer.writerows(rows)


def _invoke(dataset: Path, queries: Path, output: Path) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        status = main(
            [
                "--dataset",
                str(dataset),
                "--queries",
                str(queries),
                "--out",
                str(output),
                "--agent",
                "agents.submission",
            ]
        )
    return status, stdout.getvalue(), stderr.getvalue()


class HarnessCheckpointTests(unittest.TestCase):
    def test_replace_failure_preserves_last_complete_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(9, "first"), (42, "second"), (77, "third")])
            output = root / "out"
            real_replace = os.replace
            def fail_when_second_case_is_published(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
                with Path(source).open(newline="", encoding="utf-8") as handle:
                    candidate_ids = {int(row["row_id"]) for row in csv.DictReader(handle)}
                if 42 in candidate_ids:
                    raise OSError("injected checkpoint failure")
                real_replace(source, destination)

            with patch("rca.outputs.os.replace", side_effect=fail_when_second_case_is_published):
                status, _, stderr = _invoke(dataset, queries, output)

            self.assertNotEqual(status, 0)
            self.assertIn("could not persist case 42", stderr)
            with (output / "predictions.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([(int(row["row_id"]), row["prediction"]) for row in rows], [(9, "")])
            usage = [
                json.loads(line)
                for line in (output / "usage.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([record["row_id"] for record in usage], [9])
            self.assertEqual([path.name for path in (output / "evidence").iterdir()], ["9.md"])
            self.assertEqual(
                {path.name for path in output.iterdir()},
                {"predictions.csv", "usage.jsonl", "evidence"},
            )

    def test_supplied_credentials_are_never_read_into_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(9, "task_1: no call")])
            output = root / "out"
            secret = "sentinel-secret-value"

            with patch.dict(
                os.environ,
                {
                    "FEATHERLESS_API_KEY": secret,
                    "FEATHERLESS_BASE_URL": "https://sentinel.invalid/v1",
                },
                clear=False,
            ):
                status, stdout, stderr = _invoke(dataset, queries, output)

            self.assertEqual(status, 0, stderr)
            self.assertNotIn(secret, stdout + stderr)
            for artifact in output.rglob("*"):
                if artifact.is_file():
                    self.assertNotIn(secret, artifact.read_text(encoding="utf-8"))

    def test_run_succeeds_without_featherless_environment_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(17, "task_2: no credentials needed")])
            output = root / "out"

            with patch.dict(
                os.environ,
                {"FEATHERLESS_API_KEY": "", "FEATHERLESS_BASE_URL": ""},
                clear=False,
            ):
                status, stdout, stderr = _invoke(dataset, queries, output)

            self.assertEqual(status, 0, stderr)
            self.assertIn("harness-only", stdout.lower())

    def test_cli_does_not_create_source_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(17, "task_2: no bytecode")])
            output = root / "out"
            repository = Path(__file__).parents[2]
            runtime = root / "runtime"
            runtime.mkdir()
            shutil.copy2(repository / "run.py", runtime / "run.py")
            shutil.copytree(repository / "agents", runtime / "agents", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(repository / "rca", runtime / "rca", ignore=shutil.ignore_patterns("__pycache__"))
            environment = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith("FEATHERLESS_")
                and key not in {"PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"}
            }
            completed = subprocess.run(
                [
                    sys.executable,
                    str(runtime / "run.py"),
                    "--dataset",
                    str(dataset),
                    "--queries",
                    str(queries),
                    "--out",
                    str(output),
                    "--agent",
                    "agents.submission",
                ],
                capture_output=True,
                text=True,
                cwd=runtime,
                env=environment,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(list(runtime.rglob("*.pyc")), [])


if __name__ == "__main__":
    unittest.main()
