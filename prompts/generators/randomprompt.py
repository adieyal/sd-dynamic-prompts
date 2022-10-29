import logging
from random import Random

from prompts import constants
from prompts.wildcardmanager import WildcardManager
from . import PromptGenerator, re_combinations, re_wildcard

logger = logging.getLogger(__name__)

class RandomPromptGenerator(PromptGenerator):
    def __init__(self, wildcard_manager: WildcardManager, template, seed:int = None):
        self._wildcard_manager = wildcard_manager
        self._random = Random()
        if seed is not None:
            self._random.seed(seed)
        self._template = template

    def _replace_combinations(self, match):
        if match is None or len(match.groups()) == 0:
            logger.warning("Unexpected missing combination")
            return ""

        variants = [s.strip() for s in match.groups()[0].split("|")]
        if len(variants) > 0:
            first = variants[0].split("$$")
            quantity = constants.DEFAULT_NUM_COMBINATIONS
            if len(first) == 2: # there is a $$
                prefix_num, first_variant = first
                variants[0] = first_variant
                
                try:
                    prefix_ints = [int(i) for i in prefix_num.split("-")]
                    if len(prefix_ints) == 1:
                        quantity = prefix_ints[0]
                    elif len(prefix_ints) == 2:
                        prefix_low = min(prefix_ints)
                        prefix_high = max(prefix_ints)
                        quantity = self._random.randint(prefix_low, prefix_high)
                    else:
                        raise 
                except Exception:
                    logger.warning(f"Unexpected combination formatting, expected $$ prefix to be a number or interval. Defaulting to {constants.DEFAULT_NUM_COMBINATIONS}")
            
            try:
                picked = self._random.sample(variants, quantity)
                return ", ".join(picked)
            except ValueError as e:
                logger.exception(e)
                return ""

        return ""

    def _replace_wildcard(self, match):
        if match is None or len(match.groups()) == 0:
            logger.warning("Expected match to contain a filename")
            return ""

        wildcard = match.groups()[0]
        wildcard_files = self._wildcard_manager.match_files(wildcard)

        if len(wildcard_files) == 0:
            logging.warning(f"Could not find any wildcard files matching {wildcard}")
            return ""

        wildcards = set().union(*[f.get_wildcards() for f in wildcard_files])

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
                raise Exception("Too many recursions, something went wrong with generating the prompt")

            prompt = self.pick_variant(old_prompt)
            prompt = self.pick_wildcards(prompt)

            if prompt == old_prompt:
                logger.info(f"Prompt: {prompt}")
                return prompt
            old_prompt = prompt

    def generate(self, num_prompts) -> list[str]:
        all_prompts = [
            self.generate_prompt(self._template) for _ in range(num_prompts)
        ]

        return all_prompts

