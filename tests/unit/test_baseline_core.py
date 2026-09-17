"""Independent tests for the pure qualified-baseline kernels."""

from __future__ import annotations

import unittest

from rca.baselining.contracts import (
    BaselinePolicy,
    Measurement,
    Observation,
    ObservationBatch,
    ObservationIdentity,
    RetrievalReceipt,
    SourceSnapshot,
)
from rca.baselining.policy import assign_queries, freeze_baselines
from rca.baselining.statistics import assess_support, exact_block_bootstrap, quantile


ANCHOR = 1_700_000_000_000


def observation(
    name: str,
    start: float,
    duration: float,
    *,
    operation: str = "GET /",
    children: tuple[tuple[str, str, int], ...] = (("fetch", "rpc", 1),),
    structure_state: str = "known",
    replica: str = "frontend-0",
    end: float | None = None,
) -> Observation:
    return Observation(
        identity=ObservationIdentity("fixture", "deployment-a", name, f"root-{name}"),
        root_operation=operation,
        root_type="http",
        replica=replica,
        start_ms=start,
        end_ms=start + duration if end is None else end,
        measurement=Measurement.from_value(duration),
        children=tuple(
            __import__("rca.baselining.contracts", fromlist=["ChildOccurrence"]).ChildOccurrence(*child)
            for child in children
        ),
        structure_state=structure_state,
    )


class StatisticsTests(unittest.TestCase):
    def test_support_rules_are_independent_and_boundaries_are_exact(self) -> None:
        starts = [ANCHOR - 299_000 + index * 60_000 for index in range(20)]
        self.assertAlmostEqual(quantile([0, 10, 20, 30], 0.05), 1.5)
        self.assertEqual(assess_support(starts).status, "supported")
        self.assertEqual(assess_support(starts[:19]).reasons, ("minimum_count",))
        self.assertIn("occupied_minutes", assess_support(starts[:20:10]).reasons)

    def test_exact_bootstrap_keeps_failed_empty_draws_and_zero_center(self) -> None:
        result = exact_block_bootstrap({0: (), 1: (0.0,)}, replicate_count=200, seed=42)
        self.assertEqual(result.replicate_count, 200)
        self.assertGreater(result.failed_replicates, 0)
        self.assertEqual(result.state, "not_applicable_zero_center")
        self.assertFalse(result.relative_width_available)


class BaselinePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = SourceSnapshot("fixture", "deployment-a")

    def test_freezes_reference_and_assigns_queries_without_mutating_catalog(self) -> None:
        refs = tuple(
            observation(f"ref-{index}", ANCHOR - 299_000 + index * 12_000, 10)
            for index in range(20)
        )
        boundary = observation("at-anchor", ANCHOR, 10)
        query = observation("query", ANCHOR + 1_000, 12)
        unknown = observation("new", ANCHOR + 301_000, 8, operation="POST /new")
        batch = ObservationBatch(
            refs + (boundary, query, unknown),
            RetrievalReceipt(selected_count=23, resolved_count=23, status="complete"),
        )
        frozen = freeze_baselines(batch, self.snapshot, ANCHOR)
        self.assertEqual(len(frozen.baselines), 1)
        self.assertEqual(frozen.baselines[0].member_ids, tuple(item.observation_id for item in refs))
        assignments = assign_queries(batch, frozen)
        self.assertEqual(len(assignments.assignments), 3)
        self.assertEqual(assignments.assignments[0].baseline.median, 10.0)
        self.assertTrue(assignments.assignments[0].duration_comparison_eligible)
        self.assertEqual(assignments.assignments[2].baseline.reasons, ("missing_context",))
        self.assertEqual(frozen.set_id, freeze_baselines(batch, self.snapshot, ANCHOR).set_id)

    def test_end_at_anchor_is_excluded_and_incomplete_receipt_cannot_support(self) -> None:
        refs = tuple(
            observation(f"ref-{index}", ANCHOR - 299_000 + index * 12_000, 10, end=ANCHOR if index == 0 else None)
            for index in range(20)
        )
        # Build a full set of valid reference endpoints except for the explicit
        # boundary record; unknown endpoints are also excluded from membership.
        refs = tuple(item if item.end_ms is not None else observation(item.identity.trace_id, item.start_ms, 10) for item in refs)
        partial = ObservationBatch(refs, RetrievalReceipt(selected_count=20, resolved_count=20, status="partial", reason="budget"))
        frozen = freeze_baselines(partial, self.snapshot, ANCHOR)
        self.assertIn("partial_selection", frozen.baselines[0].support.reasons)
        self.assertEqual(frozen.baselines[0].support.status, "unavailable")


if __name__ == "__main__":
    unittest.main()
