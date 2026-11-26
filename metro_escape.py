"""El Escape de los Coleccionistas en el Metro de París.

Reads the metro network and mission from input.txt and writes the escape plan to output.txt.
See docs/enunciado-proyecto.md for the assignment and docs/design.md for the design decisions.
"""

from dataclasses import dataclass
from pathlib import Path


INPUT_PATH = Path(__file__).with_name("input.txt")
OUTPUT_PATH = Path(__file__).with_name("output.txt")


# ---------------------------------------------------------------------------
# Data types: input
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Tunnel:
    origin: int
    destination: int
    minutes: int
    line: str


@dataclass(frozen=True)
class Mission:
    pierre_origin: int
    amelie_origin: int
    pierre_gate: int
    amelie_gate: int


@dataclass(frozen=True)
class Modifier:
    kind: str            # "SIN_TRANSBORDO" or "TIEMPO_DOBLE"
    line: str
    start: int           # first minute it applies (inclusive)
    end: int | None      # first minute it stops applying; None = whole operation

    def is_active(self, minute: int) -> bool:
        if self.end is None:
            return True
        return self.start <= minute < self.end


@dataclass(frozen=True)
class MetroInput:
    transfer_times: dict[int, int]   # station id -> transfer minutes
    tunnels: tuple[Tunnel, ...]
    mission: Mission
    modifiers: tuple[Modifier, ...]


# ---------------------------------------------------------------------------
# Data types: the escape plan (the search produces it, the report prints it)
# ---------------------------------------------------------------------------

STOP_EVENTS = ("origin", "ride", "transfer", "gate")


@dataclass(frozen=True)
class Stop:
    """One line of a traveler's route in the report."""

    minute: int
    station: int
    event: str           # one of STOP_EVENTS
    line: str | None     # line ridden or transferred to; None for "origin"


@dataclass(frozen=True)
class Route:
    stops: tuple[Stop, ...]   # in time order: first "origin", last "gate"

    @property
    def departure_minute(self) -> int:
        return self.stops[0].minute

    @property
    def arrival_minute(self) -> int:
        return self.stops[-1].minute


@dataclass(frozen=True)
class Plan:
    pierre: Route
    amelie: Route

    @property
    def total_minutes(self) -> int:
        return max(self.pierre.arrival_minute, self.amelie.arrival_minute)


# ---------------------------------------------------------------------------
# Parsing input.txt
# ---------------------------------------------------------------------------

MODIFIER_KINDS = ("SIN_TRANSBORDO", "TIEMPO_DOBLE")


def read_data_rows(path: str | Path) -> list[list[str]]:
    """Return the file's meaningful lines split into words, skipping blanks and # comments."""
    with open(path, encoding="utf-8") as file:
        stripped = (line.strip() for line in file)
        return [line.split() for line in stripped if line and not line.startswith("#")]


def parse_input(path: str | Path) -> MetroInput:
    rows = iter(read_data_rows(path))

    station_count, tunnel_count = (int(value) for value in next(rows))

    transfer_times = {}
    for _ in range(station_count):
        station, minutes = next(rows)
        transfer_times[int(station)] = int(minutes)

    tunnels = []
    for _ in range(tunnel_count):
        origin, destination, minutes, line = next(rows)
        tunnels.append(Tunnel(int(origin), int(destination), int(minutes), line))

    pierre_origin, amelie_origin, pierre_gate, amelie_gate = (int(value) for value in next(rows))
    mission = Mission(
        pierre_origin=pierre_origin,
        amelie_origin=amelie_origin,
        pierre_gate=pierre_gate,
        amelie_gate=amelie_gate,
    )

    modifiers = [parse_modifier(row) for row in rows]   # whatever is left

    return MetroInput(transfer_times, tuple(tunnels), mission, tuple(modifiers))


def parse_modifier(row: list[str]) -> Modifier:
    kind, line, *window = row
    if kind not in MODIFIER_KINDS:
        raise ValueError(f"Modificador desconocido: {kind}")
    if not window:
        return Modifier(kind, line, start=0, end=None)
    start, end = (int(value) for value in window)
    return Modifier(kind, line, start, end)


def validate_input(metro: MetroInput) -> None:
    """Raise ValueError, with a Spanish message, if the input breaks a rule of the format.

    TODO (half B): not implemented yet; see docs/roadmap.md for the checks it must make.
    """


# ---------------------------------------------------------------------------
# Graph: adjacency list
# ---------------------------------------------------------------------------

Graph = dict[int, list[Tunnel]]   # station id -> tunnels leaving that station


def build_graph(metro: MetroInput) -> Graph:
    """Store the metro as an adjacency list (see docs/design.md, section 1).

    TODO (half A): not implemented yet; see docs/roadmap.md.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Search: joint breadth-first search over both travelers
# ---------------------------------------------------------------------------

def find_plan(metro: MetroInput, graph: Graph) -> Plan | None:
    """Return the fastest collision-free plan, or None if no plan exists (see docs/design.md, sections 2-3).

    TODO (half A): not implemented yet; see docs/roadmap.md.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Report: output.txt
# ---------------------------------------------------------------------------

def format_report(plan: Plan | None) -> str:
    """Return the Spanish report in the exact format of the spec's output.txt example.

    TODO (half B): not implemented yet; see docs/roadmap.md.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    metro = parse_input(INPUT_PATH)
    validate_input(metro)
    graph = build_graph(metro)
    plan = find_plan(metro, graph)
    report = format_report(plan)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write(report)


if __name__ == "__main__":
    main()
