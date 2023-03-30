from typing import Any

import pytest

from sd_dynamic_prompts.pnginfo_saver import PngInfoSaver, PromptTemplates


@pytest.fixture
def basic_parameters():
    return {
        "Prompt": "",
        "Negative prompt": "",
        "Clip skip": "1",
        "Hires resize-1": 0,
        "Hires resize-2": 0,
    }


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


BASIC_PARAMETERS = "Steps: 35, Sampler: Heun, CFG scale: 9, Seed: 77777, Size: 640x640, Model hash: d8691b4d16"


def build_parameters(positive_template, negative_template):
    template = positive_template if not negative_template else negative_template

    s = f"{template}\n{BASIC_PARAMETERS}"

    if positive_template:
        s += f"\nTemplate: {positive_template}"
    if negative_template:
        s += f"\nNegative Template: {negative_template}"

    return s


@pytest.mark.parametrize(
    ("positive_prompt", "negative_prompt"),
    [
        ("positive text", "negative text"),
        ("positive text", "negative text\nwith\nlines"),
        ("No negative prompt", ""),
        ("", "No positive prompt"),
    ],
)
def test_remove_template_from_infotext(
    basic_parameters: dict[str, Any],
    positive_prompt: str,
    negative_prompt: str,
) -> None:
    png_info_saver = PngInfoSaver()
    if not negative_prompt:
        basic_parameters["Prompt"] = build_parameters(positive_prompt, negative_prompt)
        basic_parameters["Negative prompt"] = ""
    else:
        basic_parameters["Prompt"] = positive_prompt
        basic_parameters["Negative prompt"] = build_parameters(
            positive_prompt,
            negative_prompt,
        )

    png_info_saver.strip_template_info(basic_parameters)

    if negative_prompt:
        assert basic_parameters["Prompt"] == positive_prompt
        assert (
            basic_parameters["Negative prompt"]
            == f"{negative_prompt}\n{BASIC_PARAMETERS}"
        )
    else:
        assert basic_parameters["Prompt"] == f"{positive_prompt}\n{BASIC_PARAMETERS}"
