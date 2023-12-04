from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

TEMPLATE_LABEL = "Template"
NEGATIVE_TEMPLATE_LABEL = "Negative Template"


def strip_template_info(parameters: dict[str, Any]) -> None:
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
