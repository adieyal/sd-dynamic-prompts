import logging

from modules import script_callbacks
from modules.script_callbacks import ImageSaveParams
from modules.shared import opts

from sd_dynamic_prompts.ui.pnginfo_saver import ImagePrompts, PngInfoSaver

logger = logging.getLogger(__name__)


def register_pnginfo_saver(prompt_file_saver: PngInfoSaver):
    def on_save(image_save_params: ImageSaveParams):
        try:
            if image_save_params.p:
                png_info = image_save_params.pnginfo["parameters"]
                image_prompts = ImagePrompts(
                    image_save_params.p.prompt,
                    image_save_params.p.negative_prompt,
                )

                updated_png_info = prompt_file_saver.update_pnginfo(
                    png_info,
                    image_prompts,
                )
                image_save_params.pnginfo["parameters"] = updated_png_info
        except Exception:
            logger.exception("Error save prompt file")

    save_metadata = opts.dp_write_raw_template
    if save_metadata:
        script_callbacks.on_before_image_saved(on_save)
