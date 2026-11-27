"""Half B, step B1: rejecting invalid input. Skipped while validate_input is still a stub.

Every case must raise ValueError (with a Spanish message), never another exception and never pass silently.
"""

import dataclasses
import unittest

import metro_escape as m
from tests.helpers import SAMPLE_INPUT, write_temp_input


VALID = m.parse_input(SAMPLE_INPUT)


def validation_done() -> bool:
    try:
        m.validate_input(VALID)
    except NotImplementedError:
        return False
    return True


SKIP_REASON = "validate_input is still a stub (half B, step B1)"


def with_mission(**changes) -> m.MetroInput:
    return dataclasses.replace(VALID, mission=dataclasses.replace(VALID.mission, **changes))


@unittest.skipUnless(validation_done(), SKIP_REASON)
class ValidateInputTests(unittest.TestCase):
    def assert_rejected(self, metro: m.MetroInput):
        with self.assertRaises(ValueError):
            m.validate_input(metro)

    def test_valid_sample_passes(self):
        m.validate_input(VALID)

    def test_tunnel_to_unknown_station(self):
        self.assert_rejected(dataclasses.replace(VALID, tunnels=VALID.tunnels + (m.Tunnel(1, 99, 3, "L1"),)))

    def test_tunnel_from_unknown_station(self):
        self.assert_rejected(dataclasses.replace(VALID, tunnels=VALID.tunnels + (m.Tunnel(99, 1, 3, "L1"),)))

    def test_unknown_origin(self):
        self.assert_rejected(with_mission(amelie_origin=99))

    def test_unknown_gate(self):
        self.assert_rejected(with_mission(pierre_gate=99))

    def test_both_gates_are_the_same_station(self):
        self.assert_rejected(with_mission(amelie_gate=VALID.mission.pierre_gate))

    def test_origin_is_own_gate(self):
        self.assert_rejected(with_mission(pierre_origin=VALID.mission.pierre_gate))

    def test_zero_travel_time(self):
        self.assert_rejected(dataclasses.replace(VALID, tunnels=VALID.tunnels + (m.Tunnel(1, 2, 0, "L1"),)))

    def test_negative_transfer_time(self):
        self.assert_rejected(dataclasses.replace(VALID, transfer_times={**VALID.transfer_times, 1: -1}))

    def test_window_start_not_before_end(self):
        bad = m.Modifier("TIEMPO_DOBLE", "L1", 30, 30)
        self.assert_rejected(dataclasses.replace(VALID, modifiers=(bad,)))

    def test_modifier_on_unused_line(self):
        bad = m.Modifier("SIN_TRANSBORDO", "L99", 0, None)
        self.assert_rejected(dataclasses.replace(VALID, modifiers=(bad,)))


@unittest.skipUnless(validation_done(), SKIP_REASON)
class MalformedFileTests(unittest.TestCase):
    def assert_file_rejected(self, text: str):
        path = write_temp_input(text)
        try:
            with self.assertRaises(ValueError) as caught:
                m.validate_input(m.parse_input(path))
        finally:
            path.unlink()
        self.assertNotIn("unpack", str(caught.exception), "use a Spanish message, not Python's default")

    def test_fewer_lines_than_the_counts_promise(self):
        self.assert_file_rejected("3 2\n1 1\n2 1\n3 1\n1 2 3 L1\n")

    def test_station_listed_twice(self):
        self.assert_file_rejected("2 1\n1 1\n1 2\n1 2 3 L1\n1 2 1 2\n")

    def test_modifier_with_only_one_minute(self):
        self.assert_file_rejected("3 2\n1 1\n2 1\n3 1\n1 2 3 L1\n2 3 3 L1\n1 3 2 3\nTIEMPO_DOBLE L1 5\n")


if __name__ == "__main__":
    unittest.main()
