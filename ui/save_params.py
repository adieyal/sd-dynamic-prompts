from __future__ import annotations
import logging

from modules import script_callbacks
from modules.script_callbacks import ImageSaveParams
from modules.shared import opts

from ui import constants

logger = logging.getLogger(__name__)

def on_before_image_saved(image_save_params: ImageSaveParams):
    try:
        save_metadata = getattr(opts, constants.OPTION_WRITE_RAW_TEMPLATE)
        if save_metadata:
            if image_save_params.p.prompt != "":
                image_save_params.pnginfo["parameters"] += "\nTemplate:" + image_save_params.p.prompt

            if image_save_params.p.negative_prompt != "":
                image_save_params.pnginfo["parameters"] += "\nNegative Template:" + image_save_params.p.negative_prompt
    except Exception as e:
        logger.exception("Error save metadata to image")

def initialize():
    script_callbacks.on_before_image_saved(on_before_image_saved)