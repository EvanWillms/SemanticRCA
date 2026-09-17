"""Reference-relative comparative descriptor domain library."""

from .contracts import (
    Availability,
    FieldAvailability,
    FieldOutcome,
    ComparativeDescriptor,
    ComparisonDefinition,
    DescriptorCoverage,
    DescriptorQualification,
    DurationComparison,
    EvidenceReference,
    FieldResult,
    PatternDifference,
    ReviewView,
    StructuralComparison,
    ValidationResult,
)
from .describe import describe
from .evidence import validate_descriptor
from .views import review_view, summarize, summarize_occurrences
from .artifacts import DescriptorManifest, descriptor_from_dict, load_bundle, read_bundle, write_bundle

__all__ = [
    "Availability", "FieldAvailability", "FieldOutcome", "ComparativeDescriptor", "ComparisonDefinition",
    "DescriptorCoverage", "DescriptorQualification", "DurationComparison",
    "EvidenceReference", "FieldResult", "PatternDifference", "ReviewView",
    "StructuralComparison", "ValidationResult", "describe", "review_view",
    "summarize", "summarize_occurrences", "validate_descriptor",
    "DescriptorManifest", "descriptor_from_dict", "load_bundle", "read_bundle", "write_bundle",
]
