from unittest.mock import patch

from dynamicprompts.generators.magicprompt import MagicPromptGenerator
from dynamicprompts.wildcards import WildcardManager

from sd_dynamic_prompts.frozenprompt_generator import FrozenPromptGenerator
from sd_dynamic_prompts.generator_builder import GeneratorBuilder


def test_magic_blocklist_regexp(tmp_path):
    gb = GeneratorBuilder(
        wildcard_manager=WildcardManager(tmp_path),
    )
    gb.set_seed(42)  # TODO: not setting a seed makes the test fail
    popular_artist = "grug retkawsky"
    gb.set_is_magic_prompt(
        magic_blocklist_regex=popular_artist,
        magic_model="some model",
    )
    with patch("dynamicprompts.generators.magicprompt.MagicPromptGenerator.set_model"):
        gen = gb.create_generator()
        assert isinstance(gen, MagicPromptGenerator)
        assert gen._blocklist_regex.pattern == popular_artist


def test_frozen_generator(tmp_path):
    gb = GeneratorBuilder(wildcard_manager=WildcardManager(tmp_path)).set_freeze_prompt(
        True,
    )
    gen = gb.create_generator()
    assert type(gen) == FrozenPromptGenerator
