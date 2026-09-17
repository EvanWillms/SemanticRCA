"""Resolve source locators within the supplied dataset boundary."""
from pathlib import Path


def source_path(dataset: Path, relative: str) -> Path:
    root = dataset.resolve()
    path = (root / relative).resolve()
    path.relative_to(root)
    return path
