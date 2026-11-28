"""El Escape de los Coleccionistas en el Metro de París.

Reads the metro network and mission from input.txt and writes the escape plan to output.txt.
See docs/enunciado-proyecto.md for the assignment and docs/design.md for the design decisions.
"""

# No imports: the assignment allows only code written by the team, so everything here is plain Python.

# input.txt and output.txt live in the same folder as this program, wherever it is run from.
PROGRAM_FOLDER = __file__[: max(__file__.rfind("/"), __file__.rfind("\\")) + 1]
INPUT_PATH = PROGRAM_FOLDER + "input.txt"
OUTPUT_PATH = PROGRAM_FOLDER + "output.txt"


# ---------------------------------------------------------------------------
# Data types: base class
# ---------------------------------------------------------------------------

class Value:
    """Base of every data type: compared by its fields, usable as a dict key, and never changed once built."""

    def __setattr__(self, name: str, value) -> None:
        if name in vars(self):
            raise AttributeError(f"{type(self).__name__}.{name} cannot change once set")
        super().__setattr__(name, value)

    def __eq__(self, other) -> bool:
        return type(self) is type(other) and vars(self) == vars(other)

    def __hash__(self) -> int:
        return hash((type(self), tuple(vars(self).values())))

    def __repr__(self) -> str:
        fields = ", ".join(f"{name}={value!r}" for name, value in vars(self).items())
        return f"{type(self).__name__}({fields})"


# ---------------------------------------------------------------------------
# Data types: input
# ---------------------------------------------------------------------------

class Tunnel(Value):
    def __init__(self, origin: int, destination: int, minutes: int, line: str):
        self.origin = origin
        self.destination = destination
        self.minutes = minutes
        self.line = line


class Mission(Value):
    def __init__(self, pierre_origin: int, amelie_origin: int, pierre_gate: int, amelie_gate: int):
        self.pierre_origin = pierre_origin
        self.amelie_origin = amelie_origin
        self.pierre_gate = pierre_gate
        self.amelie_gate = amelie_gate


class Modifier(Value):
    def __init__(self, kind: str, line: str, start: int, end: int | None):
        self.kind = kind     # "SIN_TRANSBORDO" or "TIEMPO_DOBLE"
        self.line = line
        self.start = start   # first minute it applies (inclusive)
        self.end = end       # first minute it stops applying; None = whole operation

    def is_active(self, minute: int) -> bool:
        if self.end is None:
            return True
        return self.start <= minute < self.end


class MetroInput(Value):
    def __init__(
        self,
        transfer_times: dict[int, int],
        tunnels: tuple[Tunnel, ...],
        mission: Mission,
        modifiers: tuple[Modifier, ...],
    ):
        self.transfer_times = transfer_times   # station id -> transfer minutes
        self.tunnels = tunnels
        self.mission = mission
        self.modifiers = modifiers


# ---------------------------------------------------------------------------
# Data types: the escape plan (the search produces it, the report prints it)
# ---------------------------------------------------------------------------

STOP_EVENTS = ("origin", "ride", "transfer", "gate")


class Stop(Value):
    """One line of a traveler's route in the report."""

    def __init__(self, minute: int, station: int, event: str, line: str | None):
        self.minute = minute
        self.station = station
        self.event = event   # one of STOP_EVENTS
        self.line = line     # line ridden or transferred to; None for "origin"


class Route(Value):
    def __init__(self, stops: tuple[Stop, ...]):
        self.stops = stops   # in time order: first "origin", last "gate"

    @property
    def departure_minute(self) -> int:
        return self.stops[0].minute

    @property
    def arrival_minute(self) -> int:
        return self.stops[-1].minute


class Plan(Value):
    def __init__(self, pierre: Route, amelie: Route):
        self.pierre = pierre
        self.amelie = amelie

    @property
    def total_minutes(self) -> int:
        return max(self.pierre.arrival_minute, self.amelie.arrival_minute)


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

class Waiting(Value):
    """At their origin, not departed yet."""

    def __init__(self, station: int):
        self.station = station


class AtStation(Value):
    """At a station on a line, about to leave it (nobody waits mid-route)."""

    def __init__(self, station: int, line: str, may_transfer: bool):
        self.station = station
        self.line = line
        # False right after a transfer: changing back and forth would be waiting in disguise.
        self.may_transfer = may_transfer


class Transferring(Value):
    """Changing to another line inside a station."""

    def __init__(self, station: int, line: str, minutes_left: int):
        self.station = station
        self.line = line   # the line being transferred to
        self.minutes_left = minutes_left


class Riding(Value):
    """Inside a tunnel, between two stations."""

    def __init__(self, tunnel: Tunnel, minutes_left: int):
        self.tunnel = tunnel
        self.minutes_left = minutes_left


class Arrived(Value):
    """At their own bunker gate. The route is over."""

    def __init__(self, station: int):
        self.station = station


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

class Move(Value):
    """One traveler's next minute: where they end up, the tunnel they use, and the report lines it produces."""

    def __init__(self, state: TravelerState, tunnel: Tunnel | None = None, stops: tuple[Stop, ...] = ()):
        self.state = state
        self.tunnel = tunnel
        self.stops = stops


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
# Search: the rules both travelers must follow together
# ---------------------------------------------------------------------------

def breaks_a_rule(pierre: Move, amelie: Move, minute: int) -> bool:
    """Whether doing both moves in the minute that starts at `minute` breaks a rule from docs/design.md, section 3."""
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


# ---------------------------------------------------------------------------
# Search: one edge of the search graph (a leg)
# ---------------------------------------------------------------------------

