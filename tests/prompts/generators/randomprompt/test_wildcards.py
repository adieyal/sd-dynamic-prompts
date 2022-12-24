from __future__ import annotations

from unittest import mock

import pytest

from prompts.generators.randomprompt import RandomPromptGenerator

@pytest.fixture
def colours() -> list[str]:
    return ["red", "green", "blue"]

@pytest.fixture
def shapes() -> list[str]:
    return ["square", "circle", "triangle"]

@pytest.fixture
def mock_get_all_values(generator: RandomPromptGenerator, colours: list[str], shapes: list[str]):
    def _ctx():
        def get_all_values(wildcard: str) -> list[str]:
            wildcard = wildcard.strip("_")
            if wildcard == "colours":
                return colours
            elif wildcard == "shapes":
                return shapes
            else:
                raise ValueError(f"Unknown wildcard {wildcard}")
        return mock.patch.object(generator._wildcard_manager, "get_all_values", new=get_all_values)
    return _ctx

class TestWildcards:
    def test_basic_wildcard(self, generator: RandomPromptGenerator, mock_get_all_values):
        generator._template = "I love __colours__"
        with mock_get_all_values():
            with mock.patch.object(generator._random, "choice", return_value="red"):
                prompt = generator.pick_wildcards(generator._template)
                assert prompt == "I love red"

    def test_wildcard_variant(self, generator: RandomPromptGenerator, mock_get_all_values):
        generator._template = "I love {2$$__colours__}"
        with mock_get_all_values():
            with mock.patch.object(generator._random, "choice", side_effect=["__colours__", "red", "blue"]):
                prompt = generator.generate_prompt(generator._template)
                assert prompt == "I love red , blue"

    def test_multiple_wildcard_variant(self, generator: RandomPromptGenerator, mock_get_all_values):
        generator._template = "I love {__shapes__|__colours__ __shapes__}"
        with mock_get_all_values():
            with mock.patch.object(generator._random, "choice", side_effect=[
                    "__colours__ __shapes__", # Select the variant
                    "blue", "circle", # select a colour and shape for __colours__, __shapes__
            ]):
                with mock.patch.object(generator._random, "choices", return_value=["blue circle"]):
                    prompt = generator.generate_prompt(generator._template)
                    assert prompt == "I love blue circle"

