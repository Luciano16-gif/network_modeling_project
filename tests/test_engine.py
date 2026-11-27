"""Half A (graph and search). Done and verified: these tests must keep passing."""

import random
import unittest

import metro_escape as m
from tests.helpers import SAMPLE_INPUT
from tests import laws


class GraphTests(unittest.TestCase):
    def test_sample_adjacency_list(self):
        graph = m.build_graph(m.parse_input(SAMPLE_INPUT))
        self.assertEqual(len(graph), 15)
        self.assertEqual(sum(len(exits) for exits in graph.values()), 22)
        self.assertEqual([(t.destination, t.line) for t in graph[2]], [(3, "L1"), (5, "L4"), (1, "L1")])


class SearchTests(unittest.TestCase):
    def test_sample_plan(self):
        metro = m.parse_input(SAMPLE_INPUT)
        plan = m.find_plan(metro, m.build_graph(metro))
        self.assertIsNotNone(plan)
        laws.check_plan(metro, plan)
        self.assertEqual(plan.total_minutes, 22)

    def test_submitted_input_txt_has_a_lawful_plan(self):
        """No exact numbers here: input.txt is meant to be redesigned (roadmap step B3)."""
        metro = m.parse_input(m.INPUT_PATH)
        plan = m.find_plan(metro, m.build_graph(metro))
        self.assertIsNotNone(plan, "the submitted input.txt should have a plan to show")
        laws.check_plan(metro, plan)

    def test_same_origin_has_no_plan(self):
        metro = m.MetroInput(
            {1: 1, 2: 1, 3: 1},
            (m.Tunnel(1, 2, 1, "L1"), m.Tunnel(1, 3, 1, "L1")),
            m.Mission(1, 1, 2, 3),
            (),
        )
        self.assertIsNone(m.find_plan(metro, m.build_graph(metro)))

    def test_random_networks_follow_every_rule_and_are_optimal(self):
        rng = random.Random(2627)
        limit = 18
        for _ in range(150):
            metro = laws.random_metro(rng)
            plan = m.find_plan(metro, m.build_graph(metro))
            with self.subTest(metro=metro):
                if plan is None:
                    self.assertIsNone(laws.brute_force_total(metro, limit))
                    continue
                laws.check_plan(metro, plan)
                self.assertEqual(laws.brute_force_total(metro, plan.total_minutes), plan.total_minutes)


if __name__ == "__main__":
    unittest.main()
