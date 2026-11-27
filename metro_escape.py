"""El Escape de los Coleccionistas en el Metro de París.

Reads the metro network and mission from input.txt and writes the escape plan to output.txt.
See docs/enunciado-proyecto.md for the assignment and docs/design.md for the design decisions.
"""

from collections import deque
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
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Graph: adjacency list
# ---------------------------------------------------------------------------

Graph = dict[int, list[Tunnel]]   # station id -> tunnels leaving that station


def build_graph(metro: MetroInput) -> Graph:
    """Store the metro as an adjacency list (see docs/design.md, section 1)."""
    graph = {station: [] for station in metro.transfer_times}
    for tunnel in metro.tunnels:
        graph[tunnel.origin].append(tunnel)
    return graph


# ---------------------------------------------------------------------------
# Search: where one traveler can be at a given minute
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Waiting:
    """At their origin, not departed yet."""

    station: int


@dataclass(frozen=True)
class AtStation:
    """At a station on a line, about to leave it (nobody waits mid-route)."""

    station: int
    line: str
    may_transfer: bool   # False right after a transfer: changing back and forth would be waiting in disguise


@dataclass(frozen=True)
class Transferring:
    """Changing to another line inside a station."""

    station: int
    line: str            # the line being transferred to
    minutes_left: int


@dataclass(frozen=True)
class Riding:
    """Inside a tunnel, between two stations."""

    tunnel: Tunnel
    minutes_left: int


@dataclass(frozen=True)
class Arrived:
    """At their own bunker gate. The route is over."""

    station: int


TravelerState = Waiting | AtStation | Transferring | Riding | Arrived


def station_of(state: TravelerState) -> int | None:
    """Return the station the traveler occupies, or None while inside a tunnel."""
    if isinstance(state, Riding):
        return None
    return state.station


# ---------------------------------------------------------------------------
# Search: line modifiers (the only place that reads them)
# ---------------------------------------------------------------------------

def transfer_allowed(modifiers: tuple[Modifier, ...], from_line: str, to_line: str, minute: int) -> bool:
    """Whether a transfer between the two lines may start at this minute (SIN_TRANSBORDO)."""
    return not any(
        modifier.kind == "SIN_TRANSBORDO"
        and modifier.line in (from_line, to_line)
        and modifier.is_active(minute)
        for modifier in modifiers
    )


def tunnel_minutes(modifiers: tuple[Modifier, ...], tunnel: Tunnel, minute: int) -> int:
    """How long the tunnel takes when entered at this minute (TIEMPO_DOBLE doubles it)."""
    doubled = any(
        modifier.kind == "TIEMPO_DOBLE"
        and modifier.line == tunnel.line
        and modifier.is_active(minute)
        for modifier in modifiers
    )
    return tunnel.minutes * 2 if doubled else tunnel.minutes


def last_modifier_minute(modifiers: tuple[Modifier, ...]) -> int:
    """From this minute on no modifier window opens or closes, so time no longer changes the rules."""
    return max((modifier.end for modifier in modifiers if modifier.end is not None), default=0)


# ---------------------------------------------------------------------------
# Search: what one traveler can do during one minute
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Move:
    """One traveler's next minute: where they end up, the tunnel they use, and the report lines it produces."""

    state: TravelerState
    tunnel: Tunnel | None = None
    stops: tuple[Stop, ...] = ()


def traveler_moves(
    state: TravelerState, minute: int, gate: int, metro: MetroInput, graph: Graph
) -> list[Move]:
    """Return every move one traveler can make during the minute that starts at `minute`."""
    if isinstance(state, Waiting):
        return origin_moves(state, minute, gate, metro, graph)
    if isinstance(state, AtStation):
        return station_moves(state, minute, gate, metro, graph)
    if isinstance(state, Transferring):
        return [transfer_progress(state.station, state.line, state.minutes_left - 1, minute + 1)]
    if isinstance(state, Riding):
        return [ride_progress(state.tunnel, state.minutes_left - 1, minute + 1, gate)]
    return []   # Arrived: nothing more to do


def origin_moves(state: Waiting, minute: int, gate: int, metro: MetroInput, graph: Graph) -> list[Move]:
    """Keep waiting, or board any train leaving the origin (boarding first is never a transfer)."""
    departure = Stop(minute, state.station, "origin", None)
    moves = [Move(state)]
    for tunnel in graph[state.station]:
        moves.append(board(tunnel, minute, gate, metro, stops=(departure,)))
    return moves


def station_moves(state: AtStation, minute: int, gate: int, metro: MetroInput, graph: Graph) -> list[Move]:
    """Stay on the same line, or change line paying the station's transfer time."""
    transfer_time = metro.transfer_times[state.station]
    moves = []
    for tunnel in graph[state.station]:
        if tunnel.line == state.line:
            moves.append(board(tunnel, minute, gate, metro))
        elif (
            state.may_transfer
            and transfer_time == 0
            and transfer_allowed(metro.modifiers, state.line, tunnel.line, minute)
        ):
            instant_transfer = Stop(minute, state.station, "transfer", tunnel.line)
            moves.append(board(tunnel, minute, gate, metro, stops=(instant_transfer,)))

    if state.may_transfer and transfer_time > 0:
        other_lines = dict.fromkeys(tunnel.line for tunnel in graph[state.station] if tunnel.line != state.line)
        for line in other_lines:
            if transfer_allowed(metro.modifiers, state.line, line, minute):
                moves.append(transfer_progress(state.station, line, transfer_time - 1, minute + 1))
    return moves