class Leg(Value):
    """One edge: both travelers make a first move, then keep going while both are riding or transferring."""

    def __init__(
        self,
        pierre: TravelerState,
        amelie: TravelerState,
        minutes: int,
        pierre_stops: tuple[Stop, ...],
        amelie_stops: tuple[Stop, ...],
    ):
        self.pierre = pierre       # Pierre's state when the leg ends
        self.amelie = amelie       # Amélie's state when the leg ends
        self.minutes = minutes     # the edge's weight
        self.pierre_stops = pierre_stops
        self.amelie_stops = amelie_stops


def is_forced(state: TravelerState) -> bool:
    """Inside a tunnel or mid-transfer, a traveler has exactly one move: keep going."""
    return isinstance(state, (Riding, Transferring))


def joint_legs(pierre: TravelerState, amelie: TravelerState, minute: int, metro: MetroInput, graph: Graph) -> list[Leg]:
    """Return every edge leaving the node where both travelers are at `minute`: one per pair of first moves."""
    mission = metro.mission
    legs = []
    for pierre_move in traveler_moves(pierre, minute, mission.pierre_gate, metro, graph):
        for amelie_move in traveler_moves(amelie, minute, mission.amelie_gate, metro, graph):
            leg = follow_leg(pierre_move, amelie_move, minute, metro, graph)
            if leg is not None:
                legs.append(leg)
    return legs


def follow_leg(pierre_move: Move, amelie_move: Move, start_minute: int, metro: MetroInput, graph: Graph) -> Leg | None:
    """Play the leg minute by minute from the two first moves; return None if any minute breaks a rule."""
    mission = metro.mission
    pierre_stops, amelie_stops = (), ()
    minute = start_minute
    while True:
        # pierre_move and amelie_move happen during the minute that starts at `minute`.
        if breaks_a_rule(pierre_move, amelie_move, minute):
            return None
        pierre_stops += pierre_move.stops
        amelie_stops += amelie_move.stops
        minute += 1
        if not (is_forced(pierre_move.state) and is_forced(amelie_move.state)):
            return Leg(pierre_move.state, amelie_move.state, minute - start_minute, pierre_stops, amelie_stops)
        # Both are forced, so each has exactly one move in the next minute.
        pierre_move = traveler_moves(pierre_move.state, minute, mission.pierre_gate, metro, graph)[0]
        amelie_move = traveler_moves(amelie_move.state, minute, mission.amelie_gate, metro, graph)[0]


# ---------------------------------------------------------------------------
# Search: Dijkstra over both travelers
# ---------------------------------------------------------------------------

def find_plan(metro: MetroInput, graph: Graph) -> Plan | None:
    """Return the fastest collision-free plan, or None if no plan exists (see docs/design.md, sections 2-3).

    Dijkstra as taught in class. Each node is where both travelers are (see search_node), each edge is a leg
    weighted by its minutes, and a node's distance is the minute both travelers reach it.
    """
    mission = metro.mission
    if mission.pierre_origin == mission.amelie_origin:
        return None   # they would share a station at minute 0

    horizon = last_modifier_minute(metro.modifiers)
    start = search_node(Waiting(mission.pierre_origin), Waiting(mission.amelie_origin), 0, horizon)
    distance = {start: 0}          # node -> smallest known distance (minutes)
    predecessor = {start: None}    # node -> (previous node, Pierre's stops, Amélie's stops) of the best leg into it
    visited = set()
    # Distances are whole minutes, so the nodes found but not visited yet are grouped by distance. The unvisited
    # node with the smallest distance is then always in the list of the lowest minute, with no need to scan them all.
    # Every leg lasts at least one minute, so visiting a minute's nodes only adds nodes to later minutes.
    unvisited_by_minute = {0: [start]}

    minute = 0
    while unvisited_by_minute:
        # Every node visited here has distance[node] == minute; a minute with no nodes gives an empty list.
        for node in unvisited_by_minute.pop(minute, []):
            if node in visited:
                continue   # an outdated entry: a shorter way was found later, so the node was already visited
            visited.add(node)
            pierre, amelie, _ = node
            if isinstance(pierre, Arrived):   # the rules only let both arrive together
                return rebuild_plan(predecessor, node)

            for leg in joint_legs(pierre, amelie, distance[node], metro, graph):
                new_distance = distance[node] + leg.minutes
                neighbor = search_node(leg.pierre, leg.amelie, new_distance, horizon)
                if neighbor in visited:
                    continue
                if neighbor not in distance or new_distance < distance[neighbor]:
                    distance[neighbor] = new_distance
                    predecessor[neighbor] = (node, leg.pierre_stops, leg.amelie_stops)
                    unvisited_by_minute.setdefault(new_distance, []).append(neighbor)
        minute += 1

    return None


def search_node(pierre: TravelerState, amelie: TravelerState, minute: int, horizon: int) -> tuple:
    """Identify a node: both states, plus the minute while a modifier window can still open or close.

    From the last modifier minute on, the same two states always have the same moves and leg lengths, so the minute
    is capped there and those nodes count once. (The minute-0 rule is not affected: the leg where both keep waiting
    at minute 0 is rejected, so "both waiting" is only ever the start node.)
    """
    return (pierre, amelie, min(minute, horizon))


def rebuild_plan(predecessor: dict, node: tuple) -> Plan:
    """Walk back from the final node to the start and collect each traveler's stops in order."""
    steps = []
    while predecessor[node] is not None:
        node, pierre_stops, amelie_stops = predecessor[node]
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
