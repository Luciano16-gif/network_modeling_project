"""Shared test helpers."""

import tempfile
from pathlib import Path

# A frozen copy of the original input.txt. Tests with exact expected numbers use it, so the
# submitted input.txt can be redesigned freely without breaking them.
SAMPLE_INPUT = Path(__file__).resolve().parent / "fixtures" / "sample_input.txt"


def write_temp_input(text: str) -> Path:
    """Write `text` to a temporary input file and return its path (the caller deletes it)."""
    file = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    with file:
        file.write(text)
    return Path(file.name)
