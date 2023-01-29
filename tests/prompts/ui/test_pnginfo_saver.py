from sd_dynamic_prompts.ui.pnginfo_saver import PngInfoSaver, PromptTemplates


def test_update_pnginfo() -> None:
    png_info_saver = PngInfoSaver()
    image_prompts = PromptTemplates("Template", "Negative Template")
    parameters = "Parameters"
    updated_parameters = png_info_saver.update_pnginfo(parameters, image_prompts)

    assert (
        updated_parameters
        == f"Parameters\nTemplate: {image_prompts.positive_template}\nNegative Template: {image_prompts.negative_template}"
    )

    image_prompts.positive_template = ""
    updated_parameters = png_info_saver.update_pnginfo(parameters, image_prompts)
    assert (
        updated_parameters
        == f"Parameters\nNegative Template: {image_prompts.negative_template}"
    )

    image_prompts.positive_template = "Positive Template"
    image_prompts.negative_template = ""
    updated_parameters = png_info_saver.update_pnginfo(parameters, image_prompts)
    assert (
        updated_parameters == f"Parameters\nTemplate: {image_prompts.positive_template}"
    )
