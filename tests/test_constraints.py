"""Hard constraints of the assignment and of the Plan contract. These must always pass."""

import ast
import unittest
from pathlib import Path

import metro_escape as m


ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "metro_escape.py"


class AssignmentConstraintTests(unittest.TestCase):
    def test_no_imports(self):
        """The spec forbids third-party libraries; to stay clear of any doubt, the program imports nothing at all."""
        tree = ast.parse(PROGRAM.read_text(encoding="utf-8"))
        imports = [node.lineno for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual(imports, [], "metro_escape.py must not import anything (lines listed)")

    def test_single_program_file(self):
        self.assertEqual([path.name for path in ROOT.glob("*.py")], ["metro_escape.py"])

    def test_pipeline_functions_exist(self):
        for name in ("parse_input", "validate_input", "build_graph", "find_plan", "format_report", "main"):
            self.assertTrue(callable(getattr(m, name, None)), name)


class PlanContractTests(unittest.TestCase):
    """The contract between the search and the report (docs/roadmap.md). Change it only with the team."""

    def test_fields(self):
        stop = m.Stop(0, 1, "origin", None)
        route = m.Route((stop,))
        self.assertEqual(tuple(vars(stop)), ("minute", "station", "event", "line"))
        self.assertEqual(tuple(vars(route)), ("stops",))
        self.assertEqual(tuple(vars(m.Plan(route, route))), ("pierre", "amelie"))
        self.assertEqual(m.STOP_EVENTS, ("origin", "ride", "transfer", "gate"))

    def test_derived_minutes(self):
        route = m.Route((m.Stop(6, 12, "origin", None), m.Stop(11, 14, "ride", "L9"), m.Stop(28, 8, "gate", "L9")))
        self.assertEqual((route.departure_minute, route.arrival_minute), (6, 28))
        self.assertEqual(m.Plan(route, route).total_minutes, 28)

    def test_contract_types_are_immutable(self):
        stop = m.Stop(0, 1, "origin", None)
        with self.assertRaises(AttributeError):
            stop.minute = 5


if __name__ == "__main__":
    unittest.main()
