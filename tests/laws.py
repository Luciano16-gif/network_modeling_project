"""The rules of the escape, checked independently of the search in metro_escape.py.

Two tools used by the tests:

- check_plan: rebuilds both travelers' minute-by-minute timelines from a Plan's stops and
  fails if any rule from docs/design.md (sections 3 and 5) is broken.
- brute_force_total: the earliest legal arrival minute, found by enumerating every timeline
  of each traveler. Slow, but simple enough to trust; only for tiny networks.

Neither reuses the search code, so a bug in the search cannot hide itself here.
"""

import metro_escape as m


# ---------------------------------------------------------------------------
# The rules, restated from docs/design.md
# ---------------------------------------------------------------------------

def is_doubled(metro, line, minute):
    return any(x.kind == "TIEMPO_DOBLE" and x.line == line and x.is_active(minute) for x in metro.modifiers)


def blocks_transfers(metro, line, minute):
    return any(x.kind == "SIN_TRANSBORDO" and x.line == line and x.is_active(minute) for x in metro.modifiers)


def ride_minutes(metro, tunnel, minute):
    return tunnel.minutes * (2 if is_doubled(metro, tunnel.line, minute) else 1)


def tunnel_id(tunnel):
    return (frozenset((tunnel.origin, tunnel.destination)), tunnel.line)


# A timeline is (stations, tunnels):
#   stations[t] = station occupied at minute t, or None while inside a tunnel
#   tunnels[t]  = id of the tunnel used between minute t and t + 1, or None


def departure_minute(tunnels):
    for minute, tunnel in enumerate(tunnels):
        if tunnel is not None:
            return minute
    return len(tunnels)


def compatible(pierre, amelie):
    """Both timelines end at the same minute, someone departs at 0, and they never collide."""
    (p_stations, p_tunnels), (a_stations, a_tunnels) = pierre, amelie
    if len(p_stations) != len(a_stations):
        return False
    if min(departure_minute(p_tunnels), departure_minute(a_tunnels)) != 0:
        return False
    if any(p is not None and p == a for p, a in zip(p_stations, a_stations)):
        return False
    return not any(p is not None and p == a for p, a in zip(p_tunnels, a_tunnels))


# ---------------------------------------------------------------------------
# Law checker
# ---------------------------------------------------------------------------

def timeline_from_route(metro, route, origin, gate):
    """Rebuild one traveler's timeline from their stops, asserting each step is legal."""
    stops = route.stops
    assert stops, "empty route"
    assert all(stop.event in m.STOP_EVENTS for stop in stops), "unknown stop event"
    first, last = stops[0], stops[-1]
    assert (first.event, first.station, first.line) == ("origin", origin, None), f"bad first stop {first}"
    assert (last.event, last.station) == ("gate", gate), f"bad last stop {last}"
    assert sum(stop.event in ("origin", "gate") for stop in stops) == 2, "origin/gate stop in the middle"

    stations = [origin] * (first.minute + 1)
    tunnels = [None] * first.minute
    station, line, now, just_transferred = origin, None, first.minute, False

    for stop in stops[1:]:
        if stop.event == "transfer":
            assert line is not None and not just_transferred, f"transfer not allowed here: {stop}"
            assert stop.station == station and stop.line != line, f"bad transfer {stop}"
            assert not blocks_transfers(metro, line, now), f"SIN_TRANSBORDO broken: {stop}"
            assert not blocks_transfers(metro, stop.line, now), f"SIN_TRANSBORDO broken: {stop}"
            wait = metro.transfer_times[station]
            assert stop.minute == now + wait, f"transfer should end at {now + wait}: {stop}"
            stations += [station] * wait
            tunnels += [None] * wait
            line, now, just_transferred = stop.line, stop.minute, True
            continue

        assert line is None or stop.line == line, f"changed line without a transfer: {stop}"
        assert stop.event == "gate" or stop.station != gate, f"passed through own gate: {stop}"
        candidates = [
            t for t in metro.tunnels
            if (t.origin, t.destination, t.line) == (station, stop.station, stop.line)
            and stop.minute == now + ride_minutes(metro, t, now)
        ]
        assert candidates, f"no tunnel {station}->{stop.station} on {stop.line} arriving at {stop.minute}"
        minutes = stop.minute - now
        stations += [None] * (minutes - 1) + [stop.station]
        tunnels += [tunnel_id(candidates[0])] * minutes
        station, line, now, just_transferred = stop.station, stop.line, stop.minute, False

    return stations, tunnels


