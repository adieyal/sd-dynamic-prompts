from __future__ import annotations
import logging
from random import Random
import random

from prompts import constants
from prompts.wildcardmanager import WildcardManager
from . import PromptGenerator, re_combinations, re_wildcard

logger = logging.getLogger(__name__)


class RandomPromptGenerator(PromptGenerator):
    def __init__(
        self,
        wildcard_manager: WildcardManager,
        template,
        seed: int = None,
        unlink_seed_from_prompt: bool = constants.UNLINK_SEED_FROM_PROMPT,
    ):
        self._wildcard_manager = wildcard_manager
        self._unlink_seed_from_prompt = unlink_seed_from_prompt

        if self._unlink_seed_from_prompt:
            self._random = random
        else:
            self._random = Random()
            if seed is not None:
                self._random.seed(seed)
            
        
        self._template = template

    def _parse_range(self, range_str: str, num_variants: int) -> tuple[int, int]:
        default_low = 0
        default_high = num_variants

        if range_str is None:
            return (default_low, default_high)

        parts = range_str.split("-")
        if len(parts) == 1:
            low = high = int(parts[0])
        elif len(parts) == 2:
            low = int(parts[0]) if parts[0] else default_low
            high = int(parts[1]) if parts[1] else default_high
        else:
            raise Exception(f"Unexpected range {range_str}")

        return min(low, high), max(low, high)

    def _parse_combinations(
        self, combinations_str: str
    ) -> tuple[tuple[int, int], str, list[str]]:
        variants = combinations_str.split("|")
        joiner = constants.DEFAULT_COMBO_JOINER
        quantity = str(constants.DEFAULT_NUM_COMBINATIONS)

        sections = combinations_str.split("$$")

        if len(sections) == 3:
            joiner = sections[1]
            sections.pop(1)

        if len(sections) == 2:
            quantity = sections[0]
            variants = sections[1].split("|")

        low_range, high_range = self._parse_range(quantity, len(variants))

        return (low_range, high_range), joiner, variants

    def _replace_combinations(self, match):
        if match is None or len(match.groups()) == 0:
            logger.warning("Unexpected missing combination")
            return ""

        combinations_str = match.groups()[0]
        (low_range, high_range), joiner, variants = self._parse_combinations(
            combinations_str
        )
        quantity = self._random.randint(low_range, high_range)
        try:
            allow_repeats = len(variants) < quantity
            if allow_repeats:
                picked = self._random.choices(variants, k=quantity)
            else:
                picked = self._random.sample(variants, quantity)
            return f" {joiner} ".join(picked)
        except ValueError as e:
            logger.exception(e)
            return ""

    def _replace_wildcard(self, match):
        if match is None or len(match.groups()) == 0:
            logger.warning("Expected match to contain a filename")
            return ""

        wildcard = match.groups()[0]
        wildcards = self._wildcard_manager.get_all_values(wildcard)

        if len(wildcards) > 0:
            return self._random.choice(list(wildcards))
        else:
            logging.warning(f"Could not find any wildcards in {wildcard}")
            return ""

    def pick_variant(self, template):
        if template is None:
            return None

        return re_combinations.sub(lambda x: self._replace_combinations(x), template)

    def pick_wildcards(self, template):
        return re_wildcard.sub(lambda x: self._replace_wildcard(x), template)

    def generate_prompt(self, template):
        old_prompt = template
        counter = 0
        while True:
            counter += 1
            if counter > constants.MAX_RECURSIONS:
                raise Exception(
                    "Too many recursions, something went wrong with generating the prompt"
                )

            prompt = self.pick_variant(old_prompt)
            prompt = self.pick_wildcards(prompt)

            if prompt == old_prompt:
                logger.info(f"Prompt: {prompt}")
                return prompt
            old_prompt = prompt

    def generate(self, num_prompts) -> list[str]:
        all_prompts = [self.generate_prompt(self._template) for _ in range(num_prompts)]

        return all_prompts

