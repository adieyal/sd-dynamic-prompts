from __future__ import annotations

import random
from typing import cast, Iterable

from .parse import Parser, ActionBuilder
from .commands import SequenceCommand, Command, LiteralCommand, VariantCommand, WildcardCommand


class RandomSequenceCommand(SequenceCommand):
    def prompts(self) -> Iterable[str]:
        if len(self.tokens) == 0:
            return []
        else:
            partials = [p.get_prompt() for p in self.tokens]
            return [" ".join(partials)]


class RandomWildcardCommand(Command):
    def __init__(self, wildcard_manager, token: str):
        super().__init__(token)
        self._wildcard_manager = wildcard_manager
        self._wildcard = token[0]

    def prompts(self) -> Iterable[str]:
        generator = RandomGenerator(self._wildcard_manager)
        values = self._wildcard_manager.get_all_values(self._wildcard)
        val = random.choice(values)
        prompts = generator.generate_prompts(val, 1)

        return prompts
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self._wildcard!r})"


class RandomVariantCommand(Command):
    def __init__(self, variants, min_bound=1, max_bound=1, sep=","):
        super().__init__(variants)
        self._weights = [p["weight"][0] for p in variants]
        self._values = [p["val"] for p in variants]
        self.min_bound = min_bound
        self.max_bound = max_bound
        self.sep = sep
        self._remaining_values = self._values

    def _combo_to_prompt(self, combo: list[SequenceCommand]) -> Iterable[list[str]]:
        if len(combo) == 0:
            yield []
        else:
            c_1, c_rest = combo[0], combo[1:]

            for p in c_1.prompts():
                for rest_prompt in self._combo_to_prompt(c_rest):
                    if rest_prompt != "":
                        yield [p] + rest_prompt
                    else:
                        yield [p]

    def prompts(self) -> Iterable[str]:
        if len(self._values) == 0:
            return []

        num_choices = random.randint(self.min_bound, self.max_bound)
        combo = random.choices(self._values, weights=self._weights, k=num_choices)
        for prompt_arr in self._combo_to_prompt(combo):
            yield self.sep.join(prompt_arr)

    def __repr__(self):
        z = zip(self._weights, self._values)
        return f"{self.__class__.__name__}({list(z)!r})"


class RandomActionBuilder(ActionBuilder):
    def get_literal_class(self):
        return LiteralCommand

    def get_variant_class(self):
        return RandomVariantCommand

    def get_wildcard_class(self):
        return RandomWildcardCommand

    def get_sequence_class(self):
        return RandomSequenceCommand


class RandomGenerator:
    def __init__(self, wildcard_manager):
        self._wildcard_manager = wildcard_manager

    def get_action_builder(self) -> ActionBuilder:
        return RandomActionBuilder(self._wildcard_manager)

    def configure_parser(self):
        builder = self.get_action_builder()
        parser = Parser(builder)

        return parser.prompt

    def generate_prompts(self, prompt: str, num_prompts: int) -> list[str]:
        if len(prompt) == 0:
            return []

        parser = self.configure_parser()
        tokens = parser.parse_string(prompt)
        tokens = cast(list[Command], tokens)

        generated_prompts = []
        for i in range(num_prompts):
            prompts = list(tokens[0].prompts())
            generated_prompts.append(prompts[0])

        return generated_prompts
