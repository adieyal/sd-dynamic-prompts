import pytest

from prompts import wildcardmanager
from prompts.generators.randomprompt import RandomPromptGenerator

from prompts import constants


@pytest.fixture
def wildcard_manager():
    return wildcardmanager.WildcardManager(None)

@pytest.fixture
def seed():
    return 0

@pytest.fixture
def generator(wildcard_manager, seed):
    return RandomPromptGenerator(wildcard_manager, "A template", seed=seed)

class TestRandomPromptVariants:
    def test_simple_pick_variant(self, generator):
        template = "I love {bread|butter}"
        generator._template = template

        variant = generator.pick_variant(template)
        assert variant == "I love butter"

        variant = generator.pick_variant(template)
        assert variant == "I love butter"

        variant = generator.pick_variant(template)
        assert variant == "I love butter"

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
        assert variant == "I love bread , bread"

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
        assert variant == "I love bread"

        variant = generator.pick_variant(template)
        assert variant == "I love bread , butter"

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
        assert variant == "I love butter"

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
        assert variant == "I love bread"

    def test_parse_combinations(self, generator):
        quantity, joiner, options = generator._parse_combinations("bread|butter")
        assert quantity == (constants.DEFAULT_NUM_COMBINATIONS, constants.DEFAULT_NUM_COMBINATIONS)
        assert joiner == constants.DEFAULT_COMBO_JOINER
        assert options == ["bread", "butter"]

        quantity, joiner, options = generator._parse_combinations("2$$bread|butter")
        assert quantity == (2, 2)
        assert joiner == constants.DEFAULT_COMBO_JOINER
        assert options == ["bread", "butter"]

        quantity, joiner, options = generator._parse_combinations("1-2$$bread|butter")
        assert quantity == (1, 2)
        assert joiner == constants.DEFAULT_COMBO_JOINER
        assert options == ["bread", "butter"]

        quantity, joiner, options = generator._parse_combinations("2-1$$bread|butter")
        assert quantity == (1, 2)
        assert joiner == constants.DEFAULT_COMBO_JOINER
        assert options == ["bread", "butter"]

        quantity, joiner, options = generator._parse_combinations("1-$$bread|butter")
        assert quantity == (1, 2)
        assert joiner == constants.DEFAULT_COMBO_JOINER
        assert options == ["bread", "butter"]

        quantity, joiner, options = generator._parse_combinations("-1$$bread|butter")
        assert quantity == (0, 1)
        assert joiner == constants.DEFAULT_COMBO_JOINER
        assert options == ["bread", "butter"]

        quantity, joiner, options = generator._parse_combinations("2$$and$$bread|butter")
        assert quantity == (2, 2)
        assert joiner == "and"
        assert options == ["bread", "butter"]

        quantity, joiner, options = generator._parse_combinations("")
        assert quantity == (1, 1)
        assert joiner == ","
        assert options == [""]
