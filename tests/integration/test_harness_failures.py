"""Preflight and empty-input integration behavior."""

from __future__ import annotations

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from run import main


def _write_queries(path: Path, rows: list[tuple[object, object]], headers: tuple[str, ...] = ("row_id", "instruction")) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def _invoke(dataset: Path, queries: Path, output: Path) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        status = main(
            [
                "--agent", "agents.submission",
                "--dataset",
                str(dataset),
                "--queries",
                str(queries),
                "--out",
                str(output),
            ]
        )
    return status, stdout.getvalue(), stderr.getvalue()


class HarnessPreflightTests(unittest.TestCase):
    def test_header_only_input_writes_only_empty_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [])
            output = root / "out"

            status, stdout, stderr = _invoke(dataset, queries, output)

            self.assertEqual(status, 0, stderr)
            self.assertIn("harness-only", stdout.lower())
            self.assertEqual((output / "predictions.csv").read_text(encoding="utf-8"), "row_id,prediction\n")
            self.assertEqual((output / "usage.jsonl").read_text(encoding="utf-8"), "")
            self.assertEqual(list((output / "evidence").iterdir()), [])

    def test_invalid_csv_rows_fail_before_creating_output(self) -> None:
        cases = (
            ([(1, "first"), (1, "duplicate")], "repeats row_id"),
            ([('3.14', "float")], "invalid row_id"),
        )
        for rows, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                dataset = root / "dataset"
                dataset.mkdir()
                queries = dataset / "query.csv"
                _write_queries(queries, rows)
                output = root / "out"

                status, _, stderr = _invoke(dataset, queries, output)

                self.assertNotEqual(status, 0)
                self.assertIn(expected, stderr)
                self.assertFalse(output.exists())

    def test_missing_header_fails_before_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(1, "ignored")], headers=("row_id", "wrong"))
            output = root / "out"

            status, _, stderr = _invoke(dataset, queries, output)

            self.assertNotEqual(status, 0)
            self.assertIn("missing required header", stderr)
            self.assertFalse(output.exists())

    def test_malformed_csv_fails_before_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            queries.write_text('row_id,instruction\n1,"unterminated\n', encoding="utf-8")
            output = root / "out"

            status, _, stderr = _invoke(dataset, queries, output)

            self.assertNotEqual(status, 0)
            self.assertIn("could not be read as valid", stderr)
            self.assertFalse(output.exists())

    def test_missing_paths_fail_before_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "out"

            status, _, stderr = _invoke(root / "missing-dataset", root / "missing-query.csv", output)

            self.assertNotEqual(status, 0)
            self.assertIn("dataset path", stderr)
            self.assertFalse(output.exists())

    def test_nonempty_output_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(1, "query")])
            output = root / "out"
            output.mkdir()
            sentinel = output / "existing.txt"
            sentinel.write_text("keep me", encoding="utf-8")

            status, _, stderr = _invoke(dataset, queries, output)

            self.assertNotEqual(status, 0)
            self.assertIn("must be empty", stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep me")
            self.assertFalse((output / "predictions.csv").exists())

    def test_output_input_overlap_is_rejected_in_both_directions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(1, "query")])

            inside_dataset = dataset / "out"
            status, _, stderr = _invoke(dataset, queries, inside_dataset)
            self.assertNotEqual(status, 0)
            self.assertIn("overlaps", stderr)
            self.assertFalse(inside_dataset.exists())

            output_parent = root / "output-parent"
            output_parent.mkdir()
            nested_dataset = output_parent / "dataset"
            nested_dataset.mkdir()
            nested_queries = nested_dataset / "query.csv"
            _write_queries(nested_queries, [(1, "query")])
            status, _, stderr = _invoke(nested_dataset, nested_queries, output_parent)
            self.assertNotEqual(status, 0)
            self.assertIn("overlaps", stderr)
            self.assertFalse((output_parent / "predictions.csv").exists())

            query_inside_output = root / "query-output"
            query_inside_output.mkdir()
            query_path = query_inside_output / "query.csv"
            _write_queries(query_path, [(1, "query")])
            status, _, stderr = _invoke(dataset, query_path, query_inside_output)
            self.assertNotEqual(status, 0)
            self.assertIn("overlaps", stderr)
            self.assertFalse((query_inside_output / "predictions.csv").exists())

    def test_unknown_agent_fails_without_initializing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(1, "query")])
            output = root / "out"

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
                        "agents.missing",
                    ]
                )

            self.assertNotEqual(status, 0)
            self.assertIn("could not initialize", stderr.getvalue())
            self.assertEqual(stdout.getvalue(), "")
            self.assertFalse(output.exists())

    def test_resume_flag_is_rejected_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dataset = root / "dataset"
            dataset.mkdir()
            queries = dataset / "query.csv"
            _write_queries(queries, [(1, "query")])
            output = root / "out"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                main(
                    [
                        "--dataset",
                        str(dataset),
                        "--queries",
                        str(queries),
                        "--out",
                        str(output),
                        "--resume",
                    ]
                )

            self.assertNotEqual(raised.exception.code, 0)
            self.assertIn("resume is unsupported", stderr.getvalue())
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
