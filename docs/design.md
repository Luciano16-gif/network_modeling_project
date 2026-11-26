# Design decisions

Decisions agreed with the team, with the reasoning needed for the oral defense.
Status of each item: **Decided** or **Pending** (waiting on an answer from the professor).

## 1. Graph representation: adjacency list (Decided)

The metro is stored as a **lista de adyacencia**: each station maps to its list of outgoing tunnels (destination, travel time, line). Each station's transfer time is stored as station data.

Why this one, for the defense:

- The search keeps asking "where can I go from this station?", and an adjacency list answers that directly, in time proportional to the station's out-degree.
- Memory is O(V + E). A metro is sparse: each station connects to only a few others.
- Parallel tunnels between the same two stations on different lines are just two entries in the list.

Why not the other four representations taught in class:

| Representation | Why it loses here |
| --- | --- |
| Matriz de adyacencia | O(V²) memory for a sparse graph, and finding a station's exits means scanning a whole row. Parallel tunnels need a list inside each cell. |
| Matriz de incidencia | O(V·E) memory, and finding exits means scanning columns. |
| Lista de lados | Finding a station's exits means scanning the whole edge list. |
| Star (forward star) | Same O(V + E) and direct access to exits, but its offset arrays add bookkeeping that is harder to explain. The closest alternative. |

## 2. Algorithm: joint breadth-first search over both travelers (Decided)

The search state holds **both** travelers at once: where each one is (waiting at their origin, at a station on a line, transferring, or partway through a tunnel). Each step advances the clock by one minute. From each state, the search tries every combination of the two travelers' next moves, discards the combinations that break a rule, and records predecessors. The first state where both reach their gates in the same minute is the optimal plan, and both routes are rebuilt from the predecessors.

This is **breadth-first search** (Unit 2) on a state graph generated as the search goes. It is also exactly what **Dijkstra** (Unit 3) does when every step costs the same (one minute). The metro itself stays in the adjacency list.

### Why not plan one traveler, then the other?

Planning Pierre first, freezing his route, and fitting Amélie around it never revisits Pierre's choice. It can miss a plan that exists:

```
Pierre: 1 → X → 3                (2 min, passes X at minute 1)
Amélie: 2 → X → 4                (2 min, passes X at minute 1)
Pierre's detour: 1 → 5 → 6 → 3   (3 min, avoids X)
```

With Pierre's fastest route frozen, Amélie cannot arrive at minute 2 without meeting him at X, so the method finds nothing. The real optimum is for Pierre to take the detour while Amélie leaves at minute 1, both arriving at minute 3. It also freezes the arrival minute, and the person waiting at their origin can block that station.

In the benchmark below, planning one traveler at a time found no plan on 11–29% of solvable random inputs, and failed most often on small, hand-sized networks.

Conflict-Based Search (the professional standard for multi-agent routing) was considered and rejected. It targets many agents on large maps, the simultaneous-arrival rule complicates it, it can blow up when the routes cross a lot, and it was not taught.

### Benchmark (throwaway Python prototype, random metro-like networks)

| Stations (tunnels) | Typical | Slowest observed | Proving no solution exists | Peak memory |
| --- | --- | --- | --- | --- |
| 15 (~34) | 0.01 s | 0.03 s | 0.02 s | — |
| 30–60 | 0.1 s | 0.4 s | 0.4 s | ~30 MB |
| 100 | 0.4 s | 1.7 s | 1.4 s | — |
| 200 | 3 s | 5 s | 9 s | ~400 MB |
| 300 (~680) | 3 s | 24 s | not measured | ~900 MB |

Any hand-written input is effectively instant. The spec's example header has 15 stations and 22 tunnels.

## 3. Rules the search enforces (Decided)

