"""The discovery CLI turns persisted comparison evidence into findings."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.demo_discovery import _write_bundle


class InputToFindingCLITest(unittest.TestCase):
    def test_demo_bundle_produces_source_linked_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            query = _write_bundle(bundle)
            output = root / "out"

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/discover.py",
                    "--dataset",
                    str(bundle),
                    "--queries",
                    str(query),
                    "--out",
                    str(output),
                ],
                cwd=Path(__file__).parents[2],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("frontend-0", result.stdout)
            self.assertIn("raw change 200", result.stdout)
            self.assertIn("worker-2", result.stdout)
            self.assertIn("change 25", result.stdout)
            findings = output / "findings.md"
            self.assertTrue(findings.is_file())
            content = findings.read_text(encoding="utf-8")
            self.assertIn("frontend-0", content)
            self.assertIn("worker-2", content)
            self.assertIn(str((bundle / "telemetry").resolve()), content)


if __name__ == "__main__":
    unittest.main()
