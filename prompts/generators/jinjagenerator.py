from __future__ import annotations
import logging
import random
from itertools import permutations
import re

import jinja2.nodes
from jinja2 import Environment
from jinja2.exceptions import TemplateSyntaxError
from jinja2.ext import Extension

from dynamicprompts.generators.promptgenerator import GeneratorException, PromptGenerator

logger = logging.getLogger(__name__)

re_wildcard = re.compile(r"__(.*?)__")
re_combinations = re.compile(r"\{([^{}]*)}")


class RandomExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["choice"] = self.choice
        environment.globals["weighted_choice"] = self.weighted_choice
        environment.globals["random"] = self.random
        environment.globals["randint"] = self.randint

    def choice(self, *items):
        return random.choice(items)

    def weighted_choice(self, *items):
        population, weights = zip(*items)
        return random.choices(population, weights=weights)[0]

    def random(self) -> float:
        return random.random()

    def randint(self, low: int, high: int) -> int:
        return random.randint(low, high)


class PermutationExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["permutations"] = self.permutation

    def permutation(self, items, low: int, high: int|None = None):
        vars = []
        if high is None:
            high = low

        for i in range(low, high + 1):
            vars.extend(permutations(items, i))

        return vars


class WildcardExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["wildcard"] = self.wildcard

    def wildcard(self, wildcard_name):
        wm = self.environment.wildcard_manager
        values = []

        for value in wm.get_all_values(wildcard_name):
            if re_wildcard.fullmatch(value):
                values.extend(self.wildcard(value))
            elif re_combinations.fullmatch(value):
                val = re_combinations.findall(value)[0]
                options = val.split("|")
                choice_ext = RandomExtension(self.environment)
                values.append(choice_ext.choice(options))
            else:
                values.append(value)
        return values


class PromptExtension(Extension):
    tags = {"prompt"}

    def __init__(self, environment):
        super().__init__(environment)
        environment.extend(prompt_blocks=[])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(["name:endprompt"], drop_needle=True)
        return jinja2.nodes.CallBlock(
            self.call_method("_prompt", []), [], [], body
        ).set_lineno(lineno)

    def _prompt(self, caller):
        self.environment.prompt_blocks.append(caller())
        return caller()


class JinjaGenerator(PromptGenerator):
    def __init__(self, template, wildcard_manager=None, context=None):
        self._template = template
        self._wildcard_manager = wildcard_manager

        if context is not None:
            self._context = context
        else:
            self._context = {}


    def generate(self, num_prompts=1) -> list[str]:
        try:
            env = Environment(
                extensions=[RandomExtension, PromptExtension, WildcardExtension, PermutationExtension]
            )
            env.wildcard_manager = self._wildcard_manager


            prompts = []
            for i in range(num_prompts):
                template = env.from_string(self._template)
                s = template.render(**self._context)
                prompts.append(s)

            if env.prompt_blocks:
                prompts = env.prompt_blocks
            return prompts
        except TemplateSyntaxError as e:
            logger.exception(e)
            raise GeneratorException(e.message)
