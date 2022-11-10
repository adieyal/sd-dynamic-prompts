from __future__ import annotations

import logging
from pathlib import Path
from prompts import constants

from .wildcardfile import WildcardFile

logger = logging.getLogger(__name__)

class WildcardManager:
    def __init__(self, path:Path):
        self._path = path

    def _directory_exists(self) -> bool:
        return self._path.exists() and self._path.is_dir()

    def ensure_directory(self):
        try:
            self._path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.exception(f"Failed to create directory {self._path}")

    def get_files(self, relative:bool=False) -> list[Path]:
        if not self._directory_exists():
            return []


        files = self._path.rglob(f"*.{constants.WILDCARD_SUFFIX}")
        if relative:
            files = [f.relative_to(self._path) for f in files]

        return files
    
    def match_files(self, wildcard:str) -> list[WildcardFile]:
        return [
            WildcardFile(path) for path in self._path.rglob(f"{wildcard}.{constants.WILDCARD_SUFFIX}")
        ]
    
    def path_to_wilcard(self, path: Path) -> str:
        rel_path = path.relative_to(self._path)
        return f"__{rel_path.with_suffix('')}__"

    def get_wildcards(self) -> list[str]:
        files = self.get_files(relative=True)
        wildcards = [self.path_to_wilcard(f) for f in files]

        return wildcards

    def get_wildcard_hierarchy(self, path: Path|None=None):
        if path is None:
            path = self._path
        
        files = path.glob("*.txt")
        wildcards = [self.path_to_wilcard(f) for f in files]
        directories = [d for d in path.glob("*") if d.is_dir()]

        hierarchy = {d.name: self.get_wildcard_hierarchy(d) for d in directories}
        return (wildcards, hierarchy)