- **Waiting:** a traveler may wait only at their own origin, before departing. At least one traveler departs at minute 0. Waiting counts as being at that station.
- **Transfers:** first boarding and staying on the same line cost nothing. Changing line costs the station's full transfer time, and the traveler occupies the station throughout. After a transfer the traveler must board a train of the new line: changing back and forth would be waiting mid-route in disguise. A transfer time of 0 makes the change instant.
- **Station collision:** the two travelers may never be at the same station at the same integer minute. This includes arriving, departing, transferring, and waiting.
- **Tunnel / same-train collision:** a tunnel is identified by the two stations it joins (either direction) plus its line. The travelers may not use the same tunnel during the same minute. That covers both opposite directions and the same train.
- **Arrival:** Pierre ends at the first bunker gate in the mission line (D1), Amélie at the second (D2). The two gates are different stations (section 5b). Neither may reach their gate before the other. The departure offset for the report is read directly from the plan.
- **No solution:** the report prints a short Spanish message saying so.

## 4. File formats (Decided)

- `input.txt` follows the example in the spec exactly: counts, stations with transfer times, tunnels, mission line. The `#` lines are comments.
- `output.txt` follows the example in the spec exactly, in Spanish.

## 5. Line modifiers (Decided: our own syntax, requested by the professor)

The spec says the input may declare lines that forbid transfers at certain times and lines whose travel time is doubled, but the example input has no syntax for them. We defined our own syntax, and the professor asked us to send it to him so he can use it. The Spanish proposal is [`propuesta-modificadores.md`](propuesta-modificadores.md). If the syntax ever changes, only the modifier parsing function changes.

Syntax: an optional section after the mission line, one modifier per line.

```
# Modificadores (opcional): Tipo | Línea | Minuto_Inicio | Minuto_Fin
SIN_TRANSBORDO L4 10 30
TIEMPO_DOBLE L1 0 45
TIEMPO_DOBLE L9
```

- `SIN_TRANSBORDO <line> [start end]`: during the window, nobody may **start** a transfer onto or off that line, at any station. Its trains keep running: riding straight through and boarding it at your origin are allowed. A traveler on the line during the window must keep riding that line, in either direction, because they can neither change lines nor wait mid-route.
- `TIEMPO_DOBLE <line> [start end]`: every tunnel of that line entered during the window takes twice its listed time. It is decided per tunnel, at the minute the traveler enters it, so a traveler already on the train when the window opens rides their next tunnels at double time. Always ×2. Overlapping windows do not stack.
- Times are minutes from the start of the operation. The window includes the start minute and excludes the end minute (`10 30` = minutes 10–29). No window means the modifier is active for the whole operation.
- The section is optional, so a file in the spec's exact format still works.
- In the code, the search only asks two questions: "may this transfer start at minute t?" and "how long does this tunnel take if entered at minute t?". The syntax never reaches the search.
- Not supported: a line that stops running completely. "Clausurada" is read as "no transfers", which is what the spec's sentence describes.

## 5b. Bunker gates (Decided)

The prose describes one bunker with two gates, D1 for Pierre and D2 for Amélie. In the graph the bunker is **two nodes, one per gate**, which is what the spec's examples show:

- The mission line `1 12 7 8` gives two gate IDs (`Destino_Búnker_P`, `Destino_Búnker_A`).
- The example output ends with Pierre at `Estación 7 (Destino Compuerta D1)` and Amélie at `Estación 8 (Destino Compuerta D2)`, both at minute 28.

The professor confirmed that a node cannot have two entrances, so each gate is its own station. Arriving together therefore never breaks the station-collision rule. A mission line with the same gate twice is invalid input.

## 6. Code layout (Decided)

One Python source file (the submission is exactly three files: program, `input.txt`, `output.txt`). Expected size is roughly 400–700 lines. It is organized top-down in clear sections: data types, parsing, graph, search, report, `main`.

The search hands its result to the report as a `Plan` (one `Route` of `Stop`s per traveler). The contract and the remaining work are in [`roadmap.md`](roadmap.md).
