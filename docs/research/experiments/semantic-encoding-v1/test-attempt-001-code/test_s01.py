"""Focused, pre-execution contract tests for the isolated S01 codec."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from . import run_s01
from .codec import canonical_structure, decode, encode


ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"


class S01CodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.codebook = json.loads((FIXTURES / "codebook.json").read_text())
        cls.policy = json.loads((FIXTURES / "policy.json").read_text())
        cls.expected = json.loads((FIXTURES / "expected-facts.json").read_text())
        cls.fixtures = {
            name: json.loads((FIXTURES / f"{name}.json").read_text())
            for name in ("T0", "T1", "T2")
        }

    @staticmethod
    def _source_hash(name: str) -> str:
        return hashlib.sha256((FIXTURES / f"{name}.json").read_bytes()).hexdigest()

    def _encode(self, name: str, fixture: dict | None = None):
        source = copy.deepcopy(fixture if fixture is not None else self.fixtures[name])
        packet, sidecar = encode(
            source,
            self.codebook,
            self.policy,
            self._source_hash(name) if fixture is None else "mutated-source",
        )
        return source, packet, sidecar, decode(packet)

    def test_frozen_fixtures_recover_all_structural_facts(self) -> None:
        for name in ("T0", "T1", "T2"):
            with self.subTest(fixture=name):
                source, packet, sidecar, facts = self._encode(name)
                differences = {
                    key: value
                    for key, value in run_s01.compare(
                        facts, self.expected["fixtures"][name]
                    ).items()
                    if not value["passed"]
                }
                self.assertEqual(differences, {})
                audit = run_s01.provenance_audit(
                    source, packet, sidecar, facts, self._source_hash(name)
                )
                self.assertTrue(audit["passed"], audit)
                self.assertTrue(
                    all(value["passed"] for value in run_s01.quality_checks(facts).values())
                )

    def test_t1_identifier_and_storage_order_changes_preserve_structure(self) -> None:
        _, _, _, t0 = self._encode("T0")
        _, _, _, t1 = self._encode("T1")

        self.assertEqual(canonical_structure(t0), canonical_structure(t1))
        self.assertEqual(t0["counts"], t1["counts"])
        self.assertEqual(t0["span_count"], t1["span_count"])
        self.assertEqual(t0["edge_count"], t1["edge_count"])

    def test_t2_added_occurrence_and_edge_remain_visible(self) -> None:
        _, _, _, t0 = self._encode("T0")
        _, _, _, t2 = self._encode("T2")
        t0_ids = {node["id"] for node in t0["nodes"]}
        added_nodes = [
            [node["id"], node["operation"], node["parent"], node["entity"]]
            for node in t2["nodes"]
            if node["id"] not in t0_ids
        ]
        added_edges = [edge for edge in t2["edges"] if edge not in t0["edges"]]

        self.assertEqual(added_nodes, [self.expected["contrasts"]["added_node"]])
        self.assertEqual(added_edges, [self.expected["contrasts"]["added_edge"]])
        self.assertEqual(t2["span_count"] - t0["span_count"], 1)
        self.assertEqual(t2["edge_count"] - t0["edge_count"], 1)
        self.assertNotEqual(canonical_structure(t0), canonical_structure(t2))

    def test_missing_occurrence_fails_frozen_t2_expectations(self) -> None:
        mutated = copy.deepcopy(self.fixtures["T2"])
        mutated["records"] = [
            row for row in mutated["records"] if row["span_id"] != "0ab7"
        ]
        _, _, _, facts = self._encode("T2", mutated)

        checks = run_s01.compare(facts, self.expected["fixtures"]["T2"])
        self.assertFalse(checks["nodes"]["passed"])
        self.assertFalse(checks["counts"]["passed"])
        self.assertFalse(checks["span_count"]["passed"])
        self.assertFalse(checks["edge_count"]["passed"])

    def test_entity_binding_mutation_is_detected_without_count_or_edge_change(self) -> None:
        mutated = copy.deepcopy(self.fixtures["T0"])
        next(row for row in mutated["records"] if row["span_id"] == "6fa6")["cmdb_id"] = "catalog#1"
        _, _, _, facts = self._encode("T0", mutated)

        checks = run_s01.compare(facts, self.expected["fixtures"]["T0"])
        self.assertTrue(checks["counts"]["passed"])
        self.assertTrue(checks["edges"]["passed"])
        self.assertTrue(checks["span_count"]["passed"])
        self.assertFalse(checks["same_entity_pairs"]["passed"])
        self.assertFalse(checks["different_entity_pairs"]["passed"])
        self.assertFalse(checks["distinct_pair_count"]["passed"])

    def test_parent_edge_mutation_is_detected_without_count_or_entity_change(self) -> None:
        mutated = copy.deepcopy(self.fixtures["T0"])
        next(row for row in mutated["records"] if row["span_id"] == "4de4")["parent_span"] = "9ce1"
        _, _, _, facts = self._encode("T0", mutated)

        checks = run_s01.compare(facts, self.expected["fixtures"]["T0"])
        self.assertTrue(checks["counts"]["passed"])
        self.assertTrue(checks["same_entity_pairs"]["passed"])
        self.assertTrue(checks["span_count"]["passed"])
        self.assertTrue(checks["edge_count"]["passed"])
        self.assertFalse(checks["edges"]["passed"])
        self.assertNotEqual(
            canonical_structure(facts), canonical_structure(self._encode("T0")[3])
        )

    def test_missing_binding_and_parent_are_rejected_at_encode_boundary(self) -> None:
        missing_binding = copy.deepcopy(self.fixtures["T0"])
        del next(row for row in missing_binding["records"] if row["span_id"] == "6fa6")["cmdb_id"]
        with self.assertRaisesRegex(ValueError, "missing required field"):
            self._encode("T0", missing_binding)

        missing_parent = copy.deepcopy(self.fixtures["T0"])
        next(row for row in missing_parent["records"] if row["span_id"] == "4de4")["parent_span"] = "missing-parent"
        with self.assertRaisesRegex(ValueError, "resolved parents"):
            self._encode("T0", missing_parent)

    def test_provenance_corruption_is_reported_without_raising(self) -> None:
        source, packet, sidecar, facts = self._encode("T0")
        evidence = facts["nodes"][0]["evidence"]
        corrupted = copy.deepcopy(sidecar)
        corrupted["records"][evidence]["row_sha256"] = "0" * 64

        audit = run_s01.provenance_audit(
            source, packet, corrupted, facts, self._source_hash("T0")
        )
        self.assertFalse(audit["passed"])
        self.assertIn(evidence, audit["differences"])

        corrupted["records"][evidence]["record_index_1based"] = "bad-index"
        audit = run_s01.provenance_audit(
            source, packet, corrupted, facts, self._source_hash("T0")
        )
        self.assertFalse(audit["passed"])
        self.assertIn(evidence + ":index", audit["differences"])

        del corrupted["records"][evidence]["row_sha256"]
        audit = run_s01.provenance_audit(
            source, packet, corrupted, facts, self._source_hash("T0")
        )
        self.assertFalse(audit["passed"])
        self.assertIn(evidence, audit["differences"])

    def test_quality_checks_cover_root_marker_and_resolved_parents(self) -> None:
        _, _, _, facts = self._encode("T0")
        checks = run_s01.quality_checks(facts)
        self.assertTrue(all(value["passed"] for value in checks.values()), checks)

        corrupted = copy.deepcopy(facts)
        corrupted["quality"]["retrieval"] = "unknown"
        corrupted["nodes"][1]["parent_resolution"] = "unknown"
        checks = run_s01.quality_checks(corrupted)
        self.assertFalse(checks["quality"]["passed"])
        self.assertFalse(checks["resolved_parents"]["passed"])

    def test_run_directory_rejects_reuse_and_creates_missing_parents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_root = run_s01.ROOT
            run_s01.ROOT = Path(temp_dir)
            try:
                first = run_s01.create_run_dir("attempt-1")
                self.assertTrue(first.is_dir())
                self.assertTrue(
                    first.parent == Path(temp_dir) / "data/experiments/semantic-encoding-v1/S01"
                )
                with self.assertRaises(FileExistsError):
                    run_s01.create_run_dir("attempt-1")
            finally:
                run_s01.ROOT = original_root


if __name__ == "__main__":
    unittest.main()
