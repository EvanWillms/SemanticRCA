"""Durable, atomic output checkpoints for the empty-output harness."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .contracts import QueryRow, Solution


class OutputWriteError(RuntimeError):
    """Raised when a case cannot be persisted as a complete checkpoint."""


def _model_usage(usage: Mapping[str, Any]) -> dict[str, Any]:
    return {str(model): value for model, value in usage.items() if isinstance(value, Mapping)}


def _usage_record(row_id: int, wall_s: float, solution: Solution) -> dict[str, Any]:
    models = _model_usage(solution.usage)
    calls = 0
    prompt_tokens = 0
    completion_tokens = 0
    for counters in models.values():
        if not isinstance(counters, Mapping):
            continue
        calls += int(counters.get("calls", 0) or 0)
        prompt_tokens += int(counters.get("prompt_tokens", 0) or 0)
        completion_tokens += int(counters.get("completion_tokens", 0) or 0)
    return {
        "row_id": row_id,
        "wall_s": max(0.0, float(wall_s)),
        "models": models,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "calls": calls,
    }


class OutputWriter:
    """Write evidence and usage before publishing each CSV checkpoint."""

    def __init__(
        self,
        out_dir: Path,
    ) -> None:
        self.out_dir = Path(out_dir)
        self.predictions_path = self.out_dir / "predictions.csv"
        self.usage_path = self.out_dir / "usage.jsonl"
        self.evidence_dir = self.out_dir / "evidence"
        self._published: list[tuple[int, str]] = []
        self._initialized = False

    def initialize(self) -> None:
        """Create an empty artifact set and an atomic header-only CSV."""

        if self._initialized:
            return
        try:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            with self.usage_path.open("w", encoding="utf-8", newline=""):
                pass
            self._atomic_write_predictions(())
        except OutputWriteError:
            raise
        except (OSError, csv.Error) as exc:
            raise OutputWriteError("could not initialize output artifacts") from exc
        self._initialized = True

    def _atomic_write_predictions(self, rows: Sequence[tuple[int, str]]) -> None:
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=self.out_dir,
                prefix=".predictions-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = handle.name
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(("row_id", "prediction"))
                writer.writerows(rows)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.predictions_path)
            temporary_path = None
        except (OSError, csv.Error) as exc:
            raise OutputWriteError("could not publish predictions checkpoint") from exc
        finally:
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass

    def _append_usage(self, record: Mapping[str, Any]) -> int:
        try:
            payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise OutputWriteError("could not serialize usage checkpoint") from exc
        try:
            with self.usage_path.open("a", encoding="utf-8", newline="") as handle:
                offset = handle.tell()
                handle.write(payload)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
                return offset
        except OSError as exc:
            raise OutputWriteError("could not persist usage checkpoint") from exc

    def _rollback_usage(self, offset: int) -> None:
        try:
            with self.usage_path.open("r+b") as handle:
                handle.truncate(offset)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError:
            pass

    def write_case(self, row: QueryRow, solution: Solution, wall_s: float) -> None:
        """Persist one case, retaining the last complete CSV on failure."""

        if not self._initialized:
            raise OutputWriteError("output writer is not initialized")
        evidence_path = self.evidence_dir / f"{row.row_id}.md"
        if evidence_path.exists():
            raise OutputWriteError("case evidence already exists")
        usage_offset: int | None = None
        evidence_created = False
        try:
            evidence_path.write_text(solution.evidence, encoding="utf-8", newline="")
            evidence_created = True
            usage_offset = self._append_usage(_usage_record(row.row_id, wall_s, solution))
            self._atomic_write_predictions((*self._published, (row.row_id, solution.prediction)))
        except Exception as exc:
            if usage_offset is not None:
                self._rollback_usage(usage_offset)
            if evidence_created:
                try:
                    evidence_path.unlink()
                except OSError:
                    pass
            if isinstance(exc, OutputWriteError):
                raise
            raise OutputWriteError("could not persist case checkpoint") from exc
        self._published.append((row.row_id, solution.prediction))
