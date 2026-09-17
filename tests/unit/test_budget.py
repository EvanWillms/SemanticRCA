"""Budget allocation at the public run/case boundary."""
import unittest
from rca.discovery.budget import RunBudget, BudgetExceeded


class BudgetTests(unittest.TestCase):
    def test_twenty_cases_keep_fair_analysis_time_and_finalization_reserve(self):
        now = [0.0]
        run = RunBudget(clock=lambda: now[0])
        first = run.allocate(20)
        now[0] = 52.0
        first.check()
        now[0] = 53.0
        with self.assertRaises(BudgetExceeded):
            first.check()
        second = run.allocate(19)
        second.check()
        now[0] = 1180.0
        with self.assertRaises(BudgetExceeded):
            second.check()
