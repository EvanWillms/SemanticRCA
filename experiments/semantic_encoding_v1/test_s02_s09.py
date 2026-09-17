"""Focused contract checks for the lean S02-S09 runner."""

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from . import run_s02_s09 as runner
from . import run_s09_live as s09


class S02S09Tests(unittest.TestCase):
    def test_r0_source_has_frozen_full_inventory(self):
        rows, ref = runner.load_r0()
        frozen = runner.load_frozen_expectations()["R0"]
        self.assertEqual(len(rows), 37)
        self.assertEqual(len({row["cmdb_id"] for row in rows}), 13)
        self.assertEqual(sum(row["parent_span"] == "" for row in rows), 1)
        self.assertEqual(Counter(row["status_code"] for row in rows), {"0": 33, "200": 2, "Ok": 2})
        packet, sidecar = runner.encode_rows(rows, "test-r0", ref, duration_unit="unknown")
        decoded = runner.decode_packet(packet)
        self.assertEqual(decoded["records"], frozen["rows"])
        expected_relations = {key: frozen[key] for key in ("entities", "counts", "parent_edges", "same_entity_pairs", "different_entity_pairs", "span_count", "edge_count")}
        self.assertEqual(runner.relation_facts(decoded), expected_relations)
        self.assertTrue(runner.audit_provenance(packet, sidecar, rows)["passed"])

        corrupted = json.loads(json.dumps(decoded))
        corrupted["edges"][0][1] = "forged-child"
        corrupted_check = runner.validate_decoded(
            corrupted, expected_rows=frozen["rows"], expected_relations=expected_relations,
            packet=packet, sidecar=sidecar, source_rows=rows)
        self.assertFalse(corrupted_check["passed"])
        self.assertFalse(corrupted_check["relations"]["parent_edges"]["passed"])
        self.assertFalse(corrupted_check["raw_consistency"]["parent_edges"]["passed"])

        corrupted_entities = json.loads(json.dumps(decoded))
        corrupted_entities["entities"][0] = "forged-entity"
        entity_check = runner.validate_decoded(
            corrupted_entities, expected_rows=frozen["rows"], expected_relations=expected_relations,
            packet=packet, sidecar=sidecar, source_rows=rows)
        self.assertFalse(entity_check["passed"])
        self.assertFalse(entity_check["relations"]["entities"]["passed"])
        self.assertFalse(entity_check["raw_consistency"]["entities"]["passed"])

    def test_missing_and_conflicting_quality_are_distinct(self):
        complete, missing, duplicate = runner.authored_s04_cases()
        missing_packet, _ = runner.encode_rows(missing, "missing", {"instrumentation_completeness": "unknown"}, retrieval="incomplete_explicit")
        duplicate_packet, _ = runner.encode_rows(duplicate, "duplicate", {"instrumentation_completeness": "unknown"})
        self.assertEqual(len(missing_packet["quality"]["unresolved_parent_references"]), 1)
        self.assertEqual(missing_packet["quality"]["structure_completeness"], "unknown")
        self.assertEqual(len(duplicate_packet["quality"]["conflicts"]), 1)
        self.assertEqual(len(duplicate_packet["records"]), 4)
        conflict = duplicate_packet["quality"]["conflicts"][0]
        self.assertEqual(set(conflict["nodes"]), {"child#1", "child#2"})
        self.assertEqual(len(conflict["evidence_ids"]), 2)

    def test_rebind_changes_exact_same_and_different_relations(self):
        fixture = json.loads((runner.ROOT / "experiments/semantic_encoding_v1/fixtures/T0.json").read_text())
        mutated = json.loads(json.dumps(fixture))
        next(row for row in mutated["records"] if row["span_id"] == "1ef5")["cmdb_id"] = "catalog#new"
        frozen = json.loads((runner.ROOT / "experiments/semantic_encoding_v1/fixtures/expected_s03_relations.json").read_text())
        original = frozen["T0"]
        changed = frozen["rebind"]
        packet, sidecar = runner.encode_rows(mutated["records"], "test-s03", {"kind": "synthetic_authored"}, duration_unit="ms")
        decoded = runner.decode_packet(packet)
        check = runner.validate_decoded(decoded, expected_rows=mutated["records"], expected_relations=changed,
                                         packet=packet, sidecar=sidecar, source_rows=mutated["records"])
        self.assertTrue(check["passed"])
        self.assertEqual(original["counts"], changed["counts"])
        self.assertEqual(original["parent_edges"], changed["parent_edges"])
        self.assertNotEqual(original["same_entity_pairs"], changed["same_entity_pairs"])
        self.assertNotEqual(original["different_entity_pairs"], changed["different_entity_pairs"])

    def test_timing_status_context_and_size_controls(self):
        cases = runner.authored_s05_cases()
        p3, _ = runner.encode_rows(cases["same_3"][0], "same3", {"instrumentation_completeness": "unknown"}, duration_unit="ms")
        p13, _ = runner.encode_rows(cases["same_13"][0], "same13", {"instrumentation_completeness": "unknown"}, duration_unit="ms")
        self.assertEqual(runner.derive_offsets(p13)[0]["offset"] - runner.derive_offsets(p3)[0]["offset"], 10)
        cross, _ = runner.encode_rows(cases["cross_3"][0], "cross3", {"instrumentation_completeness": "unknown"}, duration_unit="ms")
        self.assertEqual(runner.derive_offsets(cross)[0]["clock_qualification"], "cross_emitter_clock_alignment_unknown")
        unknown, _ = runner.encode_rows(cases["unknown_duration"][0], "unknown-duration", {"instrumentation_completeness": "unknown"}, duration_unit="unknown")
        self.assertIsNone(runner.derive_offsets(unknown)[0]["end_timestamp"])
        self.assertTrue(runner.context_time_check()["same_instant"])
        self.assertTrue(all(row["passed"] for row in runner.parse_context_names()))
        self.assertEqual(runner.parse_context_names()[-1]["actual"], None)
        for n in (1, 10, 100):
            normalized, symbolic, source = runner.s08_representations(n)
            self.assertEqual(runner.expand_symbolic(symbolic), source)
            self.assertEqual(normalized["records"], source)
            dictionary_schema = len(runner.compact({"schema": symbolic["schema"], "ops": symbolic["ops"], "entities": symbolic["entities"], "fields": symbolic["fields"]}))
            self.assertGreater(dictionary_schema, 0)

    def test_status_mapping_requires_matching_context_and_evidence(self):
        rows, mapping, verification = runner.authored_s06_cases()["mapped_error"]
        wrong_mapping = json.loads(json.dumps(mapping))
        packet, _ = runner.encode_rows(rows, "wrong-context", {"kind": "synthetic_authored", "producer_context": "other-producer"}, duration_unit="ms", status_mapping=wrong_mapping, request_verification=verification)
        decoded = runner.decode_packet(packet)
        self.assertEqual(runner.interpret_status(decoded)["spans"][0]["span_status_interpretation"], "unknown")

    def test_s09_freezes_six_slots_without_client(self):
        s06 = {case: runner.decode_packet(runner.encode_rows(rows, "s06-" + case, {"instrumentation_completeness": "unknown"}, duration_unit="ms", status_mapping=mapping, request_verification=verification)[0]) for case, (rows, mapping, verification) in runner.authored_s06_cases().items()}
        result = runner.s09_requests(s06)
        self.assertEqual(result["call_count_requested"], 6)
        self.assertEqual(len(result["calls"]), 6)
        if not result["executed"]:
            self.assertTrue(all(call["input_tokens"] is None for call in result["calls"]))

    def test_s09_preparation_uses_opaque_ids_and_rejects_free_text_claims(self):
        fixture = s09.load_s09_fixture()
        for case, representation in s09.build_schedule():
            payload, expected = s09.make_case(case, representation)
            payload_text = json.dumps(payload, sort_keys=True)
            self.assertNotIn(case, payload_text)
            self.assertNotIn("S06-", payload_text)
            self.assertEqual(expected, fixture["cases"][case]["expected"])
        expected = fixture["cases"]["unmapped_14"]["expected"]
        probe = dict(expected)
        probe["limitations"] = ["Business outcome unknown; backend target appears to be database."]
        result = s09.validate_response(json.dumps(probe), expected, {"ev-raw-a7"})
        self.assertFalse(result["entailment"])
        self.assertTrue(result["free_text_review"]["required"])
        self.assertFalse(s09.validate_response("[]", expected, set())["entailment"])


if __name__ == "__main__":
    unittest.main()
