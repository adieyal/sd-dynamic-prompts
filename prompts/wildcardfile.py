from __future__ import annotations
from pathlib import Path

class WildcardFile:
    def __init__(self, path: Path, encoding="utf8"):
        self._path = path
        self._encoding = encoding

    def get_wildcards(self) -> set[str]:
        is_empty_line = lambda line: line is None or line.strip() == "" or line.strip().startswith("#")

        with self._path.open(encoding=self._encoding, errors="ignore") as f:
            lines = [line.strip() for line in f if not is_empty_line(line)]
            return set(lines)

