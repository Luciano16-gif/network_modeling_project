"""Parsing input.txt and modifier windows. Done: these tests must keep passing."""

import unittest

import metro_escape as m
from tests.helpers import SAMPLE_INPUT, write_temp_input


class ParseInputTests(unittest.TestCase):
    def test_sample_input(self):
        metro = m.parse_input(SAMPLE_INPUT)
        self.assertEqual(len(metro.transfer_times), 15)
        self.assertEqual(len(metro.tunnels), 22)
        self.assertEqual(metro.transfer_times[2], 3)
        self.assertEqual(metro.tunnels[0], m.Tunnel(1, 2, 4, "L1"))
        self.assertEqual(metro.mission, m.Mission(pierre_origin=1, amelie_origin=12, pierre_gate=7, amelie_gate=8))
        self.assertEqual(
            metro.modifiers,
            (m.Modifier("SIN_TRANSBORDO", "L4", 10, 30), m.Modifier("TIEMPO_DOBLE", "L9", 0, None)),
        )

    def test_comments_and_blank_lines_are_skipped(self):
        path = write_temp_input("# header\n\n2 1\n  # indented comment\n1 2\n2 1\n1 2 3 L1\n\n1 2 2 1\n")
        try:
            metro = m.parse_input(path)
        finally:
            path.unlink()
        self.assertEqual(metro.transfer_times, {1: 2, 2: 1})
        self.assertEqual(metro.tunnels, (m.Tunnel(1, 2, 3, "L1"),))
        self.assertEqual(metro.modifiers, ())

    def test_unknown_modifier_kind(self):
        with self.assertRaises(ValueError):
            m.parse_modifier(["LINEA_ROTA", "L1"])


class ModifierWindowTests(unittest.TestCase):
    def test_window_includes_start_and_excludes_end(self):
        modifier = m.Modifier("TIEMPO_DOBLE", "L1", 10, 30)
        self.assertFalse(modifier.is_active(9))
        self.assertTrue(modifier.is_active(10))
        self.assertTrue(modifier.is_active(29))
        self.assertFalse(modifier.is_active(30))

    def test_no_window_means_whole_operation(self):
        modifier = m.parse_modifier(["SIN_TRANSBORDO", "L4"])
        self.assertEqual(modifier, m.Modifier("SIN_TRANSBORDO", "L4", 0, None))
        self.assertTrue(modifier.is_active(0))
        self.assertTrue(modifier.is_active(10_000))


if __name__ == "__main__":
    unittest.main()
