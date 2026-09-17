"""Public boundary for semantic evidence and bounded RCA investigation."""

from .ingestion import from_semantic_traces
from .investigation import investigate

__all__ = ["from_semantic_traces", "investigate"]