def check_plan(metro, plan):
    """Fail with an AssertionError if the plan breaks any rule."""
    mission = metro.mission
    pierre = timeline_from_route(metro, plan.pierre, mission.pierre_origin, mission.pierre_gate)
    amelie = timeline_from_route(metro, plan.amelie, mission.amelie_origin, mission.amelie_gate)
    assert plan.pierre.arrival_minute == plan.amelie.arrival_minute, "arrivals differ"
    assert plan.total_minutes == plan.pierre.arrival_minute
    assert compatible(pierre, amelie), "collision, or nobody departs at minute 0"


# ---------------------------------------------------------------------------
# Brute force
# ---------------------------------------------------------------------------

def timelines(metro, origin, gate, total):
    """Every legal timeline of one traveler that reaches their gate exactly at minute `total`."""
    exits = {}
    for tunnel in metro.tunnels:
        exits.setdefault(tunnel.origin, []).append(tunnel)
    found = []

    def extend(station, line, minute, stations, tunnels):
        if line is None and minute < total:   # still waiting at the origin
            extend(station, None, minute + 1, stations + [station], tunnels + [None])
        for tunnel in exits.get(station, []):
            new_stations, new_tunnels, board = list(stations), list(tunnels), minute
            if line is not None and tunnel.line != line:
                if blocks_transfers(metro, line, minute) or blocks_transfers(metro, tunnel.line, minute):
                    continue
                wait = metro.transfer_times[station]
                new_stations += [station] * wait
                new_tunnels += [None] * wait
                board = minute + wait
            minutes = ride_minutes(metro, tunnel, board)
            arrive = board + minutes
            if arrive > total:
                continue
            new_stations += [None] * (minutes - 1) + [tunnel.destination]
            new_tunnels += [tunnel_id(tunnel)] * minutes
            if tunnel.destination == gate:
                if arrive == total:
                    found.append((new_stations, new_tunnels))
                continue
            extend(tunnel.destination, tunnel.line, arrive, new_stations, new_tunnels)

    extend(origin, None, 0, [origin], [])
    return found


def brute_force_total(metro, limit):
    """The earliest minute both can arrive legally, or None if there is none up to `limit`."""
    mission = metro.mission
    for total in range(1, limit + 1):
        pierre_options = timelines(metro, mission.pierre_origin, mission.pierre_gate, total)
        if not pierre_options:
            continue
        amelie_options = timelines(metro, mission.amelie_origin, mission.amelie_gate, total)
        if any(compatible(p, a) for p in pierre_options for a in amelie_options):
            return total
    return None


# ---------------------------------------------------------------------------
# Random tiny networks
# ---------------------------------------------------------------------------

def random_metro(rng):
    """A random network of 4-7 stations, or None if the draw is unusable."""
    count = rng.randint(4, 7)
    lines = ["L1", "L2", "L3"][: rng.randint(1, 3)]
    transfer_times = {station: rng.randint(0, 3) for station in range(1, count + 1)}
    tunnels = set()
    for _ in range(rng.randint(count, 3 * count)):
        u, v = rng.sample(range(1, count + 1), 2)
        line, minutes = rng.choice(lines), rng.randint(1, 4)
        tunnels.add(m.Tunnel(u, v, minutes, line))
        if rng.random() < 0.6:
            tunnels.add(m.Tunnel(v, u, minutes, line))
    pierre_origin, amelie_origin, pierre_gate, amelie_gate = rng.sample(range(1, count + 1), 4)
    modifiers = []
    for _ in range(rng.choice([0, 0, 1, 2])):
        kind, line = rng.choice(m.MODIFIER_KINDS), rng.choice(lines)
        if rng.random() < 0.3:
            modifiers.append(m.Modifier(kind, line, 0, None))
        else:
            start = rng.randint(0, 8)
            modifiers.append(m.Modifier(kind, line, start, start + rng.randint(1, 8)))
    ordered = tuple(sorted(tunnels, key=lambda t: (t.origin, t.destination, t.line, t.minutes)))
    mission = m.Mission(pierre_origin, amelie_origin, pierre_gate, amelie_gate)
    return m.MetroInput(transfer_times, ordered, mission, tuple(modifiers))
