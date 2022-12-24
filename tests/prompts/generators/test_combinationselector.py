from unittest import mock
import pytest

from prompts.generators.randomprompt import CombinationSelector, RandomPromptGenerator
from prompts.wildcardmanager import WildcardManager


@pytest.fixture
def wildcard_manager():
    return WildcardManager(None)


@pytest.fixture
def generator(wildcard_manager):
    return RandomPromptGenerator(wildcard_manager, "")


class TestCombinationSelector:
    def test_rejects_empty(self, wildcard_manager):
        options = []
        selector = CombinationSelector(wildcard_manager, options)

        selections = selector.pick()
        assert len(selections) == 0

    def test_selects_one(self, generator):
        options = ["a"]
        selector = CombinationSelector(generator, options)

        selections = selector.pick()
        assert len(selections) == 1
        assert selections[0] == "a"

    def test_selects_multiple(self, generator):
        options = ["a", "b", "c", "d"]
        selector = CombinationSelector(generator, options)

        with mock.patch("random.choice", side_effect=["a", "b", "a"]):
            selections = selector.pick(3)
            assert len(selections) == 3
            assert selections[0] == "a"
            assert selections[1] == "b"
            assert selections[2] == "a"

    def test_selects_from_wildcard(self, generator):
        options = ["__colours__"]

        colours = ["red", "green", "blue", "yellow"]

        with mock.patch("random.choice", side_effect=["red", "yellow", "blue"]):
            with mock.patch.object(
                generator._wildcard_manager, "get_all_values", return_value=colours
            ):
                selector = CombinationSelector(generator, options)
                selections = selector.pick(3)
                assert len(selections) == 3
                assert selections[0] == "red"
                assert selections[1] == "yellow"
                assert selections[2] == "blue"

    def test_selects_from_wildcard_or_literal(self, generator):
        options = ["__colours__", "a"]

        colours = ["red", "green", "blue", "yellow"]

        with mock.patch("random.choice", side_effect=["red", "yellow", "blue", "a"]):
            with mock.patch.object(
                generator._wildcard_manager, "get_all_values", return_value=colours
            ):
                selector = CombinationSelector(generator, options)
                selections = selector.pick(4)
                assert len(selections) == 4
                assert selections[0] == "red"
                assert selections[1] == "yellow"
                assert selections[2] == "blue"
                assert selections[3] == "a"

    def test_selects_from_two_wildcards(self, generator):
        options = ["__colours__", "__animals__"]

        colours = ["red", "green", "blue", "yellow"]
        animals = ["dog", "cat", "bird", "fish"]

        with mock.patch("random.choice", side_effect=["red", "dog", "blue", "cat"]):
            with mock.patch.object(
                generator._wildcard_manager,
                "get_all_values",
                side_effect=[colours, animals],
            ):
                selector = CombinationSelector(generator, options)
                selections = selector.pick(4)
                assert len(selections) == 4
                assert selections[0] == "red"
                assert selections[1] == "dog"
                assert selections[2] == "blue"
                assert selections[3] == "cat"
