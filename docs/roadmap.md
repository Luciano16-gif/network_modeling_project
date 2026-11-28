# Roadmap

How the rest of the program gets built. The work is split into two halves that meet at one contract: the search returns a `Plan`, and the report prints it. Each half can be built and checked without waiting for the other.

Read first: [`enunciado-proyecto.md`](enunciado-proyecto.md) (the assignment) and [`design.md`](design.md) (every rule below comes from there).

## Already done (the base)

All in `metro_escape.py`:

- **Input data types:** `Tunnel`, `Mission`, `Modifier`, `MetroInput`.
- **Plan data types:** `Stop`, `Route`, `Plan`. This is the contract between the two halves.
- **Parser:** `parse_input` reads `input.txt`, including the optional modifier section.
- **`main`:** the full pipeline, from reading the input through validating, building the graph, searching and writing the report.
- **Half A, the engine:** `build_graph` and `find_plan` are implemented, with each traveler's states and moves.
- **Stubs:** one empty function per remaining half B step, each marked `TODO (half B)`.

## The contract: `Plan`

The search returns a `Plan`, or `None` when no plan exists. A `Plan` holds one `Route` per traveler, and a `Route` is the list of `Stop`s that become the lines of the report.

| `Stop.event` | `minute` is when… | `line` | Report line |
| --- | --- | --- | --- |
| `"origin"` | the traveler departs | `None` | `Minuto 0: Estación 1 (Origen)`, or `(Origen - Inicia Movimiento)` if the departure minute is above 0 |
| `"ride"` | the train arrives at `station` | line ridden | `Minuto 4: Estación 2 (Viaje L1)` |
| `"transfer"` | the transfer at `station` finishes | line transferred to | `Minuto 7: Estación 2 (Termina Transbordo a L4)` |
| `"gate"` | the traveler arrives at their gate | line ridden | `Minuto 28: Estación 7 (Destino Compuerta D1)` (`D2` for Amélie) |

- The first stop is always `"origin"`, and the last one is always `"gate"`.
- Every tunnel adds one `"ride"` stop, except the last tunnel, which adds the `"gate"` stop.
- `Route.departure_minute`, `Route.arrival_minute` and `Plan.total_minutes` are derived from the stops and are never stored separately.

Do not change the contract unless both halves agree, since both depend on it.

## Half A: the engine (done)

Lives in the *Graph* and *Search* sections. Kept here as a description of how it works.

### A1. `build_graph` (adjacency list)

- **What it builds:** a `dict` from station id to the list of `Tunnel`s that leave that station. Tunnels are directed, exactly as written in the input.
- **Every station is a key,** even one with no exits, so later lookups never fail.
- **Done when:** the graph for `input.txt` has 15 keys and 22 tunnels in total, and `graph[2]` holds the tunnels `2 → 3`, `2 → 5` and `2 → 1`.

### A2. Traveler states and moves

- **States:** each traveler is in one of five states, as described in `design.md`, sections 2–3:
  - waiting at their origin
  - at a station on a line
  - transferring (with minutes left)
  - riding a tunnel (with minutes left)
  - arrived at their gate
- **Moves:** a function that, given one traveler's state and the current minute, returns every state that traveler can be in one minute later.
- **Modifiers** enter only through two helpers:
  - "may a transfer onto or off this line start at minute t?" (`SIN_TRANSBORDO`)
  - "how many minutes does this tunnel take if entered at minute t?" (`TIEMPO_DOBLE`, ×2 per tunnel)
- **Done when:** one traveler alone, with no modifiers, reaches every station in the same times a hand calculation gives.

### A3. `find_plan` (Dijkstra over both travelers)

- **The search:** Dijkstra over pairs of states (`design.md`, section 2). Each edge is a leg: both travelers make a first move, then keep going while both are inside a tunnel or mid-transfer. It is weighted by its minutes. It rejects every leg that breaks a rule in `design.md`, section 3:
  - both travelers at the same station in the same minute
  - both travelers in the same tunnel in the same minute
  - waiting anywhere other than the origin
  - one traveler arriving before the other
- **At least one traveler departs at minute 0.**
- **When both reach their gates in the same minute,** rebuild both routes from the predecessors as `Stop`s.
- **Done when:** `find_plan` returns a `Plan` for `input.txt` whose routes follow every rule.

## Half B: everything around the engine

Lives in the *Parsing*, *Report* and *Main* sections, plus a `tests/` folder.

### B1. `validate_input` and error messages

Raise `ValueError` with a Spanish message when:

- a tunnel, origin or gate names a station that is not listed
- Pierre's gate and Amélie's gate are the same station (the bunker is two nodes, one per gate)
- a traveler's origin is their own gate (they would already be at the bunker at minute 0)
- a station is listed twice
- a travel time is zero or negative, or a transfer time is negative
- a modifier has exactly one minute, a start that is not before its end, or a line that no tunnel uses

Also:

- **A short file:** when the file has fewer lines than its counts promise, `parse_input` currently fails with a bare `StopIteration`. Turn that into a clear Spanish message.
- **`main`:** catch `ValueError`, print the message, and stop without writing `output.txt`.
- **Done when:** every test in `tests/test_validation.py` passes. They are skipped until `validate_input` stops raising `NotImplementedError`.

### B2. `format_report`

- **Format:** return the exact text of the spec's `output.txt` example, using the contract table above.
- **The departure section:** for each traveler, print `* Pierre arranca en el minuto: N`. If N is above 0, append `(Debe esperar N minutos en su estación de origen)`.
- **Travel time** in each route header is `arrival_minute - departure_minute`.
- **When `plan` is `None`,** print a short Spanish message saying that no collision-free plan with a simultaneous arrival exists.
- **Done when:** every test in `tests/test_report.py` passes. They are skipped until `format_report` stops raising `NotImplementedError`. `test_spec_example` holds the exact expected text.

### B3. The final `input.txt`

- **What it must show:** design the submitted input so the plan visibly includes at least one transfer, one collision the search had to avoid (a wait or a detour), and an effect from each modifier.
- **Then:** generate `output.txt` from it.
- **Tests:** the tests with exact numbers use `tests/fixtures/sample_input.txt`, a frozen copy of the original input. Changing `input.txt` does not break them. The only test that reads `input.txt` checks that it has a plan following every rule.

### B4. Tests (already in place)

The `tests/` folder uses only `unittest` and is not part of the three submitted files. Run it with `python -m unittest`.

| File | What it covers |
| --- | --- |
| `tests/laws.py` | The plan checker and a brute force, written independently of the search |
| `tests/test_engine.py` | Half A: every rule and optimality on 150 random networks |
| `tests/test_parsing.py` | Parsing and modifier windows |
| `tests/test_constraints.py` | No imports in the program, one program file, the `Plan` contract |
| `tests/test_validation.py` | Half B, step B1 (skipped until implemented) |
| `tests/test_report.py` | Half B, step B2 (skipped until implemented) |

Add tests for anything new. Never weaken the existing ones.

## Rules for everyone

- **Run the program** with `python metro_escape.py`. It needs Python 3.10 or newer.
- **Run the tests** with `python -m unittest` before every commit. GitHub runs them on every PR too.
- **Stay in your own sections** of `metro_escape.py`, which keeps merges clean.
- **One branch and one PR per step,** squash-merged into `main`.
- **Do not:**
  - plan one traveler at a time (see `design.md`, section 2)
  - use Conflict-Based Search or any third-party package
  - change the input format without updating `design.md`
  - implement anything not described in the spec and `design.md`
