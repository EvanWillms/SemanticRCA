"""Public output contract tests for the empty-output harness."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class EmptyOutputContractTests(unittest.TestCase):
    def test_cli_preserves_noncontiguous_ids_and_writes_empty_case_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            with queries.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(("row_id", "instruction"))
                writer.writerow((9, "task_1: what happened?\nInclude the timeline."))
                writer.writerow((42, "task_7: explain the failure."))
            output = root / "out"

            completed = subprocess.run(
                [
                    sys.executable,
                    "run.py",
                    "--agent", "agents.submission",
                    "--dataset",
                    str(dataset),
                    "--queries",
                    str(queries),
                    "--out",
                    str(output),
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parents[2],
                env={key: value for key, value in os.environ.items() if not key.startswith("FEATHERLESS_")},
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("harness-only", completed.stdout.lower())
            with (output / "predictions.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([int(row["row_id"]) for row in rows], [9, 42])
            self.assertEqual([row["prediction"] for row in rows], ["", ""])

            evidence = (output / "evidence" / "9.md").read_text(encoding="utf-8")
            self.assertIn("## Answer", evidence)
            self.assertIn("## Confidence", evidence)
            self.assertIn("## Evidence", evidence)
            self.assertIn("## Ruled out", evidence)
            usage = [
                json.loads(line)
                for line in (output / "usage.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([record["row_id"] for record in usage], [9, 42])
            self.assertTrue(all(record["models"] == {} for record in usage))
            self.assertTrue(all(record["calls"] == 0 for record in usage))
            self.assertTrue(all(record["prompt_tokens"] == 0 for record in usage))
            self.assertTrue(all(record["completion_tokens"] == 0 for record in usage))

    def test_all_task_labels_flow_through_as_blank_placeholders(self) -> None:
        labels = [f"task_{number}" for number in range(1, 8)]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            with queries.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(("row_id", "instruction"))
                for row_id, label in zip((101, 7, 9001, 13, 81, 4, 600), labels):
                    writer.writerow((row_id, f"{label}: preserve this request"))
            output = root / "out"

            completed = subprocess.run(
                [
                    sys.executable,
                    "run.py",
                    "--agent", "agents.submission",
                    "--dataset",
                    str(dataset),
                    "--queries",
                    str(queries),
                    "--out",
                    str(output),
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parents[2],
                env={key: value for key, value in os.environ.items() if not key.startswith("FEATHERLESS_")},
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            with (output / "predictions.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([int(row["row_id"]) for row in rows], [101, 7, 9001, 13, 81, 4, 600])
            self.assertEqual([row["prediction"] for row in rows], [""] * 7)
            for row_id in (101, 7, 9001, 13, 81, 4, 600):
                evidence = (output / "evidence" / f"{row_id}.md").read_text(encoding="utf-8")
                for heading in ("## Answer", "## Confidence", "## Evidence", "## Ruled out"):
                    self.assertIn(heading, evidence)
                self.assertIn("not implemented", evidence.lower())
                self.assertIn("no telemetry evidence", evidence.lower())
                self.assertIn("no alternatives", evidence.lower())


if __name__ == "__main__":
    unittest.main()
