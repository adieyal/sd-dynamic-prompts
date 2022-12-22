import random
from unittest import mock
import pytest

from prompts.wildcardmanager import WildcardManager
from prompts.generators.randomprompt import RandomPromptGenerator

from prompts import constants


@pytest.fixture
def wildcard_manager():
    return WildcardManager(None)


@pytest.fixture
def seed():
    s = 0
    random.seed(s)

    return s


@pytest.fixture
def generator(wildcard_manager, seed):
    return RandomPromptGenerator(
        wildcard_manager, "A template", seed=seed, unlink_seed_from_prompt=False
    )


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

        variant = generator.pick_variant(template)
        assert variant == 'I love bread'

        variant = generator.pick_variant(template)
        assert variant == 'I love bread'

        variant = generator.pick_variant(template)
        assert variant == 'I love butter'

        variant = generator.pick_variant(template)
        assert variant == 'I love bread'

        variant = generator.pick_variant(template)
        assert variant == 'I love bread'

        variant = generator.pick_variant(template)
        assert variant == 'I love butter'

        variant = generator.pick_variant(template)
        assert variant == 'I love bread'

        variant = generator.pick_variant(template)
        assert variant == 'I love bread'

        variant = generator.pick_variant(template)
        assert variant == 'I love bread'

        variant = generator.pick_variant(template)
        assert variant == 'I love bread'

    def test_multiple_pick_variant(self, generator):
        template = "I love {2$$bread|butter}"
        generator._template = template

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

    def test_multiple_variant_one_option(self, generator):
        template = "I love {2$$bread}"
        generator._template = template

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

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love bread , butter"

        variant = generator.pick_variant(template)
        assert variant == "I love bread , butter"

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love bread"

    def test_variant_range_missing_lower(self, generator):
        template = "I love {-2$$bread|butter}"
        generator._template = template

        variant = generator.pick_variant(template)
        assert variant == "I love butter"

        variant = generator.pick_variant(template)
        assert variant == "I love "

        variant = generator.pick_variant(template)
        assert variant == "I love butter"

        variant = generator.pick_variant(template)
        assert variant == "I love butter"

        variant = generator.pick_variant(template)
        assert variant == "I love bread"

        variant = generator.pick_variant(template)
        assert variant == "I love bread , butter"

    def test_variant_range_missing_upper(self, generator):
        template = "I love {1-$$bread|butter}"
        generator._template = template

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love bread , butter"

        variant = generator.pick_variant(template)
        assert variant == "I love bread , butter"

        variant = generator.pick_variant(template)
        assert variant == "I love butter , bread"

        variant = generator.pick_variant(template)
        assert variant == "I love bread"

    def test_parse_combinations(self, generator):
        quantity, _, options, weights = generator._parse_combinations("bread|butter")
        assert quantity == (
            constants.DEFAULT_NUM_COMBINATIONS,
            constants.DEFAULT_NUM_COMBINATIONS,
        )
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("2$$bread|butter")
        assert quantity == (2, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("1-2$$bread|butter")
        assert quantity == (1, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("2-1$$bread|butter")
        assert quantity == (1, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("1-$$bread|butter")
        assert quantity == (1, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("-1$$bread|butter")
        assert quantity == (0, 1)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("2$$and$$bread|butter")
        assert quantity == (2, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("")
        assert quantity == (1, 1)
        assert options == [""]
        assert weights == [1.0]

        quantity, _, options, weights = generator._parse_combinations("3::bread|2::butter")
        assert quantity == (1, 1)
        assert options == ["bread", "butter"]
        assert weights == [3.0, 2.0]

        quantity, _, options, weights = generator._parse_combinations("1.3::bread|butter")
        assert quantity == (1, 1)
        assert options == ["bread", "butter"]
        assert weights == [1.3, 1.0]

        quantity, _, options, weights = generator._parse_combinations("1-2$$2.5::bread|butter")
        assert quantity == (1, 2)
        assert options == ["bread", "butter"]
        assert weights == [2.5, 1.0]

    def test_joiner(self, generator):
        _, joiner, _, _ = generator._parse_combinations("bread|butter")
        assert joiner == constants.DEFAULT_COMBO_JOINER

        _, joiner, _, _ = generator._parse_combinations("2$$bread|butter")
        assert joiner == constants.DEFAULT_COMBO_JOINER

        _, joiner, _, _ = generator._parse_combinations("2$$and$$bread|butter")
        assert joiner == "and"

        _, joiner, _, _ = generator._parse_combinations("")
        assert joiner == ","

        _, joiner, _, _ = generator._parse_combinations("2$$|$$bread|butter")
        assert joiner == "|"

    def test_photographers(self, generator):
        quantity, joiner, options, weights = generator._parse_combinations("2-4$$|$$a|b|c")


class TestGeneratorPrompt:
    def test_simple(self, generator):
        template = "I love {bread|butter}"
        generator._template = template

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


class TestUnlinkSeedFromPrompt:
    def test_unlink_seed_from_prompt(self, wildcard_manager):
        generator = RandomPromptGenerator(wildcard_manager, "A template")
        assert generator._unlink_seed_from_prompt == constants.UNLINK_SEED_FROM_PROMPT

        random.seed(0)
        for i in range(5):
            generator = RandomPromptGenerator(
                wildcard_manager, "A template", unlink_seed_from_prompt=False, seed=0
            )
            generator._template = "I love {1-2$$red|green|blue}"

            prompt = generator.generate(5)
            assert prompt == ['I love blue , red', 'I love blue , green', 'I love red', 'I love blue , red', 'I love green , blue']
            

        prev_prompt = None
        random.seed(0)
        for i in range(5):
            generator = RandomPromptGenerator(
                wildcard_manager, "A template", unlink_seed_from_prompt=True, seed=0
            )
            generator._template = "I love {1-2$$red|green|blue}"

            prompt = generator.generate(5)
            assert prompt != prev_prompt
            prev_prompt = prompt

