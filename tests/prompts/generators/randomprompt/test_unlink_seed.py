import random

from prompts.generators.randomprompt import RandomPromptGenerator
from prompts import constants

class TestUnlinkSeedFromPrompt:
    def test_unlink_seed_from_prompt(self, wildcard_manager):
        generator = RandomPromptGenerator(wildcard_manager, "A template")
        assert generator._unlink_seed_from_prompt == constants.UNLINK_SEED_FROM_PROMPT

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

