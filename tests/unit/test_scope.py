from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import unittest

from rca.contracts import QueryRow
from rca.scope import interpret


UTC_PLUS_8 = timezone(timedelta(hours=8))


class ScopeInterpretationTests(unittest.TestCase):
    def test_interprets_public_component_reason_query(self) -> None:
        instruction = (
            "The cloud service system, Cloudbed-7, encountered two failures "
            "within the time range of June 15, 2025, from 09:00 to 09:30. "
            "Your task is to identify the root cause component and the root cause reason."
        )

        result = interpret(QueryRow(42, instruction, "task_6"))

        self.assertEqual(result.status, "interpreted")
        self.assertEqual(result.instruction, instruction)
        self.assertEqual(result.instruction_hash, hashlib.sha256(instruction.encode()).hexdigest())
        self.assertEqual(result.scope.deployment, "cloudbed-7")
        self.assertEqual(result.scope.window_start, datetime(2025, 6, 15, 9, tzinfo=UTC_PLUS_8))
        self.assertEqual(result.scope.window_end, datetime(2025, 6, 15, 9, 30, tzinfo=UTC_PLUS_8))
        self.assertEqual(result.scope.failure_count, 2)
        self.assertEqual(result.scope.requested_fields, ("component", "reason"))
        self.assertEqual(result.errors, ())

    def test_preserves_unicode_offsets_and_rolls_permitted_midnight_window(self) -> None:
        instruction = (
            "The cloud service system, cloudbed-1, experienced a failure within "
            "the time range of March 20, 2022, from 23:30 to 00:00. Please identify "
            "the root cause component. café"
        )

        result = interpret(QueryRow(0, instruction, "task_3"))

        self.assertEqual(result.status, "interpreted")
        self.assertEqual(result.scope.window_end, datetime(2022, 3, 21, tzinfo=UTC_PLUS_8))
        self.assertTrue(any(item.convention for item in result.support if item.field == "window_end"))
        deployment_support = next(item for item in result.support if item.field == "deployment")
        self.assertEqual(instruction[deployment_support.start : deployment_support.end], deployment_support.excerpt)

    def test_rejects_a_missing_count(self) -> None:
        result = interpret(
            QueryRow(
                1,
                "The system cloudbed-1 experienced failure within the time range "
                "of March 20, 2022, from 09:00 to 09:30. Please identify the root cause component.",
            )
        )

        self.assertEqual(result.status, "unsupported")
        self.assertIn("missing_failure_count", result.errors)
        self.assertIsNone(result.scope)

    def test_rejects_task_index_projection_mismatch(self) -> None:
        result = interpret(
            QueryRow(
                1,
                "The system cloudbed-1 experienced one failure within the time range "
                "of March 20, 2022, from 09:00 to 09:30. Please identify the root cause component.",
                "task_1",
            )
        )

        self.assertEqual(result.status, "unsupported")
        self.assertIn("task_index_mismatch", result.errors)


if __name__ == "__main__":
    unittest.main()
