from __future__ import annotations

from dynamicprompts.generators.promptgenerator import PromptGenerator


class FrozenPromptGenerator(PromptGenerator):
    """
    Generates a prompt once and repeats that prompt as num_images times
    """

    def __init__(self, prompt_generator: PromptGenerator):
        self._generator = prompt_generator

    def generate(
        self,
        template: str,
        num_images: int = 1,
    ) -> list[str]:
        prompts = self._generator.generate(template, 1)
        return num_images * prompts
