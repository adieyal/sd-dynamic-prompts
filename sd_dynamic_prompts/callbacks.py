from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from modules import script_callbacks
from modules.generation_parameters_copypaste import parse_generation_parameters
from modules.script_callbacks import ImageSaveParams

from sd_dynamic_prompts.pnginfo_saver import PromptTemplates
from sd_dynamic_prompts.settings import on_ui_settings
from sd_dynamic_prompts.wildcards_tab import initialize as initialize_wildcards_tab

if TYPE_CHECKING:
    from sd_dynamic_prompts.sddp_script import SDDPScript


logger = logging.getLogger(__name__)


def register_pnginfo_saver(sddp: SDDPScript) -> None:
    def on_save(image_save_params: ImageSaveParams) -> None:
        if not sddp.is_enabled:
            return

        try:
            if image_save_params.p:
                png_info = image_save_params.pnginfo["parameters"]
                image_prompts = PromptTemplates(
                    positive_template=image_save_params.p.prompt,
                    negative_template=image_save_params.p.negative_prompt,
                )

                updated_png_info = sddp.pnginfo_saver.update_pnginfo(
                    png_info,
                    image_prompts,
                )
                image_save_params.pnginfo["parameters"] = updated_png_info
        except Exception:
            logger.exception("Error save prompt file")

    script_callbacks.on_before_image_saved(on_save)


def register_prompt_writer(sddp: SDDPScript) -> None:
    def on_save(image_save_params: ImageSaveParams) -> None:
        if not sddp.is_enabled:
            return

        image_name = Path(image_save_params.filename)
        prompt_filename = image_name.with_suffix(".csv")
        sddp.prompt_writer.write_prompts(prompt_filename)

    script_callbacks.on_before_image_saved(on_save)


def register_on_infotext_pasted(sddp: SDDPScript) -> None:
    def on_infotext_pasted(infotext: str, parameters: dict[str, Any]) -> None:
        if not sddp.is_enabled:
            return

        new_parameters = {}
        if "Prompt" in parameters and "Template:" in parameters["Prompt"]:
            parameters = sddp.pnginfo_saver.strip_template_info(parameters)
            new_parameters = parse_generation_parameters(parameters["Prompt"])
        elif (
            "Negative prompt" in parameters
            and "Template:" in parameters["Negative prompt"]
        ):
            parameters = sddp.pnginfo_saver.strip_template_info(parameters)
            new_parameters = parse_generation_parameters(parameters["Negative prompt"])
            new_parameters["Negative prompt"] = new_parameters["Prompt"]
            new_parameters["Prompt"] = parameters["Prompt"]
        parameters.update(new_parameters)

    script_callbacks.on_infotext_pasted(on_infotext_pasted)


def register_settings(sddp: SDDPScript) -> None:
    def on_ui_settings_callback():
        on_ui_settings(sddp)

    script_callbacks.on_ui_settings(on_ui_settings_callback)


def register_wildcards_tab(sddp: SDDPScript) -> None:
    initialize_wildcards_tab(sddp.wildcard_manager)
