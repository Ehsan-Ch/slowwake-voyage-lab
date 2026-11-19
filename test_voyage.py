import itertools
import unittest
from build import ROOT, render
from voyage import Leg, ROUTES, best, candidate_plans, experiment, leg_option


class VoyageTests(unittest.TestCase):
    def test_dynamic_program_matches_exhaustive_search(self):
        route = (Leg(20, 1, 1), Leg(40, -2, 1.4), Leg(25, 0, .9))
        speeds = (9, 12, 16)
        all_plans = []
        for choices in itertools.product(speeds, repeat=len(route)):
            legs = [leg_option(leg, speed) for leg, speed in zip(route, choices)]
            all_plans.append((sum(o.minutes for o in legs), sum(o.fuel_grams for o in legs), choices))
        for deadline in (210, 400, 450, 500, 700):
            self.assertEqual(best(candidate_plans(route, speeds), deadline), best(all_plans, deadline))

    def test_currents_change_ground_speed_and_fuel_total(self):
        following = leg_option(Leg(40, 2, 1), 14)
        opposing = leg_option(Leg(40, -2, 1), 14)
        self.assertLess(following.minutes, opposing.minutes)
        self.assertLess(following.fuel_grams, opposing.fuel_grams)
        self.assertEqual(following.minutes, 150)

    def test_deadline_and_comparator(self):
        for profile in experiment().values():
            for deadline, comparison in profile["plans"].items():
                for plan in comparison.values():
                    if plan:
                        self.assertLessEqual(plan["minutes"], int(deadline) * 60)
                        self.assertEqual(plan["minutes"], sum(leg["minutes"] for leg in plan["legs"]))
                        self.assertAlmostEqual(plan["fuel"], sum(leg["fuel"] for leg in plan["legs"]))
                if comparison["constant"]:
                    self.assertLessEqual(comparison["adaptive"]["fuel"], comparison["constant"]["fuel"])

    def test_infeasible_deadline(self):
        route = ROUTES["headwind"]
        candidates = candidate_plans(route)
        self.assertIsNone(best(candidates, 60))

    def test_report_reproduces(self):
        self.assertEqual((ROOT / "index.html").read_text(encoding="utf-8"), render())
