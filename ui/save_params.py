from __future__ import annotations
import logging
from typing import Dict, Any

from modules import script_callbacks
from modules.script_callbacks import ImageSaveParams
from modules.shared import opts
from modules.generation_parameters_copypaste import parse_generation_parameters

logger = logging.getLogger(__name__)

def on_before_image_saved(image_save_params: ImageSaveParams):
    try:
        save_metadata = opts.dp_write_raw_template
        if save_metadata:
            if image_save_params.p.prompt != "":
                image_save_params.pnginfo["parameters"] += "\nTemplate:" + image_save_params.p.prompt

            if image_save_params.p.negative_prompt != "":
                image_save_params.pnginfo["parameters"] += "\nNegative Template:" + image_save_params.p.negative_prompt
    except Exception as e:
        logger.exception("Error save metadata to image")

def remove_template_from_infotext(infotext: str, parameters: Dict[str, Any]):
    new_parameters = {}

    if "Prompt" in parameters and "Template:" in parameters["Prompt"]:
        prompt = parameters["Prompt"].split("Template:")[0].strip()
        new_parameters = parse_generation_parameters(prompt)
    elif "Negative prompt" in parameters and "Template:" in parameters["Negative prompt"]:
        prompt = parameters["Negative prompt"].split("Template:")[0].strip()
        new_parameters = parse_generation_parameters(prompt)
        new_parameters["Negative prompt"] = new_parameters["Prompt"]
        new_parameters["Prompt"] = parameters["Prompt"]

    parameters.update(new_parameters)

def initialize():
    script_callbacks.on_before_image_saved(on_before_image_saved)
    script_callbacks.on_infotext_pasted(remove_template_from_infotext)