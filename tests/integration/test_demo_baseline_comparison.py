"""One public CLI check for the authored source-to-descriptor demo."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class FixtureDemoTest(unittest.TestCase):
    def test_fixture_demo_prints_and_saves_all_query_outcomes(self):
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "demo"
            result = subprocess.run(
                [sys.executable, str(repo / "scripts/demo_baseline_comparison.py"),
                 "--output-dir", str(output)],
                cwd=tmp, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Fixture check: PASS", result.stdout)
            report = json.loads((output / "demo.json").read_text())
            self.assertEqual(report["assignment_count"], 8)
            rows = {row["trace_id"]: row for row in report["descriptors"]}
            self.assertEqual(rows["query-0"]["duration"]["signed_excess"]["value"], 2)
            self.assertEqual(rows["query-1"]["duration"]["signed_excess"]["value"], -2)
            self.assertEqual(rows["query-2"]["duration"]["signed_excess"]["value"], 0)
            self.assertEqual(rows["query-zero"]["duration"]["signed_excess"]["value"], 12)
            self.assertEqual(rows["query-new"]["duration"]["signed_excess"]["status"], "unavailable")
            summary = (output / "demo.md").read_text()
            self.assertIn("query-new", summary)
            self.assertIn("semantic evidence validation", summary)
            self.assertEqual(json.loads((output / "fixture-check.json").read_text())["status"], "passed")


if __name__ == "__main__":
    unittest.main()
