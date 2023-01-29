from __future__ import annotations

import csv
from pathlib import Path

from dynamicprompts import constants


class PromptWriter:
    def __init__(self):
        self.reset()
        self._enabled = False

    def reset(self):
        self._already_saved = False
        self._positive_prompt = ""
        self._negative_prompt = ""
        self._positive_prompts = []
        self._negative_prompts = []

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = value

    def set_data(
        self,
        positive_prompt: str,
        negative_prompt: str,
        positive_prompts: list[str],
        negative_prompts: list[str],
    ) -> None:
        self._positive_prompt = positive_prompt
        self._negative_prompt = negative_prompt
        self._positive_prompts = positive_prompts
        self._negative_prompts = negative_prompts

    def write_prompts(self, path: Path | str) -> Path | None:
        if not self._enabled or self._already_saved:
            return None

        self._already_saved = True

        path = Path(path)
        with path.open("w", encoding=constants.DEFAULT_ENCODING, errors="ignore") as f:
            writer = csv.writer(f)
            writer.writerow(["positive_prompt", "negative_prompt"])
            writer.writerow([self._positive_prompt, self._negative_prompt])
            for positive_prompt, negative_prompt in zip(
                self._positive_prompts,
                self._negative_prompts,
            ):
                writer.writerow([positive_prompt, negative_prompt])

        return path
