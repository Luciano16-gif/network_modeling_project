"""El Escape de los Coleccionistas en el Metro de París.

Reads the metro network and mission from input.txt and writes the escape plan to output.txt.
See docs/enunciado-proyecto.md for the assignment and docs/design.md for the design decisions.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data types
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
# Parsing input.txt
# ---------------------------------------------------------------------------

MODIFIER_KINDS = ("SIN_TRANSBORDO", "TIEMPO_DOBLE")


def read_data_rows(path: str) -> list[list[str]]:
    """Return the file's meaningful lines split into words, skipping blanks and # comments."""
    with open(path, encoding="utf-8") as file:
        stripped = (line.strip() for line in file)
        return [line.split() for line in stripped if line and not line.startswith("#")]


def parse_input(path: str) -> MetroInput:
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

    mission = Mission(*(int(value) for value in next(rows)))

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
