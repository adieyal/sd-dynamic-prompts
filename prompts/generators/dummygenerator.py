from __future__ import annotations

from .promptgenerator import PromptGenerator


class DummyGenerator(PromptGenerator):
    def __init__(self, template):
        self._template = template

    def generate(self, num_images) -> list[str]:
        return num_images * [self._template]
