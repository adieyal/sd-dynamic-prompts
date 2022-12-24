import random
from unittest import mock
import pytest

from prompts.generators.randomprompt import MAX_SELECTION_ITERATIONS


class TestRandomPromptVariants:
    def test_simple_pick_variant(self, generator):
        template = "I love {bread|butter}"
        generator._template = template

        variant = generator.pick_variant(template)
        assert variant == "I love butter"

        variant = generator.pick_variant(template)
        assert variant == "I love bread"

        variant = generator.pick_variant(template)
        assert variant == "I love butter"

    def test_simple_pick_variant_weights(self, generator):
        template = "I love {10::bread|butter}"
        generator._template = template

        with mock.patch.object(
            generator._random,
            "choice",
            side_effect=[
                "bread",
                "bread",
                "butter",
                "bread",
                "bread",
                "butter",
                "bread",
                "bread",
                "bread",
                "butter",
            ],
        ):

            variant = generator.pick_variant(template)
            assert variant == "I love bread"

            variant = generator.pick_variant(template)
            assert variant == "I love bread"

            variant = generator.pick_variant(template)
            assert variant == "I love butter"

            variant = generator.pick_variant(template)
            assert variant == "I love bread"

            variant = generator.pick_variant(template)
            assert variant == "I love bread"

            variant = generator.pick_variant(template)
            assert variant == "I love butter"

            variant = generator.pick_variant(template)
            assert variant == "I love bread"

            variant = generator.pick_variant(template)
            assert variant == "I love bread"

            variant = generator.pick_variant(template)
            assert variant == "I love bread"

            variant = generator.pick_variant(template)
            assert variant == "I love butter"

    def test_multiple_pick_variant(self, generator):
        template = "I love {2$$bread|butter}"
        generator._template = template

        with mock.patch.object(
            generator._random,
            "choice",
            side_effect=[
                "butter",
                "bread",
                "butter",
                "bread",
                "butter",
                "bread",
            ],
        ):

            variant = generator.pick_variant(template)
            assert variant == "I love butter , bread"

            variant = generator.pick_variant(template)
            assert variant == "I love butter , bread"

            variant = generator.pick_variant(template)
            assert variant == "I love butter , bread"

    def test_multiple_variant_one_option(self, generator):
        template = "I love {2$$bread}"
        generator._template = template

        with mock.patch.object(
            generator._random,
            "choice",
            side_effect=["bread"] * MAX_SELECTION_ITERATIONS * 2,
        ):
            variant = generator.pick_variant(template)
            assert variant == "I love bread"

    def test_multiple_variant_zero_options(self, generator):
        template = "I love {}"
        generator._template = template

        variant = generator.pick_variant(template)
        assert variant == "I love "

    def test_variant_range(self, generator):
        template = "I love {1-2$$bread|butter}"
        generator._template = template

        with mock.patch.object(
            generator._random,
            "choice",
            side_effect=[
                "butter",
                "bread",
                "bread",
                "butter",
                "butter",
            ],
        ):
            with mock.patch.object(generator._random, "randint", side_effect=[2, 2, 1]):
                variant = generator.pick_variant(template)
                assert variant == "I love butter , bread"

                variant = generator.pick_variant(template)
                assert variant == "I love bread , butter"

                variant = generator.pick_variant(template)
                assert variant == "I love butter"

    def test_variant_range_missing_lower(self, generator):
        template = "I love {-2$$bread|butter}"
        generator._template = template

        with mock.patch.object(
            generator._random,
            "choice",
            side_effect=[
                "butter",
                "butter",
                "bread",
                "butter",
            ],
        ):
            with mock.patch.object(
                generator._random, "randint", side_effect=[1, 0, 1, 2]
            ):

                variant = generator.pick_variant(template)
                assert variant == "I love butter"

                variant = generator.pick_variant(template)
                assert variant == "I love "

                variant = generator.pick_variant(template)
                assert variant == "I love butter"

                variant = generator.pick_variant(template)
                assert variant == "I love bread , butter"

    def test_variant_range_missing_upper(self, generator):
        template = "I love {1-$$bread|butter}"
        generator._template = template

        with mock.patch.object(
            generator._random,
            "choice",
            side_effect=[
                "butter",
                "bread",
                "bread",
                "butter",
                "bread",
            ],
        ):
            with mock.patch.object(generator._random, "randint", side_effect=[2, 2, 1]):

                variant = generator.pick_variant(template)
                assert variant == "I love butter , bread"

                variant = generator.pick_variant(template)
                assert variant == "I love bread , butter"

                variant = generator.pick_variant(template)
                assert variant == "I love bread"


class TestGeneratorPrompt:
    def test_simple(self, generator):
        template = "I love {bread|butter}"
        generator._template = template

        with mock.patch.object(
            generator._random,
            "choice",
            side_effect=[
                "butter",
                "bread",
                "butter",
                "bread",
                "bread",
                "butter",
                "bread",
            ],
        ):

            prompt = generator.generate(1)
            assert prompt == ["I love butter"]

            prompt = generator.generate(2)
            assert prompt == ["I love bread", "I love butter"]

            prompt = generator.generate(4)
            assert prompt == [
                "I love bread",
                "I love bread",
                "I love butter",
                "I love bread",
            ]
