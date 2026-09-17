"""Independent happy-path checks at the raw CSV → descriptor public seam."""
from pathlib import Path
import tempfile
import unittest

from rca.baselining.demo import run_demo


class BaselineDemoTest(unittest.TestCase):
    def test_raw_sources_to_all_six_slices(self):
        dataset = Path(__file__).parents[1] / "fixtures/qualified_baselines/dataset"
        with tempfile.TemporaryDirectory() as output:
            result = run_demo(dataset, "demo", 1788221100000, Path(output))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["assignment_count"], 8)
        self.assertEqual(sorted(item["member_count"] for item in result["baselines"]), [20, 20])
        self.assertEqual(sorted(item["median_ms"] for item in result["baselines"]), [0, 10])
        self.assertTrue(all(item["support"] == "supported" for item in result["baselines"]))
        descriptors = {item["trace_id"]: item for item in result["descriptors"]}
        self.assertEqual([descriptors[f"query-{i}"]["slice_index"] for i in range(6)], list(range(6)))
        self.assertEqual([descriptors[f"query-{i}"]["duration"]["signed_excess"]["value"] for i in range(6)], [2, -2, 0, 2, 2, 2])
        zero = descriptors["query-zero"]["duration"]
        self.assertEqual(zero["signed_excess"]["value"], 12)
        self.assertEqual(zero["ratio"]["status"], "undefined")
        self.assertEqual(zero["mad_departure"]["status"], "undefined")
        self.assertEqual(descriptors["query-new"]["duration"]["signed_excess"]["status"], "unavailable")
        self.assertFalse(descriptors["query-0"]["structure"]["absent_from_reference"]["value"])
        self.assertEqual(len(descriptors["query-0"]["structure"]["pattern_differences"]), 1)
        self.assertTrue(descriptors["query-0"]["duration"]["observed"]["evidence"])


if __name__ == "__main__":
    unittest.main()