def board(tunnel: Tunnel, minute: int, gate: int, metro: MetroInput, stops: tuple[Stop, ...] = ()) -> Move:
    """Enter a tunnel at this minute."""
    minutes_left = tunnel_minutes(metro.modifiers, tunnel, minute) - 1
    return ride_progress(tunnel, minutes_left, minute + 1, gate, stops)


def ride_progress(
    tunnel: Tunnel, minutes_left: int, end_minute: int, gate: int, stops: tuple[Stop, ...] = ()
) -> Move:
    """Spend one more minute in the tunnel; arrive at its far end when no minutes are left."""
    if minutes_left > 0:
        return Move(Riding(tunnel, minutes_left), tunnel, stops)
    station = tunnel.destination
    if station == gate:
        return Move(Arrived(station), tunnel, stops + (Stop(end_minute, station, "gate", tunnel.line),))
    arrival = Stop(end_minute, station, "ride", tunnel.line)
    return Move(AtStation(station, tunnel.line, may_transfer=True), tunnel, stops + (arrival,))


def transfer_progress(station: int, line: str, minutes_left: int, end_minute: int) -> Move:
    """Spend one more minute transferring; stand on the new line when no minutes are left."""
    if minutes_left > 0:
        return Move(Transferring(station, line, minutes_left))
    return Move(AtStation(station, line, may_transfer=False), stops=(Stop(end_minute, station, "transfer", line),))


# ---------------------------------------------------------------------------
# Search: joint breadth-first search over both travelers
# ---------------------------------------------------------------------------

def find_plan(metro: MetroInput, graph: Graph) -> Plan | None:
    """Return the fastest collision-free plan, or None if no plan exists (see docs/design.md, sections 2-3).

    Each node of the search is (Pierre's state, Amélie's state, minute), and each step is one minute.
    Breadth-first order means the first node where both have arrived is the earliest possible arrival.
    """
    mission = metro.mission
    if mission.pierre_origin == mission.amelie_origin:
        return None   # they would share a station at minute 0

    horizon = last_modifier_minute(metro.modifiers)
    start = (Waiting(mission.pierre_origin), Waiting(mission.amelie_origin), 0)
    parents = {visit_key(start, horizon): None}
    queue = deque([start])

    while queue:
        pierre, amelie, minute = node = queue.popleft()
        pierre_moves = traveler_moves(pierre, minute, mission.pierre_gate, metro, graph)
        amelie_moves = traveler_moves(amelie, minute, mission.amelie_gate, metro, graph)

        for pierre_move in pierre_moves:
            for amelie_move in amelie_moves:
                if breaks_a_rule(pierre_move, amelie_move, minute):
                    continue
                next_node = (pierre_move.state, amelie_move.state, minute + 1)
                next_key = visit_key(next_node, horizon)
                if next_key in parents:
                    continue
                parents[next_key] = (visit_key(node, horizon), pierre_move.stops, amelie_move.stops)
                if isinstance(pierre_move.state, Arrived) and isinstance(amelie_move.state, Arrived):
                    return rebuild_plan(parents, next_key)
                queue.append(next_node)

    return None


def visit_key(node: tuple, horizon: int) -> tuple:
    """Identify a search node; after the last modifier window, the same pair of states at any minute counts once."""
    pierre, amelie, minute = node
    return (pierre, amelie, min(minute, horizon))


def breaks_a_rule(pierre: Move, amelie: Move, minute: int) -> bool:
    """Whether doing both moves in the same minute breaks a rule from docs/design.md, section 3."""
    if minute == 0 and isinstance(pierre.state, Waiting) and isinstance(amelie.state, Waiting):
        return True   # at least one of them departs at minute 0
    if isinstance(pierre.state, Arrived) != isinstance(amelie.state, Arrived):
        return True   # one would reach the bunker before the other
    pierre_station = station_of(pierre.state)
    if pierre_station is not None and pierre_station == station_of(amelie.state):
        return True   # same station at the same minute
    if pierre.tunnel and amelie.tunnel and tunnel_id(pierre.tunnel) == tunnel_id(amelie.tunnel):
        return True   # same tunnel during the same minute, in either direction
    return False


def tunnel_id(tunnel: Tunnel) -> tuple[frozenset[int], str]:
    """The same id for both directions of a tunnel on a line."""
    return (frozenset((tunnel.origin, tunnel.destination)), tunnel.line)


def rebuild_plan(parents: dict, key: tuple) -> Plan:
    """Walk back from the final node to the start and collect each traveler's stops in order."""
    steps = []
    while parents[key] is not None:
        key, pierre_stops, amelie_stops = parents[key]
        steps.append((pierre_stops, amelie_stops))
    steps.reverse()
    pierre = Route(tuple(stop for pierre_stops, _ in steps for stop in pierre_stops))
    amelie = Route(tuple(stop for _, amelie_stops in steps for stop in amelie_stops))
    return Plan(pierre, amelie)


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
