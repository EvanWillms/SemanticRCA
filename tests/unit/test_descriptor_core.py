from __future__ import annotations

from dataclasses import replace
import unittest

from rca.baselining.contracts import (
    BaselineStatistics,
    CenterStability,
    ChildOccurrence,
    FrozenBaseline,
    Measurement,
    Observation,
    ObservationIdentity,
    StructuralPattern,
    StructuralPopulation,
    QueryAssignment,
    SupportAssessment,
)
from rca.comparisons import ComparisonDefinition, describe, review_view, summarize_occurrences, validate_descriptor


def _fixture(value: float, children: tuple[ChildOccurrence, ...] = ()):
    observation = Observation(
        ObservationIdentity("snapshot-1", "demo", "trace-1", f"span-{value}"),
        "frontend.request", "http", "frontend-0", 1000.0, 1000.0 + value,
        Measurement.from_value(value, raw_unit="ms"), children=children,
    )
    baseline = FrozenBaseline(
        "baseline-1", "cohort-1", "set-1", ("frontend.request", "http", ()), "members-1", (),
        BaselineStatistics(20, 10.0, 10.0, 10.0, 0.0),
        SupportAssessment("supported", 20, 3, 3, 10, 0.5),
        CenterStability("fails_screen"),
    )
    pattern = StructuralPattern("pattern-1", ("frontend.request", "http"), (("db", "sql", 1),), (), 20, 20, 1.0)
    population = StructuralPopulation("population-1", "set-1", ("frontend.request", "http"), known_structure_count=20, patterns=(pattern,))
    assignment = QueryAssignment(
        f"occ-{value}", observation.observation_id, "set-1", 0, baseline, population,
        "qualified", duration_comparison_eligible=True, observation=observation,
    )
    return observation, assignment


class DescriptorCoreTests(unittest.TestCase):
    def test_signed_excess_preserves_positive_negative_and_zero(self):
        positive, positive_a = _fixture(12.0)
        negative, negative_a = _fixture(8.0)
        equal, equal_a = _fixture(10.0)
        self.assertEqual(describe(positive, positive_a).duration.signed_excess.value, 2.0)
        self.assertEqual(describe(negative, negative_a).duration.signed_excess.value, -2.0)
        equal_d = describe(equal, equal_a)
        self.assertEqual(equal_d.duration.signed_excess.value, 0.0)
        self.assertEqual(equal_d.duration.ordering.value, "equal_to_median")

    def test_optional_diagnostics_distinguish_not_requested_and_undefined(self):
        observation, assignment = _fixture(12.0)
        default = describe(observation, assignment)
        self.assertEqual(default.duration.ratio.status, "not_requested")
        diagnostics = describe(observation, assignment, definition=ComparisonDefinition(diagnostics=("ratio", "mad")))
        self.assertEqual(diagnostics.duration.ratio.value, 1.2)
        self.assertEqual(diagnostics.duration.mad_departure.status, "undefined")

    def test_c2_multiplicity_delta_and_unknown_structure_are_separate(self):
        observation, assignment = _fixture(12.0, (ChildOccurrence("db", "sql", 2),))
        descriptor = describe(observation, assignment)
        pattern = descriptor.structure.pattern_differences[0]
        self.assertEqual(pattern.additions['["db","sql"]'], 1)
        unknown = replace(observation, structure_state="unknown", children=())
        unknown_descriptor = describe(unknown, replace(assignment, observation=unknown))
        self.assertEqual(unknown_descriptor.structure.query_state, "unknown")
        self.assertEqual(unknown_descriptor.structure.absent_from_reference.status, "unavailable")

    def test_validation_is_arithmetic_only_until_evidence_graph_is_available(self):
        observation, assignment = _fixture(12.0)
        descriptor = describe(observation, assignment)
        result = validate_descriptor(descriptor)
        self.assertEqual(result.status, "unchecked")
        with self.assertRaises(ValueError):
            review_view([descriptor], "set-1", 0)
        trusted = replace(descriptor, validation_status="valid")
        view = review_view([trusted], "set-1", 0)
        self.assertEqual(view.descriptor_ids, (trusted.descriptor_id,))

    def test_coverage_keeps_occurrences_and_unique_observations_separate(self):
        observation, assignment = _fixture(12.0)
        first = describe(observation, assignment)
        second = describe(observation, replace(assignment, occurrence_id="occ-second", slice_index=1))
        coverage = summarize_occurrences([first, second])
        self.assertEqual(coverage.occurrence_count, 2)
        self.assertEqual(coverage.unique_observation_count, 1)
        self.assertEqual(coverage.repeated_observation_count, 1)


if __name__ == "__main__":
    unittest.main()
