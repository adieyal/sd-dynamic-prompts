import logging
from pathlib import Path

from modules import script_callbacks
from modules.script_callbacks import ImageSaveParams

from sd_dynamic_prompts.ui.pnginfo_saver import ImagePrompts, PngInfoSaver
from sd_dynamic_prompts.ui.prompt_writer import PromptWriter

logger = logging.getLogger(__name__)


def register_pnginfo_saver(pnginfo_saver: PngInfoSaver) -> None:
    def on_save(image_save_params: ImageSaveParams) -> None:
        try:
            if image_save_params.p:
                png_info = image_save_params.pnginfo["parameters"]
                image_prompts = ImagePrompts(
                    image_save_params.p.prompt,
                    image_save_params.p.negative_prompt,
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
