from __future__ import annotations

import logging
from random import Random
import random

from prompts import constants
from prompts.wildcardmanager import WildcardManager
from . import PromptGenerator, re_combinations, re_wildcard

logger = logging.getLogger(__name__)

MAX_SELECTION_ITERATIONS = 100


class CombinationSelector:
    def __init__(
        self, wildcard_manager: WildcardManager, options: list[str], weights: list[float]|None=None, rand=None
    ):
        if rand is None:
            self._random = random
        else:
            self._random = rand

        get_option = (
            lambda option: wildcard_manager.get_all_values(option)
            if wildcard_manager.is_wildcard(option)
            else [option]
        )

        self._options = [get_option(o) for o in options]
        if weights is None:
            self._weights = [1.0 for _ in range(len(self._options))]
        else:
            self._weights = weights

    def pick(self, count=1) -> list[str]:
        picked = []

        if len(self._options) == 0:
            return picked

        for i in range(count):
            option = self._random.choices(
                population=self._options,
                weights=self._weights
            )[0]
            picked.append(self._random.choice(option))

        return picked


class CombinationCollector:
    def __init__(self, selector: CombinationSelector, rand=None):
        if rand is None:
            self._random = random
        else:
            self._random = rand

        self._selector = selector

    def collect(self, count: int | tuple[int, int], duplicates=False) -> list[str]:
        """
        Attempts to collect count combinations from the selector without duplicates
        if this is impossible, it will return as many as possible without duplicates
        """

        collected = []
        iterations = 0

        if isinstance(count, int):
            min_count = max_count = count
        else:
            min_count, max_count = count
        num_to_collect = self._random.randint(min_count, max_count)

        while len(collected) < num_to_collect:
            iterations += 1
            if iterations > MAX_SELECTION_ITERATIONS:
                return collected

            picked = self._selector.pick()[0]
            if not duplicates and picked in collected:
                continue

            iterations = 0
            collected.append(picked)

        return collected


class RandomPromptGenerator(PromptGenerator):
    def __init__(
        self,
        wildcard_manager: WildcardManager,
        template,
        seed: int | None = None,
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

    def _parse_weight(self, variant_str: str) -> tuple[float, str]:
        parts = variant_str.split("::")

        if len(parts) == 1:
            return [1.0, variant_str]
        elif len(parts) == 2:
            return [float(parts[0]), parts[1]]
        else:
            raise Exception(f"Unexpected weighted variant {variant_str}")

    def _parse_combinations(
        self, combinations_str: str
    ) -> tuple[tuple[int, int], str, list[str], list[float]]:
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

        weights, variants = zip(*[self._parse_weight(v) for v in variants])

        return (low_range, high_range), joiner, list(variants), list(weights)

    def _replace_combinations(self, match):
        if match is None or len(match.groups()) == 0:
            logger.warning("Unexpected missing combination")
            return ""

        combinations_str = match.groups()[0]
        (low_range, high_range), joiner, variants, weights = self._parse_combinations(
            combinations_str
        )

        selector = CombinationSelector(
            self._wildcard_manager, variants, weights, rand=self._random
        )
        collector = CombinationCollector(selector, rand=self._random)
        collected = collector.collect((low_range, high_range))
        return f" {joiner} ".join(collected)

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

