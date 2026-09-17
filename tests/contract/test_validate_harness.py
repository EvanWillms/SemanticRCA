from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_harness.py"


PLACEHOLDER_EVIDENCE = """## Answer
Diagnosis is not implemented in this scaffold.

## Confidence
No confidence is measured because diagnosis is not implemented.

## Evidence
No evidence was assessed; this harness does not read telemetry.

## Ruled out
No alternatives were assessed because diagnosis is not implemented.
"""


def write_valid_artifacts(out: Path, row_ids: tuple[int, ...]) -> None:
    evidence_dir = out / "evidence"
    if evidence_dir.exists():
        shutil.rmtree(evidence_dir)
    evidence_dir.mkdir(parents=True)
    with (out / "predictions.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "prediction"])
        writer.writeheader()
        for row_id in row_ids:
            writer.writerow({"row_id": row_id, "prediction": ""})
    with (out / "usage.jsonl").open("w") as handle:
        for row_id in row_ids:
            handle.write(
                json.dumps(
                    {
                        "row_id": row_id,
                        "wall_s": 0.001,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "calls": 0,
                        "models": {},
                    }
                )
                + "\n"
            )
    for row_id in row_ids:
        (evidence_dir / f"{row_id}.md").write_text(PLACEHOLDER_EVIDENCE)


def write_queries(path: Path, row_ids: tuple[int, ...]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "instruction"])
        writer.writeheader()
        for row_id in row_ids:
            writer.writerow({"row_id": row_id, "instruction": f"query {row_id}"})


class ValidateHarnessCLITests(unittest.TestCase):
    def run_validator(self, queries: Path, out: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--queries", str(queries), "--out", str(out)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_accepts_valid_noncontiguous_outputs_with_scaffold_notice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            row_ids = (9, 42)
            write_queries(queries, row_ids)
            write_valid_artifacts(out, row_ids)

            result = self.run_validator(queries, out)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("scaffold-only", result.stdout.lower())
        self.assertIn("not official benchmark validation", result.stdout.lower())

    def test_rejects_duplicate_prediction_headers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, (9,))
            write_valid_artifacts(out, (9,))
            (out / "predictions.csv").write_text("row_id,prediction,prediction\n9,,\n")

            result = self.run_validator(queries, out)

        self.assertNotEqual(result.returncode, 0)

    def test_rejects_prediction_row_missing_a_column(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, (9,))
            write_valid_artifacts(out, (9,))
            (out / "predictions.csv").write_text("row_id,prediction\n9\n")

            result = self.run_validator(queries, out)

        self.assertNotEqual(result.returncode, 0)

    def test_rejects_evidence_without_unimplemented_answer_notice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, (9,))
            write_valid_artifacts(out, (9,))
            (out / "evidence" / "9.md").write_text(
                PLACEHOLDER_EVIDENCE.replace(
                    "Diagnosis is not implemented in this scaffold.",
                    "The answer is pending.",
                )
            )

            result = self.run_validator(queries, out)

        self.assertNotEqual(result.returncode, 0)

    def test_rejects_usage_without_explicit_zero_counters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, (9,))
            write_valid_artifacts(out, (9,))
            usage_path = out / "usage.jsonl"
            record = json.loads(usage_path.read_text())
            del record["calls"]
            usage_path.write_text(json.dumps(record) + "\n")

            result = self.run_validator(queries, out)

        self.assertNotEqual(result.returncode, 0)

    def test_rejects_malformed_evidence_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, (9,))
            write_valid_artifacts(out, (9,))
            (out / "evidence" / "9.md").write_text(
                PLACEHOLDER_EVIDENCE.replace("## Answer\n", "## Answer  \n")
            )

            result = self.run_validator(queries, out)

        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_unrepresentably_large_wall_time_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, (9,))
            write_valid_artifacts(out, (9,))
            usage_path = out / "usage.jsonl"
            record = json.loads(usage_path.read_text())
            record["wall_s"] = 10**1000
            usage_path.write_text(json.dumps(record) + "\n")

            result = self.run_validator(queries, out)

        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)

    def test_accepts_header_only_query_and_empty_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, ())
            write_valid_artifacts(out, ())

            result = self.run_validator(queries, out)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("scaffold-only", result.stdout.lower())

    def test_rejects_duplicate_and_unexpected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, (9, 42))

            write_valid_artifacts(out, (9, 42))
            with (out / "predictions.csv").open("a") as handle:
                handle.write("9,\n")
            duplicate_prediction = self.run_validator(queries, out)

            write_valid_artifacts(out, (9, 42))
            with (out / "usage.jsonl").open("a") as handle:
                handle.write(
                    json.dumps(
                        {
                            "row_id": 99,
                            "wall_s": 0.001,
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "calls": 0,
                            "models": {},
                        }
                    )
                    + "\n"
                )
            extra_usage = self.run_validator(queries, out)

            write_valid_artifacts(out, (9, 42))
            (out / "evidence" / "42.md").unlink()
            missing_evidence = self.run_validator(queries, out)

            write_valid_artifacts(out, (9, 42))
            (out / "evidence" / "99.md").write_text(PLACEHOLDER_EVIDENCE)
            extra_evidence = self.run_validator(queries, out)

            write_valid_artifacts(out, (9, 42))
            (out / "evidence" / "09.md").write_text(PLACEHOLDER_EVIDENCE)
            duplicate_evidence = self.run_validator(queries, out)

        for result in (
            duplicate_prediction,
            extra_usage,
            missing_evidence,
            extra_evidence,
            duplicate_evidence,
        ):
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_unexpected_root_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries = root / "query.csv"
            out = root / "out"
            out.mkdir()
            write_queries(queries, (9,))
            write_valid_artifacts(out, (9,))
            (out / "unexpected.json").write_text("{}")

            result = self.run_validator(queries, out)

        self.assertNotEqual(result.returncode, 0)

    def test_rejects_boolean_or_nonfinite_usage_values(self) -> None:
        invalid_values = {
            "wall_s": (True, float("nan"), float("inf"), -0.1),
            "prompt_tokens": (False, 1),
            "completion_tokens": (True, 1),
            "calls": (False, 1),
        }
        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        root = Path(temp_dir)
                        queries = root / "query.csv"
                        out = root / "out"
                        out.mkdir()
                        write_queries(queries, (9,))
                        write_valid_artifacts(out, (9,))
                        usage_path = out / "usage.jsonl"
                        record = json.loads(usage_path.read_text())
                        record[field] = value
                        usage_path.write_text(json.dumps(record) + "\n")

                        result = self.run_validator(queries, out)

                    self.assertNotEqual(result.returncode, 0)
