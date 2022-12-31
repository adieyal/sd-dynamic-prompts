from __future__ import annotations

from typing import cast
import logging

import pyparsing as pp

from .commands import SequenceCommand, LiteralCommand, VariantCommand, WildcardCommand

logger = logging.getLogger(__name__)


def parse_bound_expr(expr, max_options):
    lbound = 1
    ubound = max_options
    separator = ","

    if expr is None:
        return lbound, ubound, separator
    expr = expr[0]

    if "range" in expr:
        rng = expr["range"]
        if "exact" in rng:
            lbound = ubound = rng["exact"]
        else:
            if "lower" in expr["range"]:
                lbound = int(expr["range"]["lower"])
            if "upper" in expr["range"]:
                ubound = int(expr["range"]["upper"])

    if "separator" in expr:
        separator = expr["separator"][0]

    return lbound, ubound, separator


class Parser:
    def __init__(self, builder: ActionBuilder):
        self._builder = builder
        prompt = self._configure_parser(self._builder)
        self._prompt = prompt

        
    @property
    def prompt(self):
        return self._prompt

    def parse(self, prompt: str) -> SequenceCommand:
        tokens = self.prompt.parse_string(prompt, parse_all=True)
        return cast(SequenceCommand, tokens[0])

    def _enable_comments(self, prompt):
        prompt.ignore("#" + pp.restOfLine)
        prompt.ignore("//" + pp.restOfLine)
        prompt.ignore(pp.c_style_comment)

    def _configure_range(self):
        hyphen = pp.Suppress("-")
        variant_delim = pp.Suppress("$$")

        separator = pp.Word(pp.alphanums + " ", exclude_chars="$").leave_whitespace()("separator")
        bound = pp.common.integer
        bound_range1 = bound("exact")
        bound_range2 = bound("lower") + hyphen
        bound_range3 = hyphen + bound("upper")
        bound_range4 = bound("lower") + hyphen + bound("upper")

        bound_range = pp.Group(
            bound_range4 | bound_range3 | bound_range2 | bound_range1
        )
        bound_expr = pp.Group(
            bound_range("range")
            + variant_delim
            + pp.Opt(separator + variant_delim, default=",")("separator")
        )

        return bound_expr

    def _configure_wildcard(self):
        wildcard_enclosure = pp.Suppress("__")
        wildcard = (wildcard_enclosure + ... + wildcard_enclosure)("wildcard")

        return wildcard

    def _configure_literal_sequence(self):
        non_literal_chars = "{}|$[]"
        wildcard_enclosure = pp.Suppress("__")

        prompt_editing = self._configure_prompt_editing()

        literal = pp.Word(pp.printables, exclude_chars=non_literal_chars)("literal")
        literal_sequence = (pp.OneOrMore(~wildcard_enclosure + literal))("literal_sequence")

        return prompt_editing | literal_sequence

    def _configure_prompt_editing(self):
        left_bracket, right_bracket = map(pp.Word, "[]")
        pipe = pp.Word("|")
        chars = pp.Regex(r"[^\]|]*")

        prompt_editing = left_bracket + chars + pp.OneOrMore(pipe + chars) + right_bracket
        return prompt_editing.set_parse_action(lambda s, loc, token: "".join(token))


    def _configure_weight(self):
        weight_delim = pp.Suppress("::")
        weight = (pp.common.real | pp.common.integer) + weight_delim

        return weight

    def _configure_variants(self, literal_sequence, bound_expr, prompt):
        weight_delim = pp.Suppress("::")

        left_brace, right_brace = map(pp.Suppress, "{}")
        weight = pp.common.integer + weight_delim
        
        variant_option = prompt
        variant = pp.Group(pp.Opt(weight, default=1)("weight") + variant_option("val"))
        variants_list = pp.Group(pp.delimited_list(variant, delim="|"))

        variants = (
            left_brace
            + pp.Group(pp.Opt(bound_expr)("bound_expr") + variants_list("variants"))
            + right_brace
        )

        return variants


    def _configure_parser(self, builder: ActionBuilder):
        bound_expr = self._configure_range()

        prompt = pp.Forward()
        wildcard = self._configure_wildcard()
        literal_sequence = self._configure_literal_sequence()
        variants = self._configure_variants(literal_sequence, bound_expr, prompt)
        
        chunk = (variants | wildcard | literal_sequence)

        prompt <<= pp.ZeroOrMore(chunk)("prompt")
        
        self._enable_comments(prompt)

        wildcard.set_parse_action(builder.get_wildcard_action)
        variants.set_parse_action(builder.get_variant_action)
        literal_sequence.set_parse_action(builder.get_literal_action)

        prompt.set_parse_action(
            lambda s, loc, token: builder.get_sequence_class()(token.as_list())
        )

        return prompt


class ActionBuilder:
    def get_literal_class(self):
        return LiteralCommand

    def get_wildcard_class(self):
        return WildcardCommand

    def get_variant_class(self):
        return VariantCommand

    def get_sequence_class(self):
        return SequenceCommand

    def __init__(self, wildcard_manager):
        self._wildcard_manager = wildcard_manager

    def get_wildcard_action(self, token):
        return self.get_wildcard_class()(self._wildcard_manager, token)

    def get_variant_action(self, token):
        parts = token[0].as_dict()
        variants = parts["variants"]
        variants = [{"weight": v["weight"], "val": v["val"]} for v in variants]
        if "bound_expr" in parts:
            min_bound, max_bound, sep = parse_bound_expr(
                parts["bound_expr"], max_options=len(variants)
            )
            command = self.get_variant_class()(variants, min_bound, max_bound, sep)
        else:
            command = self.get_variant_class()(variants)

        return command

    def get_literal_action(self, token):
        s = " ".join(token)
        return self.get_literal_class()(s)

