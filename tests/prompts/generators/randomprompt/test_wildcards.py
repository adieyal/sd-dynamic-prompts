from __future__ import annotations
from typing import List
from unittest import mock

import pytest

from prompts.generators.randomprompt import RandomPromptGenerator

@pytest.fixture
def colours() -> List[str]:
    return ["red", "green", "blue"]

@pytest.fixture
def shapes() -> List[str]:
    return ["square", "circle", "triangle"]

@pytest.fixture
def mock_get_all_values(generator: RandomPromptGenerator, colours: List[str], shapes: List[str]):
    def _ctx():
        def get_all_values(wildcard: str) -> List[str]:
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

    def test_missing_wildcard(self, generator: RandomPromptGenerator):
        generator._template = "An __invalid__ wildcard"
        prompts = generator.generate(10)
        assert len(prompts) == 10
        assert prompts[0] == "An __invalid__ wildcard"

