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
        self._positive_template = ""
        self._negative_template = ""
        self._positive_prompts = []
        self._negative_prompts = []

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def set_data(
        self,
        *,
        positive_template: str,
        negative_template: str,
        positive_prompts: list[str],
        negative_prompts: list[str],
    ) -> None:
        self.reset()

        self._positive_template = positive_template
        self._negative_template = negative_template
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
            writer.writerow([self._positive_template, self._negative_template])
            for positive_prompt, negative_prompt in zip(  # noqa: B905
                self._positive_prompts,
                self._negative_prompts,
            ):
                writer.writerow([positive_prompt, negative_prompt])

        return path
