from __future__ import annotations

import logging

from dynamicprompts.generators import PromptGenerator

logger = logging.getLogger(__name__)


class DummyAttentionGenerator:
    def __init__(self, generator: PromptGenerator, *args, **kwargs):
        self._generator = generator
        logger.warning(
            "Using the DummyAttentionGenerator, this is possibly because you don't have spacy installed. "
            "Install it with `python -m pip install dynamicprompts[attentiongrabber]`"
        )

    def generate(self, *args, **kwargs) -> list[str]:
        return self._generator.generate(*args, **kwargs)
