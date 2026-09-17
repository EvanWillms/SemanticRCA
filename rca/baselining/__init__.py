"""Reusable qualified frontend baseline domain API.

Source access is explicit; the freeze and assignment kernels perform no I/O.
The legacy discovery profile does not select this policy automatically.
"""
from .contracts import (
    AssignmentBatch, BaselinePolicy, BaselineSet, ChildOccurrence,
    FrozenBaseline, Measurement, MissingContext, Observation, ObservationBatch,
    ObservationIdentity, QueryAssignment, RetrievalReceipt, SourceLocator,
    SourceSnapshot, StructuralPopulation,
)
from .policy import assign_queries, freeze_baselines
from .observations import collect_requests
from rca.telemetry.trace_index import PreparedTraceView, prepare_sources

__all__ = [
    "AssignmentBatch", "BaselinePolicy", "BaselineSet", "ChildOccurrence",
    "FrozenBaseline", "Measurement", "MissingContext", "Observation",
    "ObservationBatch", "ObservationIdentity", "PreparedTraceView",
    "QueryAssignment", "RetrievalReceipt", "SourceLocator", "SourceSnapshot",
    "StructuralPopulation", "assign_queries", "collect_requests",
    "freeze_baselines", "prepare_sources",
]
