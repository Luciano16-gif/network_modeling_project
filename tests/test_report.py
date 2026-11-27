"""Half B, step B2: format_report. Skipped while it is still a stub; the target is fixed here.

The expected text is the spec's output.txt example (docs/enunciado-proyecto.md, section 4), with the
"..." lines left out. Do not edit the expected text to make a test pass: fix format_report instead.
"""

import unittest

import metro_escape as m
from tests.helpers import SAMPLE_INPUT


def is_implemented(function, *args) -> bool:
    try:
        function(*args)
    except NotImplementedError:
        return False
    except Exception:
        return True
    return True


REPORT_DONE = is_implemented(m.format_report, None)
SKIP_REASON = "format_report is still a stub (half B, step B2)"


def spec_example_plan() -> m.Plan:
    """The spec's output.txt example as a Plan, built by hand."""
    pierre = m.Route((
        m.Stop(0, 1, "origin", None),
        m.Stop(4, 2, "ride", "L1"),
        m.Stop(7, 2, "transfer", "L4"),
        m.Stop(15, 5, "ride", "L4"),
        m.Stop(28, 7, "gate", "L4"),
    ))
    amelie = m.Route((
        m.Stop(6, 12, "origin", None),
        m.Stop(11, 14, "ride", "L9"),
        m.Stop(28, 8, "gate", "L9"),
    ))
    return m.Plan(pierre, amelie)


SPEC_EXAMPLE_REPORT = """\
=== PLAN DE ESCAPE CONFIGURADO ===
Tiempo Total de la Operación: 28 minutos

[PROGRAMACIÓN DE SALIDAS]
* Pierre arranca en el minuto: 0
* Amélie arranca en el minuto: 6 (Debe esperar 6 minutos en su estación de origen)

[RUTA DE PIERRE (Tiempo total de viaje: 28 min)]
Minuto 0: Estación 1 (Origen)
Minuto 4: Estación 2 (Viaje L1)
Minuto 7: Estación 2 (Termina Transbordo a L4)
Minuto 15: Estación 5 (Viaje L4)
Minuto 28: Estación 7 (Destino Compuerta D1)

[RUTA DE AMÉLIE (Tiempo total de viaje: 22 min)]
Minuto 6: Estación 12 (Origen - Inicia Movimiento)
Minuto 11: Estación 14 (Viaje L9)
Minuto 28: Estación 8 (Destino Compuerta D2)

Resultado de Sincronización: ÉXITO. Llegada simultánea en el minuto 28.
"""


@unittest.skipUnless(REPORT_DONE, SKIP_REASON)
class FormatReportTests(unittest.TestCase):
    def test_spec_example(self):
        self.assertEqual(m.format_report(spec_example_plan()).rstrip("\n"), SPEC_EXAMPLE_REPORT.rstrip("\n"))

    def test_pierre_waits_instead(self):
        plan = spec_example_plan()
        swapped = m.Plan(
            pierre=m.Route((m.Stop(3, 1, "origin", None), m.Stop(28, 7, "gate", "L4"))),
            amelie=m.Route((m.Stop(0, 12, "origin", None), m.Stop(28, 8, "gate", "L9"))),
        )
        lines = m.format_report(swapped).splitlines()
        self.assertIn("* Pierre arranca en el minuto: 3 (Debe esperar 3 minutos en su estación de origen)", lines)
        self.assertIn("* Amélie arranca en el minuto: 0", lines)
        self.assertIn("Minuto 3: Estación 1 (Origen - Inicia Movimiento)", lines)
        self.assertIn("Minuto 0: Estación 12 (Origen)", lines)
        self.assertIn("[RUTA DE PIERRE (Tiempo total de viaje: 25 min)]", lines)
        self.assertEqual(plan.total_minutes, 28)

    def test_no_plan_is_a_short_spanish_message(self):
        report = m.format_report(None)
        self.assertIsInstance(report, str)
        self.assertTrue(report.strip())
        self.assertNotIn("ÉXITO", report)

    def test_real_plan_for_sample_input(self):
        metro = m.parse_input(SAMPLE_INPUT)
        report = m.format_report(m.find_plan(metro, m.build_graph(metro)))
        self.assertIn("Resultado de Sincronización: ÉXITO. Llegada simultánea en el minuto 22.", report)


if __name__ == "__main__":
    unittest.main()
