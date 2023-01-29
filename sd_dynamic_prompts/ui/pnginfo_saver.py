from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplates:
    positive_template: str
    negative_template: str


class PngInfoSaver:
    def __init__(self):
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def update_pnginfo(self, parameters: str, prompt_templates: PromptTemplates) -> str:
        if not self._enabled:
            return parameters

        if prompt_templates.positive_template:
            parameters += f"\nTemplate: {prompt_templates.positive_template}"

        if prompt_templates.negative_template:
            parameters += f"\nNegative Template: {prompt_templates.negative_template}"

        return parameters
