import logging
from pathlib import Path
from typing import Any

from modules import script_callbacks
from modules.generation_parameters_copypaste import parse_generation_parameters
from modules.script_callbacks import ImageSaveParams

from sd_dynamic_prompts.ui.pnginfo_saver import PngInfoSaver, PromptTemplates
from sd_dynamic_prompts.ui.prompt_writer import PromptWriter

logger = logging.getLogger(__name__)


def register_pnginfo_saver(pnginfo_saver: PngInfoSaver) -> None:
    def on_save(image_save_params: ImageSaveParams) -> None:
        try:
            if image_save_params.p:
                png_info = image_save_params.pnginfo["parameters"]
                image_prompts = PromptTemplates(
                    positive_template=image_save_params.p.prompt,
                    negative_template=image_save_params.p.negative_prompt,
                )

                updated_png_info = pnginfo_saver.update_pnginfo(
                    png_info,
                    image_prompts,
                )
                image_save_params.pnginfo["parameters"] = updated_png_info
        except Exception:
            logger.exception("Error save prompt file")

    script_callbacks.on_before_image_saved(on_save)


def register_prompt_writer(prompt_writer: PromptWriter) -> None:
    def on_save(image_save_params: ImageSaveParams) -> None:
        image_name = Path(image_save_params.filename)
        prompt_filename = image_name.with_suffix(".csv")
        prompt_writer.write_prompts(prompt_filename)

    script_callbacks.on_before_image_saved(on_save)


def register_on_infotext_pasted(pnginfo_saver: PngInfoSaver) -> None:
    def on_infotext_pasted(infotext: str, parameters: dict[str, Any]) -> None:
        new_parameters = {}
        if "Prompt" in parameters and "Template:" in parameters["Prompt"]:
            parameters = pnginfo_saver.strip_template_info(parameters)
            new_parameters = parse_generation_parameters(parameters["Prompt"])
        elif (
            "Negative prompt" in parameters
            and "Template:" in parameters["Negative prompt"]
        ):
            parameters = pnginfo_saver.strip_template_info(parameters)
            new_parameters = parse_generation_parameters(parameters["Negative prompt"])
            new_parameters["Negative prompt"] = new_parameters["Prompt"]
            new_parameters["Prompt"] = parameters["Prompt"]
        parameters.update(new_parameters)

    script_callbacks.on_infotext_pasted(on_infotext_pasted)
