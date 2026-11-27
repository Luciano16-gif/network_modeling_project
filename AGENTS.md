# Agent instructions

## The assignment

This repository is a university project: *El Escape de los Coleccionistas en el Metro de París*.

- Specification: [`docs/enunciado-proyecto.md`](docs/enunciado-proyecto.md) (Markdown transcription, read this first).
- Original: [`docs/enunciado-proyecto.pdf`](docs/enunciado-proyecto.pdf) (source of truth if the two disagree).
- Design decisions: [`docs/design.md`](docs/design.md). Follow what is marked **Decided**; do not implement anything marked **Pending**.
- Remaining work, split into two halves, and the `Plan` contract between them: [`docs/roadmap.md`](docs/roadmap.md).
- Course material: [`docs/class-material/`](docs/class-material/README.md) (local only, git-ignored; ask the user for it if it is missing). The defense is judged against what was taught, so ground design choices (graph representation, shortest-path algorithm) in this material rather than in outside techniques.

## Hard constraints from the assignment

- Python, standard library only. No third-party packages.
- The submission is exactly three files: the source program, `input.txt`, and `output.txt`.
- The graph must be stored using one of the representations taught in class, and the team must be able to justify that choice at the defense.
- The team will be questioned on the purpose of every method, so code must be small, explicit, and easy to explain.

## Rules for coding agents (read before editing anything)

1. **Finished code: do not modify it** unless the user explicitly asks in the current session:
   - the *Graph* and *Search* sections of `metro_escape.py` (half A, verified)
   - the `Plan` contract: `Stop`, `Route`, `Plan`, `STOP_EVENTS`
   - `tests/laws.py`

   `parse_input` and `parse_modifier` may only gain the error checks listed in `docs/roadmap.md`, step B1.
2. **Tests decide when work is done.** Run `python -m unittest` from the repository root before every commit. Every test must pass.
3. **Never delete, skip or weaken a test, and never change an expected value, to make it pass.** Fix the code instead. You may add new tests.
4. **If a half A test fails after your change, your change is wrong.** Undo it. Do not edit the search to make it pass.
5. **The skipped tests are the acceptance criteria for half B.** The tests in `tests/test_validation.py` and `tests/test_report.py` turn on by themselves once `validate_input` and `format_report` stop raising `NotImplementedError`.
6. **Keep the hard constraints:** standard library only, and one program file. `tests/test_constraints.py` checks both.
7. **Keep changes small.** Do not:
   - add new `.py` files at the root
   - add dependencies
   - leave debugging prints
   - reformat or rename code you were not asked to change
8. **When unsure, stop and ask the user.** Do not guess.

## How we work

- Design decisions (graph representation, algorithm, module layout) are made together with the user. Do not implement features or pick an approach on your own; propose and discuss first.
- Code identifiers, docstrings, and comments are in English.
- User-facing output (the generated `output.txt` report and error messages) is in Spanish and follows the format in the specification exactly.

## Code conventions

Follow the style already in `metro_escape.py`:

- **One file,** organized top-down in the sections listed in `docs/design.md`, section 6. New code goes in its section, not at the end of the file.
- **Data:** immutable `@dataclass(frozen=True)` types and tuples. Values that can be derived, such as a route's arrival minute, are `@property`s, not stored fields.
- **Functions:** small, with type hints. Give a function a docstring when its name alone does not say what it returns.
- **Constants and globals:** fixed values are module-level constants in capitals, like `MODIFIER_KINDS`. There is no other global state.
- **Errors:** invalid input raises `ValueError` with a Spanish message. Do not catch errors only to hide them.
- **The `Plan` contract** (`Stop`, `Route`, `Plan`) connects the search and the report. Do not change it without updating `docs/roadmap.md`.
- **Before committing,** run `python -m unittest` and `python metro_escape.py`.
