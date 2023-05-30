from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sd_dynamic_prompts.utils import get_logger

logger = get_logger(__name__)

TEMPLATE_LABEL = "Template"
NEGATIVE_TEMPLATE_LABEL = "Negative Template"


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
            parameters += f"\n{TEMPLATE_LABEL}: {prompt_templates.positive_template}"

        if prompt_templates.negative_template:
            parameters += (
                f"\n{NEGATIVE_TEMPLATE_LABEL}: {prompt_templates.negative_template}"
            )

        return parameters

    def strip_template_info(self, parameters: dict[str, Any]) -> str:
        if "Prompt" in parameters and f"{TEMPLATE_LABEL}:" in parameters["Prompt"]:
            parameters["Prompt"] = (
                parameters["Prompt"].split(f"{TEMPLATE_LABEL}:")[0].strip()
            )
        elif "Negative prompt" in parameters:
            split_by = None
            if (
                f"\n{TEMPLATE_LABEL}:" in parameters["Negative prompt"]
                and f"\n{NEGATIVE_TEMPLATE_LABEL}:" in parameters["Negative prompt"]
            ):
                split_by = f"{TEMPLATE_LABEL}"
            elif f"\n{NEGATIVE_TEMPLATE_LABEL}:" in parameters["Negative prompt"]:
                split_by = f"\n{NEGATIVE_TEMPLATE_LABEL}:"
            elif f"\n{TEMPLATE_LABEL}:" in parameters["Negative prompt"]:
                split_by = f"\n{TEMPLATE_LABEL}:"

            if split_by:
                parameters["Negative prompt"] = (
                    parameters["Negative prompt"].split(split_by)[0].strip()
                )

        return parameters
