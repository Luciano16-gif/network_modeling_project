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
- **Before committing,** run `python metro_escape.py` (and the tests in `tests/` once they exist).
