from __future__ import annotations

from typing import Iterable
from collections import OrderedDict

from .parse import (
    ActionBuilder,
    Parser,
)

from .commands import (
    Command,
    SequenceCommand,
    WildcardCommand,
    LiteralCommand,
    VariantCommand,
)


class CombinatorialSequenceCommand(SequenceCommand):
    def __init__(self, tokens: list[Command] | None = None, separator=" "):
        self._sep = separator
        super().__init__(tokens)

    def prompts(self, tokens: list[Command] | None = None) -> Iterable[str]:
        if tokens is None:
            tokens = self.tokens

        if len(tokens) == 0:
            yield ""
        else:
            token = tokens[0]
            for prompt in token.prompts():
                for next_prompts in self.prompts(tokens[1:]):
                    yield (prompt + self._sep + next_prompts).strip()


class CombinatorialWildcardCommand(WildcardCommand):
    def __init__(self, wildcard_manager, token):
        super().__init__(wildcard_manager, token)
        self._wildcard_manager = wildcard_manager
        self._wildcard = token[0]

    def prompts(self):
        generator = CombinatorialGenerator(self._wildcard_manager)
        values = self._wildcard_manager.get_all_values(self._wildcard)
        for val in values:
            for prompt in generator.generate_prompts(val):
                yield prompt

    def __repr__(self):
        return f"{self.__class__.__name__}({self._wildcard!r})"


class CombinatorialVariantCommand(VariantCommand):
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

    def _dedupe(self, arr: list[str]) -> tuple[str]:
        d = OrderedDict()
        for item in arr:
            d[item] = None
        return tuple(d.keys())

    def prompts(self) -> Iterable[str]:
        if len(self._values) == 0:
            return []
        
        seen = set()

        for bound in range(self.min_bound, self.max_bound + 1):
            for combo in self._combinations(bound):
                for prompt_arr in self._combo_to_prompt(combo):
                    deduped_arr = self._dedupe(prompt_arr)
                    correct_size = len(deduped_arr) == bound
                    if deduped_arr not in seen and correct_size:
                        seen.add(deduped_arr)
                        yield self.sep.join(deduped_arr)
                    

    def __repr__(self):
        z = zip(self._weights, self._values)
        return f"{self.__class__.__name__}({list(z)!r})"


class CombinatorialActionBuilder(ActionBuilder):
    def get_literal_class(self):
        return LiteralCommand

    def get_variant_class(self):
        return CombinatorialVariantCommand

    def get_wildcard_class(self):
        return CombinatorialWildcardCommand

    def get_sequence_class(self):
        return CombinatorialSequenceCommand

    def get_prompt_alternating_class(self):
        return lambda tokens : CombinatorialSequenceCommand(tokens, separator="")

    def get_prompt_editing_class(self):
        return lambda tokens : CombinatorialSequenceCommand(tokens, separator="")


class CombinatorialGenerator:
    def __init__(self, wildcard_manager):
        self._wildcard_manager = wildcard_manager

    def get_action_builder(self) -> ActionBuilder:
        return CombinatorialActionBuilder(self._wildcard_manager)

    def configure_parser(self) -> Parser:
        builder = self.get_action_builder()
        parser = Parser(builder)

        return parser

    def generate_prompts(self, prompt: str, num_prompts: int|None=None) -> list[str]:
        if len(prompt) == 0:
            return []

        parser = self.configure_parser()
        sequence = parser.parse(prompt)
        prompts = sequence.prompts()

        if num_prompts is None:
            return [p for idx, p in enumerate(prompts)]
        else:
            return [p for idx, p in enumerate(prompts) if idx < num_prompts]
