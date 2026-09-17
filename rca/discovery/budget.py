"""Monotonic analysis allocations that reserve time to persist case results."""
from dataclasses import dataclass
import time
from collections.abc import Callable


class BudgetExceeded(RuntimeError):
    """Analysis must stop and let the writer finalize the current case."""


@dataclass(frozen=True)
class CaseBudget:
    deadline: float
    clock: Callable[[], float]

    def check(self) -> None:
        if self.clock() >= self.deadline:
            raise BudgetExceeded('analysis_time_budget_exhausted')


class RunBudget:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self.clock = clock
        self.started = clock()
        self.deadline = self.started + 1180

    def allocate(self, remaining_cases: int) -> CaseBudget:
        now = self.clock()
        available = max(0.0, self.deadline - now - 20 - remaining_cases * 5)
        return CaseBudget(now + min(575, available / remaining_cases), self.clock)
