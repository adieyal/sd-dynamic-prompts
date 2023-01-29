from sd_dynamic_prompts.ui.pnginfo_saver import ImagePrompts, PngInfoSaver


def test_update_pnginfo() -> None:
    png_info_saver = PngInfoSaver()
    image_prompts = ImagePrompts("Template", "Negative Template")
    parameters = "Parameters"
    updated_parameters = png_info_saver.update_pnginfo(parameters, image_prompts)

    assert (
        updated_parameters
        == f"Parameters\nTemplate: {image_prompts.prompt}\nNegative Template: {image_prompts.negative_prompt}"
    )

    image_prompts.prompt = ""
    updated_parameters = png_info_saver.update_pnginfo(parameters, image_prompts)
    assert (
        updated_parameters
        == f"Parameters\nNegative Template: {image_prompts.negative_prompt}"
    )

    image_prompts.prompt = "Positive Template"
    image_prompts.negative_prompt = ""
    updated_parameters = png_info_saver.update_pnginfo(parameters, image_prompts)
    assert updated_parameters == f"Parameters\nTemplate: {image_prompts.prompt}"
