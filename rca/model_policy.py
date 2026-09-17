"""Allowed inference models from the official Track 1 docs/models.md.

Source: mantisgrid-hackathon/hackathon-2026-official/track-1/docs/models.md
Synced 2026-09-17. Keep an explicit snapshot so the submission is standalone.
"""

ALLOWED_MODELS = frozenset({
    "zai-org/GLM-4.7-Flash",
    "zai-org/GLM-5.3-Flash",
    "zai-org/GLM-4.6",
    "zai-org/GLM-4.7",
    "zai-org/GLM-5",
    "zai-org/GLM-5.1",
    "zai-org/GLM-5.2",
})


def require_allowed_model(model: str) -> str:
    """Reject unsupported IDs before any provider request or fallback occurs."""
    if model not in ALLOWED_MODELS:
        raise ValueError("Model is not listed in official Track 1 docs/models.md")
    return model
